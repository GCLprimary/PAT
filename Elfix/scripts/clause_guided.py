"""
scripts/clause_guided.py — does CLAUSE-level head-awareness (predicate/argument) finally
fix the stall AND beat the flat-window control the head-unaware brake only tied?
=================================================================================
The head-unaware ConstituentController reduced the class-stall but did NOT beat a flat
class-window (scripts/parse_guided): the greedy class-PMI binder is too coarse. The
diagnosis was that the fix needs the PREDICATE/ARGUMENT distinction — and the TOPICAL
distributional classes do not carry it (a class-level N-V 2-colouring washes out). The
RoleTagger earns it instead from FUNCTOR context (a 2-hop bridge from 'the'), and the
ClauseController uses it: brake argument-stacking while a verb is OWED ("don't run past an
open subject until a verb arrives"). This gates that.

ARMS (all share the same base levers; only the controller changes):
  baseline (off)      no constituency controller
  +flat-window        a flat class-window no-repeat (the control parse_guided tied)
  +constituent        the head-unaware ConstituentController (repeated head-class brake)
  +clause             the head-AWARE ClauseController (brake args while a verb is owed)

METRICS (content words -> class / verb_score; '.' dropped):
  class-2cycle   the A-B-A-B stall (vs a REAL-TEXT reference; lower = less stalled)
  verb-rate      fraction of content words that are PREDICATES — clause COMPLETENESS. The
                 all-argument salad has too few verbs; real text has ~1 per clause. Closer
                 to real = more sentence-like. (The clause arm should RAISE this.)
GUARDRAILS: content% / on-topic% / gram-cost must hold.

WIN CONDITION: +clause reduces the stall AT LEAST as well as the flat window AND raises
verb-rate toward real text (the structural thing a flat window cannot do). The measurement
is the finding either way; gated on STRUCTURE, not perplexity (the floor is ppl-optimal).

Run:  python scripts/clause_guided.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.syntax_tree import SyntaxTree, ConstituentController, RoleTagger, ClauseController
from elfix.session import Session
from scripts.parse_guided import FlatClassWindow, class_seq, stall_metrics  # reuse

BASE = dict(sem_adapt=(0.6, 9.0), no_repeat=8, fn_penalty=0.25, grammar=0.5)  # grammar 0.5: the
STRENGTH = 2.0                                                                # grid's sweet spot


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    p = Predictor(utts[:50000], vocab)
    print("  earning distributional classes + scaffold + role tagger...")
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:50000], vocab)
    tree = SyntaxTree(scaffold)
    roles = RoleTagger(p.bigram, space.skeleton, space.anchors[0])
    skel = space.skeleton
    W = round(tree.binder.mean_constituent_len())

    # sanity: the earned roles must actually separate verbs from nouns
    vex = ["knew", "took", "said", "gave", "became"]
    nex = ["house", "city", "company", "street", "money"]
    mv = sum(roles.score(w) or 0 for w in vex) / len(vex)
    mn = sum(roles.score(w) or 0 for w in nex) / len(nex)
    print(f"  role tagger: verbs {vex} ~ {mv:.2f}  vs  nouns {nex} ~ {mn:.2f}  "
          f"(sep {'OK' if mv - mn > 0.3 else 'WEAK'})")

    prompts = [u for u in utts[50000:50090] if 6 <= len(u) <= 16]
    print(f"  {len(prompts)} prompts; flat-window W={W}\n")

    def verb_rate(words):
        content = [w for w in words if roles.score(w) is not None]
        return (sum(1 for w in content if roles.is_predicate(w)) / len(content)
                if content else 0.0)

    arms = {
        "baseline (off)": lambda: (0.0, None),
        "+flat-window":   lambda: (STRENGTH, FlatClassWindow(scaffold, W)),
        "+constituent":   lambda: (STRENGTH, ConstituentController(tree)),
        "+clause":        lambda: (STRENGTH, ClauseController(roles)),
    }

    # real-text reference
    rcyc = rvr = 0.0
    for u in prompts:
        ws = [w for w in u if w in vocab]
        m = stall_metrics(class_seq(ws, space))
        rcyc += m[0] if m else 0
        rvr += verb_rate(ws)
    rcyc /= len(prompts); rvr /= len(prompts)
    print(f"  REAL TEXT:  class-2cycle {rcyc:.0%}   verb-rate {rvr:.0%}\n")

    def guard(s, words):
        content = [w for w in words if w not in skel]
        active = set(sorted(s.sem_carry.weights, key=lambda c: -s.sem_carry.weights[c])[:10])
        on = (sum(1 for w in content if space.class_of(w) in active) / len(content)
              if content else 0.0)
        return (len(content) / max(1, len(words)), on, scaffold.seq_bits(words))

    agg = {name: [0.0] * 6 + [0] for name in arms}   # cyc, vrate, content, on, gram, _, n
    examples = {}
    for pi, u in enumerate(prompts):
        for name, make in arms.items():
            con, ctrl = make()
            s = Session(p, cmu, space=space, scaffold=scaffold, learn=False)
            s.read(" ".join(u))
            out = s.respond(n=24, temperature=0.7, rng_seed=pi, remember=False,
                            constituency=con, controller=ctrl, **BASE)
            words = [w for w, _, _ in out if w != "."]
            m = stall_metrics(class_seq(words, space))
            if m:
                g = guard(s, words)
                a = agg[name]
                a[0] += m[0]; a[1] += verb_rate(words)
                a[2] += g[0]; a[3] += g[1]; a[4] += g[2]; a[6] += 1
            if pi == 3:
                examples[name] = " ".join(words)

    print(f"  example continuation of: '{' '.join(prompts[3])[:50]}...'")
    for name in arms:
        print(f"    {name:<16} {examples.get(name, '')}")

    print(f"\n  metrics (mean over {len(prompts)} prompts, n=24):")
    print(f"    {'config':<16}{'2cycle':>8}{'verb-rate':>11}{'content':>9}{'on-top':>8}{'gram':>7}")
    print(f"    {'(real text)':<16}{rcyc:>7.0%}{rvr:>11.0%}{'--':>9}{'--':>8}{'--':>7}")
    for name in arms:
        a = agg[name]; c = a[6] or 1
        print(f"    {name:<16}{a[0]/c:>7.0%}{a[1]/c:>11.0%}{a[2]/c:>9.0%}{a[3]/c:>8.0%}{a[4]/c:>7.2f}")

    def col(name, j):
        return agg[name][j] / (agg[name][6] or 1)

    b, fw, cl = "baseline (off)", "+flat-window", "+clause"
    brakes = col(cl, 0) <= col(b, 0) - 0.02
    beats_window = col(cl, 0) <= col(fw, 0) + 0.02
    raises_verbs = col(cl, 1) >= col(b, 1) + 0.03 and abs(col(cl, 1) - rvr) <= abs(col(b, 1) - rvr)
    earns = brakes and beats_window and raises_verbs
    print(f"\n  ==> Q the CLAUSE controller (head-AWARE): stall {col(b,0):.0%}->{col(cl,0):.0%} "
          f"(real {rcyc:.0%}), verb-rate\n      {col(b,1):.0%}->{col(cl,1):.0%} (real {rvr:.0%}); "
          f"vs flat-window {col(fw,0):.0%} stall.")
    if earns:
        print(f"      EARNS its keep: the predicate/argument distinction the topical classes\n"
              f"      could NOT give lets the brake complete clauses (raise verbs) where the flat\n"
              f"      window only suppresses repeats -- head-awareness, finally load-bearing.")
    else:
        print(f"      Honest result: {'brakes the stall' if brakes else 'weak on the stall'}, "
              f"{'raises verbs' if raises_verbs else 'verb-rate flat'}, "
              f"{'beats' if beats_window else 'ties/loses to'} the window.\n"
              f"      The measurement is the finding; kept opt-in.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
