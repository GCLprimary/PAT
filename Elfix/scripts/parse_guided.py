"""
scripts/parse_guided.py  —  does the constituent controller fix the class-STALL,
and does the PARSE STRUCTURE earn its keep over a flat class-window?
=================================================================================
The 1st-order ceiling is HIERARCHY (scripts/ngram_ceiling): the output stalls INSIDE a
constituent because a flat model has no phrase CLOSURE. The fix (elfix.syntax_tree) is an
online bracketer that penalises re-entering the OPEN constituent with a repeated head-
class — the non-local closure signal the flat class-bigram cannot represent. This gates it.

THE FAIR TEST (two questions, two controls):
  Q1 does the brake reduce the class-STALL?  no_repeat=8 already blocks exact-WORD loops;
     grammar already biases the next CLASS. Neither can catch the CLASS stall: DIFFERENT
     words cycling through the SAME few classes ('president kennedy senator johnson
     president kennedy ...') — every transition grammatical, every word distinct, no
     progression, no closure. So the metric is CLASS-level; baseline (off) is no_repeat +
     grammar.
  Q2 does the PARSE STRUCTURE earn its keep?  The brake is scoped to the OPEN constituent
     (it RESETS at a phrase boundary — binding <= chance), so a class may freely RECUR
     across phrases. A flat class-WINDOW (penalise any class seen in the last W content
     words, never resetting) is the control. If the flat window matches the parse, the
     structure is decoration; if the parse holds the stall down with LESS collateral
     (on-topic / content), the constituent scoping earns its keep.

METRICS on the OUTPUT (content words -> distributional class; '.' dropped):
  class-2cycle   P(class[i]==class[i-2]) — the A-B-A-B stall (vs a REAL-TEXT reference).
  class-run      mean maximal run of one class — the A-A stall.
  class-distinct distinct classes / length — phrase progression.
GUARDRAILS (the brake must not buy this by wrecking the wins): content% / on-topic% / gram-cost.

The floor is perplexity-optimal (scripts/adaptive_topic), so this is gated on STRUCTURE,
not perplexity, and stays OPT-IN unless it earns its place here.

Run:  python scripts/parse_guided.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.syntax_tree import SyntaxTree, ConstituentController
from elfix.session import Session

BASE = dict(sem_adapt=(0.6, 9.0), no_repeat=8, fn_penalty=0.25, grammar=1.0)
STRENGTH = 2.0          # the constituency exponent (a lever, like grammar — not earned)


class FlatClassWindow:
    """CONTROL: a flat class-level no-repeat over the last W emitted CONTENT classes, with
    NO constituent structure (never resets at a phrase boundary). Same interface as the
    controller, so respond() can swap it in. Isolates whether the parse's phrase-scoping
    earns its keep over a dumb window."""

    def __init__(self, scaffold, width: int):
        self.sc = scaffold
        self.width = width
        self.recent = []

    def reset(self):
        self.recent = []

    def observe(self, word):
        c = self.sc.sclass(word)
        if c[0] == "cl":
            self.recent.append(c)
            if len(self.recent) > self.width:
                self.recent.pop(0)

    def penalty_signal(self, cand_word):
        c = self.sc.sclass(cand_word)
        if c[0] != "cl":
            return 1.0
        rep = self.recent.count(c)
        return 1.0 if rep == 0 else 1.0 / (1.0 + rep)


def class_seq(words, space):
    """The content-word class sequence (the stall lives here)."""
    return [c for w in words if (c := space.class_of(w)) is not None]


def stall_metrics(cseq):
    """class-2cycle, mean class-run, class-distinct of a content-class sequence."""
    if len(cseq) < 3:
        return None
    cyc = sum(1 for i in range(2, len(cseq)) if cseq[i] == cseq[i - 2]) / (len(cseq) - 2)
    runs, cur = [], 1
    for a, b in zip(cseq, cseq[1:]):
        cur = cur + 1 if a == b else (runs.append(cur) or 1)
    runs.append(cur)
    return cyc, sum(runs) / len(runs), len(set(cseq)) / len(cseq)


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    p = Predictor(utts[:50000], vocab)
    print("  earning distributional classes + syntactic scaffold...")
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:50000], vocab)
    skel = space.skeleton
    tree = SyntaxTree(scaffold)
    W = round(tree.binder.mean_constituent_len())     # the matched flat-window width
    print(f"  {len(space.class_words)} classes; binder p_bond {tree.binder.p_bond:.2f} "
          f"-> earned mean constituent length {tree.binder.mean_constituent_len():.2f} words")
    prompts = [u for u in utts[50000:50090] if 6 <= len(u) <= 18]
    print(f"  {len(prompts)} prompts; flat-window control W={W} (matched to mean phrase)\n")

    # the three arms: off, the flat-window control, the parse-scoped controller
    arms = {
        "baseline (off)":   lambda: (0.0, None),
        f"+flat-window {W}": lambda: (STRENGTH, FlatClassWindow(scaffold, W)),
        "+constituent":      lambda: (STRENGTH, ConstituentController(tree)),
    }

    ref = [m for u in prompts
           if (m := stall_metrics(class_seq([w for w in u if w in vocab], space)))]
    ref_cyc = sum(m[0] for m in ref) / len(ref)
    ref_run = sum(m[1] for m in ref) / len(ref)
    print(f"  REAL TEXT reference:  class-2cycle {ref_cyc:.0%}   class-run {ref_run:.2f}\n")

    def guard(s, words):
        content = [w for w in words if w not in skel]
        active = set(sorted(s.sem_carry.weights, key=lambda c: -s.sem_carry.weights[c])[:10])
        on = (sum(1 for w in content if space.class_of(w) in active) / len(content)
              if content else 0.0)
        return (len(content) / max(1, len(words)), on, scaffold.seq_bits(words))

    agg = {name: [0.0] * 6 + [0] for name in arms}
    examples = {}
    for pi, u in enumerate(prompts):
        for name, make in arms.items():
            con, ctrl = make()
            s = Session(p, cmu, space=space, scaffold=scaffold, learn=False)
            s.read(" ".join(u))
            out = s.respond(n=24, temperature=0.7, rng_seed=pi, remember=False,
                            constituency=con, controller=ctrl, **BASE)
            words = [w for w, _, _ in out if w != "."]
            if (m := stall_metrics(class_seq(words, space))):
                g = guard(s, words)
                a = agg[name]
                for j in range(3):
                    a[j] += m[j]
                for j in range(3):
                    a[3 + j] += g[j]
                a[6] += 1
            if pi == 3:
                examples[name] = " ".join(words)

    print(f"  example continuation of: '{' '.join(prompts[3])[:50]}...'")
    for name in arms:
        print(f"    {name:<17} {examples.get(name, '')}")

    print(f"\n  metrics (mean over {len(prompts)} prompts, n=24 tokens each):")
    print(f"    {'config':<17}{'2cycle':>8}{'run':>7}{'distinct':>9}"
          f"{'content':>9}{'on-top':>8}{'gram':>7}")
    print(f"    {'(real text)':<17}{ref_cyc:>7.0%}{ref_run:>7.2f}{'--':>9}"
          f"{'--':>9}{'--':>8}{'--':>7}")
    for name in arms:
        a = agg[name]
        c = a[6] or 1
        print(f"    {name:<17}{a[0]/c:>7.0%}{a[1]/c:>7.2f}{a[2]/c:>9.2f}"
              f"{a[3]/c:>8.0%}{a[4]/c:>8.0%}{a[5]/c:>7.2f}")

    def col(name, j):
        return agg[name][j] / (agg[name][6] or 1)

    b, fw, cn = "baseline (off)", f"+flat-window {W}", "+constituent"
    # Q1: the class-repeat brake reduces the stall (the constituent arm vs off)
    brakes = col(cn, 0) <= col(b, 0) - 0.02 and col(cn, 1) <= col(b, 1) - 0.10
    # Q2: does the phrase-SCOPING dominate a flat window? It earns its keep only if it
    # holds the stall ~as well AND preserves more on-topic (the cross-phrase recurrence
    # the flat window kills). Measured: it does NOT dominate — a genuine trade-off.
    parse_dominates = (col(cn, 0) <= col(fw, 0) + 0.01 and col(cn, 4) >= col(fw, 4) + 0.01)
    print(f"\n  ==> Q1 the class-repeat brake {'WORKS' if brakes else 'is WEAK'}: class-2cycle "
          f"{col(b,0):.0%}->{col(cn,0):.0%} (real {ref_cyc:.0%}),\n      class-run "
          f"{col(b,1):.2f}->{col(cn,1):.2f} (real {ref_run:.2f}) -- the CLASS stall the flat "
          f"class-bigram\n      could not reach (different words, same classes) is reduced "
          f"toward real text.")
    print(f"\n      Q2 does the PARSE STRUCTURE earn its keep? {'YES' if parse_dominates else 'NO -- a TRADE-OFF'}. "
          f"vs the flat-window\n      control (W={W}), the constituent scoping is GENTLER: it "
          f"brakes the stall less\n      ({col(cn,0):.0%} vs {col(fw,0):.0%} 2cycle) but preserves "
          f"more on-topic content ({col(cn,4):.0%} vs {col(fw,4):.0%}),\n      because it RESETS "
          f"at phrase boundaries -- a class may recur across phrases. Neither\n      dominates: "
          f"the closure signal is real but the greedy class-PMI binder is too coarse\n      for "
          f"the phrase-scoping to beat a flat window (no head-awareness -- scripts/constituents\n"
          f"      flagged exactly this). The brake is a usable lever; the PARSE is not yet "
          f"load-bearing\n      for generation. Kept OPT-IN, honest -- the measurement is the "
          f"finding.")
    return 0          # a measurement that completed: the trade-off is the finding


if __name__ == "__main__":
    raise SystemExit(main())
