"""
scripts/generate_quality.py  —  above the bigram floor, by the RIGHT metric
===========================================================================
The adaptive-topic gate proved the floor is perplexity-OPTIMAL: minimizing next-word
surprise PRODUCES the function-word salad. So lifting generation is a DIFFERENT
objective, and must be measured by generation metrics, not held-out bits. This scores
generation-time levers (heuristics that knowingly trade perplexity for content):

  content-rate  fraction of output tokens that are CONTENT words (1 - function-word).
  distinct      unique / total (anti-cycle diversity).
  repeat-2      fraction of 2-cycle repeats 'X _ X' (the carry's cycling).
  on-topic      fraction of CONTENT words whose class is in the active topic.

LEVERS (Session.respond):  sem_adapt (lean on topic at blind spots), no_repeat (break
carry cycles), fn_penalty (down-weight the earned function-word skeleton).

Run:  python scripts/generate_quality.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace
from elfix.session import Session

CONFIGS = {
    "baseline":   dict(),
    "+adapt":     dict(sem_adapt=(0.6, 9.0)),
    "+norepeat":  dict(no_repeat=4),
    "+fnpenalty": dict(fn_penalty=0.25),
    "all":        dict(sem_adapt=(0.6, 9.0), no_repeat=4, fn_penalty=0.25),
}


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    p = Predictor(utts[:50000], vocab)
    print("  earning distributional classes...")
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    prompts = [" ".join(u) for u in utts[50000:50050] if 5 <= len(u) <= 20]
    skel = space.skeleton
    print(f"  {len(space.class_words)} classes; {len(prompts)} prompts\n")

    def metrics(s, words):
        if not words:
            return None
        content = [w for w in words if w not in skel]
        active = set(sorted(s.sem_carry.weights, key=lambda c: -s.sem_carry.weights[c])[:10])
        on = (sum(1 for w in content if space.class_of(w) in active) / len(content)
              if content else 0.0)
        rep = sum(1 for i in range(2, len(words)) if words[i] == words[i - 2]) / max(1, len(words) - 2)
        return (len(content) / len(words), len(set(words)) / len(words), rep, on)

    agg = {name: [0.0, 0.0, 0.0, 0.0, 0] for name in CONFIGS}
    examples = {}
    for pi, prompt in enumerate(prompts):
        for name, kw in CONFIGS.items():
            s = Session(p, cmu, space=space, learn=False)   # no store -> no OOV growth
            s.read(prompt)
            out = s.respond(n=12, temperature=0.7, rng_seed=pi, remember=False, **kw)
            words = [w for w, _, _ in out]
            m = metrics(s, words)
            if m:
                a = agg[name]
                for j in range(4):
                    a[j] += m[j]
                a[4] += 1
            if pi == 1:
                examples[name] = " ".join(words)

    print(f"  example continuation of: '{prompts[1][:56]}...'")
    for name in CONFIGS:
        print(f"    {name:<11} {examples.get(name, '')}")
    print(f"\n  metrics (mean over {len(prompts)} prompts):")
    print(f"    {'config':<11}{'content%':>9}{'distinct':>9}{'repeat-2':>9}{'on-topic':>9}")
    base = None
    for name in CONFIGS:
        a = agg[name]
        c = a[4] or 1
        row = (a[0] / c, a[1] / c, a[2] / c, a[3] / c)
        if name == "baseline":
            base = row
        print(f"    {name:<11}{row[0]:>8.0%}{row[1]:>9.2f}{row[2]:>8.0%}{row[3]:>8.0%}")

    allr = tuple(agg["all"][j] / (agg["all"][4] or 1) for j in range(4))
    print(f"\n  ==> baseline -> all levers:  content {base[0]:.0%}->{allr[0]:.0%}, "
          f"distinct {base[1]:.2f}->{allr[1]:.2f}, repeat {base[2]:.0%}->{allr[2]:.0%}, "
          f"on-topic {base[3]:.0%}->{allr[3]:.0%}.")
    print("      The levers trade perplexity (measured negative) for CONTENT, DIVERSITY")
    print("      and TOPIC — the actual axes of 'above the floor'. Pick the config whose")
    print("      output reads best for the default; the trade is explicit, not hidden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
