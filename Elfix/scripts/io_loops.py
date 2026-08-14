"""
scripts/io_loops.py — the system on ACTUAL read<->respond loops, floor vs the deployed
FACTORED base. Gathers the live data the compartment work pointed at: does the +0.72-bit
factored win show up turn-by-turn in READ surprisal, and how does it move the LOCATOR and
generation (the two other surfaces the new base shifts)?
============================================================================================
Two sessions over the SAME reads, sharing the earned space/scaffold/roles but different
predictors: one plain (the floor), one with attach_factored (the deployed win). Each read
is scored by both; the factored session drives the topic, the typed locator (predicate/
argument + class), and the response.

Run:  python scripts/io_loops.py        (~2-3 min: the clustering earns)
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.lexicon.inferred_store import InferredStore
from elfix.session import Session


def read_surprisal(sess, line, vocab):
    """Mean per-word surprisal of `line` under `sess`'s predictor (before it reads)."""
    prev = next((w for w in reversed(sess.history) if w in sess.p.vocab), None)
    tot, n = 0.0, 0
    for w in line.split():
        if prev is not None and prev in sess.p.vocab and w in sess.p.vocab:
            tot += -math.log2(sess.p.prob(prev, w))
            n += 1
        prev = w
    return (tot / n) if n else 0.0, n


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    train = utts[:50000]
    p_floor = Predictor(train, vocab)
    p_fac = Predictor(train, vocab)
    print("  earning classes + scaffold...")
    space = SemanticSpace(train, vocab, unigram=p_floor.unigram)
    scaffold = SyntaxScaffold(space, train, vocab)
    p_fac.attach_factored(space, scaffold)
    print(f"  factored base attached (lambda={p_fac.factored_lam}); "
          f"{len(space.class_words)} classes\n")

    s_floor = Session(p_floor, cmu, store=InferredStore(cmu), space=space, scaffold=scaffold,
                      learn=False)
    s_fac = Session(p_fac, cmu, store=InferredStore(cmu), space=space, scaffold=scaffold,
                    learn=False, factored=True)

    # a contiguous run of Brown sentences (topically coherent), 6..16 words
    reads = [" ".join(u) for u in utts[52000:52120] if 6 <= len(u) <= 16][:8]

    print("=" * 94)
    print("READ <-> RESPOND LOOP  (surprisal: floor -> factored, bits/word)")
    print("=" * 94)
    agg_fl = agg_fa = agg_n = 0
    for i, line in enumerate(reads, 1):
        fl, n = read_surprisal(s_floor, line, vocab)
        fa, _ = read_surprisal(s_fac, line, vocab)
        agg_fl += fl * n; agg_fa += fa * n; agg_n += n
        s_floor.read(line)
        s_fac.read(line)
        print(f"\n[{i}] READ: {line}")
        print(f"    surprisal {fl:5.2f} -> {fa:5.2f} bits/word  ({fl - fa:+.2f}, {n} scored)"
              f"   topic: {', '.join(s_fac.topics(2))}")
        reply = s_fac.respond(n=16, temperature=0.6, rng_seed=i, boundaries=True)
        print(f"    RESPOND: {' '.join(w for w, _, _ in reply)}")

    print("\n" + "=" * 94)
    print(f"AGGREGATE read surprisal over {agg_n} words:  "
          f"floor {agg_fl/agg_n:.2f}  ->  factored {agg_fa/agg_n:.2f}  "
          f"({(agg_fl-agg_fa)/agg_n:+.2f} bits/word)")

    print("\nTYPED LOCATOR (factored session) — where meaning attached, and WHAT KIND:")
    for w, h, t, role in s_fac.locator_typed(6):
        kind = f"{role} {t}" if role else (t or "function/uncl.")
        print(f"    '{w}'  {h:4.0f} bits  --  {kind}")

    # what the factored base changed most: the words whose surprisal dropped the most
    print("\nWHERE FACTORED HELPED MOST (per-word floor->factored drop, this run):")
    drops = []
    for line in reads:
        prev = None
        for w in line.split():
            if prev is not None and prev in vocab and w in vocab:
                d = -math.log2(p_floor.prob(prev, w)) + math.log2(p_fac.prob(prev, w))
                drops.append((d, prev, w))
            prev = w
    for d, prev, w in sorted(drops, reverse=True)[:8]:
        print(f"    {prev} -> {w:<14} {d:+.1f} bits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
