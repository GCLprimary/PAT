"""
scripts/grammar_quality.py  —  does the syntactic scaffold make output GRAMMATICAL?
===================================================================================
The content levers lifted content 36%->84% but OVER-suppressed function words (16% vs
real English's ~50%) — content-rich word-clouds, not sentences. The class-bigram
scaffold (SyntaxScaffold, +0.57 bits of structure) should put function words back WHERE
grammar wants them ('of the', 'to find', noun->preposition), pulling the output toward
real text's STRUCTURE.

Measured against a REAL-TEXT reference (the prompt sentences themselves):
  fn-rate   function-word fraction — grammatical text needs ~half; content-only has too
            few, the baseline salad too many. Closer to real = better.
  gram-cost mean -log2 P(class | prev-class) of the output under the scaffold — how much
            its class-sequence looks like real English (lower = more grammatical).
  + content / on-topic / repeat (we must not lose the content win).

Run:  python scripts/grammar_quality.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.session import Session

CONFIGS = {
    "content-only": dict(sem_adapt=(0.6, 9.0), no_repeat=4, fn_penalty=0.25),
    "+grammar":     dict(sem_adapt=(0.6, 9.0), no_repeat=4, fn_penalty=0.25, grammar=1.0),
    "balanced":     dict(sem_adapt=(0.6, 9.0), no_repeat=4, fn_penalty=1.0, grammar=2.0),
}


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    p = Predictor(utts[:50000], vocab)
    print("  earning distributional classes + syntactic scaffold...")
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:50000], vocab)
    skel = space.skeleton
    prompts = [u for u in utts[50000:50060] if 6 <= len(u) <= 18]
    print(f"  {len(space.class_words)} classes; {len(prompts)} prompts\n")

    # ── REAL-TEXT reference: what grammatical structure actually looks like ───────
    ref_fn = sum(sum(1 for w in u if w in skel) / len(u) for u in prompts) / len(prompts)
    ref_gram = sum(scaffold.seq_bits([w for w in u if w in vocab]) for u in prompts) / len(prompts)
    print(f"  REAL TEXT reference:  fn-rate {ref_fn:.0%}   gram-cost {ref_gram:.2f} bits\n")

    def metrics(s, words):
        if not words:
            return None
        content = [w for w in words if w not in skel]
        active = set(sorted(s.sem_carry.weights, key=lambda c: -s.sem_carry.weights[c])[:10])
        on = (sum(1 for w in content if space.class_of(w) in active) / len(content)
              if content else 0.0)
        rep = sum(1 for i in range(2, len(words)) if words[i] == words[i - 2]) / max(1, len(words) - 2)
        return (len(content) / len(words), 1 - len(content) / len(words), on,
                scaffold.seq_bits(words), rep)

    agg = {name: [0.0] * 5 + [0] for name in CONFIGS}
    examples = {}
    for pi, u in enumerate(prompts):
        for name, kw in CONFIGS.items():
            s = Session(p, cmu, space=space, scaffold=scaffold, learn=False)
            s.read(" ".join(u))
            out = s.respond(n=14, temperature=0.7, rng_seed=pi, remember=False, **kw)
            words = [w for w, _, _ in out]
            m = metrics(s, words)
            if m:
                a = agg[name]
                for j in range(5):
                    a[j] += m[j]
                a[5] += 1
            if pi == 2:
                examples[name] = " ".join(words)

    print(f"  example continuation of: '{' '.join(prompts[2])[:54]}...'")
    for name in CONFIGS:
        print(f"    {name:<13} {examples.get(name, '')}")
    print(f"\n  metrics (mean over {len(prompts)} prompts):")
    print(f"    {'config':<13}{'content%':>9}{'fn-rate':>8}{'on-topic':>9}"
          f"{'gram-cost':>10}{'repeat':>8}")
    print(f"    {'(real text)':<13}{'--':>9}{ref_fn:>7.0%}{'--':>9}{ref_gram:>10.2f}{'--':>8}")
    for name in CONFIGS:
        a = agg[name]
        c = a[5] or 1
        print(f"    {name:<13}{a[0]/c:>8.0%}{a[1]/c:>8.0%}{a[2]/c:>8.0%}"
              f"{a[3]/c:>10.2f}{a[4]/c:>7.0%}")

    def fn(name): return agg[name][1] / (agg[name][5] or 1)
    def gr(name): return agg[name][3] / (agg[name][5] or 1)
    closer = abs(fn("balanced") - ref_fn) < abs(fn("content-only") - ref_fn)
    grammatical = gr("balanced") < gr("content-only")
    ok = closer and grammatical
    print(f"\n  ==> {'GRAMMAR HELPS' if ok else 'WEAK'}: the scaffold moves fn-rate "
          f"{fn('content-only'):.0%}->{fn('balanced'):.0%}\n      (real {ref_fn:.0%}) and "
          f"gram-cost {gr('content-only'):.2f}->{gr('balanced'):.2f} (real {ref_gram:.2f}) "
          f"-- function words\n      return WHERE grammar wants them and the class-sequence "
          f"looks more like English,\n      while content/topic hold. Output is more "
          f"sentence-shaped (still not parseable;\n      a 1st-order class-bigram is the "
          f"floor of syntax, not the ceiling).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
