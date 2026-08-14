"""
scripts/adaptive_topic.py  —  let the topic arbitrate the BLIND SPOTS (above the floor)
=======================================================================================
The generation diagnostic (the live query) found: the topic layer surfaces the RIGHT
content words, but they lose at the high-entropy decision points (every prompt's worst
spot was 'after the', H=11.8 bits) to the function-word marginal, because the topic
weight is a small CONSTANT. The fix this data points to: scale the topic weight with
the base distribution's ENTROPY — lean hard on the topic when the bigram is blind,
ignore it when the bigram is confident (where it could only dilute a correct answer).

  sem_beta(H) = bc_max * min(1, H / h_ref)

This gate measures whether that beats a FIXED topic weight on held-out perplexity. If
yes, the validated topic signal is allowed to decide exactly the moments it should.

METHOD: contiguous train/dev/test. base bigram+unigram (Dirichlet backoff) + word-cache
+ class-cache (the wired CarryCache / SemanticCarry). Earn the schedule on DEV, report
on TEST. H is the entropy of the base lexical distribution at each step.

Run:  python scripts/adaptive_topic.py        (~2-3 min: the clustering earns)
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor, CarryCache, MIN_CONTEXT
from elfix.semantic import SemanticSpace, SemanticCarry

ALPHA, RATE, K_BACK, BW = 0.1, 0.99, 5.0, 0.3


def _ent(cnt):
    tot = sum(cnt.values()) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in cnt.values() if v)


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a, b = int(len(utts) * 0.8), int(len(utts) * 0.9)
    train, dev, test = utts[:a], utts[a:b], utts[b:]
    p = Predictor(train, vocab)
    U, NU, V = p.unigram, sum(p.unigram.values()), len(p.unigram)
    H_uni = _ent(U)
    print(f"train {len(train):,}  dev {len(dev):,}  test {len(test):,}  vocab {V:,}")
    print("  earning distributional classes...")
    space = SemanticSpace(train, vocab, unigram=U)
    print(f"  {len(space.class_words)} classes; unigram entropy {H_uni:.1f} bits\n")

    clean = lambda S: [[w for w in u if w in vocab] for u in S]
    dev_v = [u for u in clean(dev) if u]
    test_v = [u for u in clean(test) if u]

    def p_base(prev, nxt):
        cnt = p.bigram.get(prev)
        att = sum(cnt.values()) if cnt else 0
        p_uni = (U.get(nxt, 0) + ALPHA) / (NU + ALPHA * V)
        if att == 0:
            return p_uni
        return (cnt.get(nxt, 0) + K_BACK * p_uni) / (att + K_BACK)

    def h_base(prev):
        cnt = p.bigram.get(prev)
        if cnt and sum(cnt.values()) >= MIN_CONTEXT:
            return _ent(cnt)
        return H_uni                       # blind context -> max uncertainty

    def score(stream, bc_of):
        """bc_of(prev) -> the topic weight for that step (fixed or entropy-adaptive)."""
        wc, sc = CarryCache(RATE), SemanticCarry(space, U, RATE)
        bits, n = 0.0, 0
        for utt in stream:
            prev = None
            for w in utt:
                if prev is not None:
                    bc = min(bc_of(prev), 1.0 - BW - 0.05)
                    pmix = ((1 - BW - bc) * p_base(prev, w)
                            + BW * wc.prob(w) + bc * sc.prob(w))
                    bits += -math.log2(pmix)
                    n += 1
                wc.observe(w); sc.observe(w); prev = w
        return bits / n if n else 0.0

    # ── earn the FIXED and ADAPTIVE topic weights on DEV ─────────────────────────
    base = score(dev_v, lambda prev: 0.0)
    fixed = min(((bc, score(dev_v, lambda prev, c=bc: c)) for bc in (0.1, 0.2, 0.3)),
               key=lambda t: t[1])
    adapt = min(((bm, hr, score(dev_v, lambda prev, m=bm, h=hr: m * min(1.0, h_base(prev) / h)))
                 for bm in (0.4, 0.6, 0.8) for hr in (6.0, 9.0, 12.0)),
                key=lambda t: t[2])
    print(f"  DEV: base {base:.3f} | best FIXED bc={fixed[0]} -> {fixed[1]:.3f} | "
          f"best ADAPTIVE bc_max={adapt[0]}, h_ref={adapt[1]} -> {adapt[2]:.3f}\n")

    # ── report on TEST at the dev-earned settings ────────────────────────────────
    t_base = score(test_v, lambda prev: 0.0)
    t_fixed = score(test_v, lambda prev, c=fixed[0]: c)
    t_adapt = score(test_v, lambda prev, m=adapt[0], h=adapt[1]:
                    m * min(1.0, h_base(prev) / h))
    print(f"  TEST bits/word:")
    print(f"    base (no topic)        {t_base:6.3f}")
    print(f"    fixed topic weight     {t_fixed:6.3f}   ({t_base - t_fixed:+.3f} vs base)")
    print(f"    ENTROPY-ADAPTIVE       {t_adapt:6.3f}   ({t_base - t_adapt:+.3f} vs base, "
          f"{t_fixed - t_adapt:+.3f} vs fixed)\n")

    gain = t_fixed - t_adapt
    if gain > 0.01:
        print(f"  ==> SIGNAL: letting the topic weight RISE with the base entropy beats "
              f"a fixed\n      weight by {gain:.3f} bits/word -- the topic arbitrates the "
              f"blind spots (high H,\n      e.g. after 'the') and stays out of the way "
              f"when the bigram is confident.\n      Wire sem_beta = {adapt[0]} * "
              f"min(1, H/{adapt[1]}) into predict()/respond.")
    else:
        print(f"  ==> WEAK: adaptive weighting moves test perplexity by only {gain:+.3f} "
              f"vs fixed.\n      The fixed topic weight already captures most of it; "
              f"adaptivity is not the lever\n      for perplexity (it may still help "
              f"GENERATION quality, measured separately).")
    return 0 if gain > 0.01 else 1


if __name__ == "__main__":
    raise SystemExit(main())
