"""
scripts/carry_predict.py  —  does ACCUMULATED context predict the next word?
============================================================================
The arc so far:
  * phono backoff  -> the LAST WORD's SOUND does not predict the next word (the
    sound-class collapses to the function-word marginal). NEGATIVE.
  * converge probe -> the within-word path does not fold back (dissimilation, not
    harmony). NEGATIVE.
Both said the predictive signal is NOT in the local sound. The locator said it is
in SYNTAX/SEMANTICS. This gate tests the next candidate: ACCUMULATED CONTEXT, via
the Tier-5 leaky integrator (decaying_carry) applied to WORD IDENTITY instead of
the last word alone — a decaying CACHE of what was recently said. Topic words recur
("york ... york", "president ... kennedy ... president"), so if meaning is topical,
a decaying memory of recent words should beat the bigram.

This is the "second, slower carry for the ~0.2-bit topical residual" that
carry_revalidate flagged as the designated refinement. The cache decay rate is a
TIMESCALE we SWEEP (Law 1 — earned by which rate maximises held-out likelihood, not
chosen); the fast within-word rate is 0.67, topical memory should want a slower one.

CONTROL (the rigour): re-run the SAME cache with the test SENTENCES in shuffled
order. This keeps every within-sentence bigram AND every word frequency identical
(the baseline is unchanged) and destroys ONLY the CROSS-sentence topical adjacency.
So:  real lift = total cache benefit;  shuffled lift = the non-topical part (local
frequency tracking);  real - shuffled = the genuine TOPICAL component.

METHOD: bigram+unigram base trained on the first 90% of sentences; the held-out is
the CONTIGUOUS last 10% (real running text, so topical structure survives — an
every-Nth split would decimate it). A causal decaying word-cache runs ONLINE over
the test stream (uses only past test words). Interpolate
  P(next) = (1-beta) P_base(next | prev) + beta P_cache(next)
and score held-out bits/word. P_base is add-alpha smoothed; the cache reweights
toward recently-seen words. Lower bits = better.

Run:  python scripts/carry_predict.py
"""
import sys
import math
import random
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import MIN_CONTEXT

ALPHA = 0.1
PRUNE = 1e-3          # drop cache entries below this weight (keeps the cache small)
SEED = 0


def _build_base(train, vocab):
    bigram = defaultdict(Counter)
    unigram = Counter()
    for utt in train:
        ws = [w for w in utt if w in vocab]
        unigram.update(ws)
        for a, b in zip(ws, ws[1:]):
            bigram[a][b] += 1
    return bigram, unigram


def _score(stream, bigram, unigram, NU, V, rate, beta):
    """Causal held-out bits/word with a decaying word-cache at retention `rate`,
    interpolated at weight `beta`. `stream` is a list of utterances (word lists);
    the bigram context resets per utterance, the cache carries ACROSS them."""
    cache = {}                       # word -> decaying weight
    ctot = 0.0
    bits = 0.0
    n = 0
    for utt in stream:
        prev = None
        for w in utt:
            # predict w from base(prev) interpolated with the cache
            if prev is not None and prev in bigram and \
                    sum(bigram[prev].values()) >= MIN_CONTEXT:
                d = bigram[prev]; tot = sum(d.values())
            else:
                d = unigram; tot = NU
            p_base = (d.get(w, 0) + ALPHA) / (tot + ALPHA * V)
            p_cache = (cache.get(w, 0.0) / ctot) if ctot > 0 else 0.0
            p = (1 - beta) * p_base + beta * p_cache
            bits += -math.log2(p)
            n += 1
            # fold w into the decaying cache (Tier-5 leaky integrator over identity)
            for k in list(cache):
                cache[k] *= rate
                if cache[k] < PRUNE:
                    del cache[k]
            cache[w] = cache.get(w, 0.0) + (1 - rate)
            ctot = sum(cache.values())
            prev = w
    return bits / n if n else 0.0


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu.keys())
    utts = load_utterances()
    # contiguous train / dev / test (cache needs running text). Params are EARNED on
    # dev and reported on test -- never tuned on the test stream (Law 1 honesty).
    a, b_ = int(len(utts) * 0.8), int(len(utts) * 0.9)
    train, dev, test = utts[:a], utts[a:b_], utts[b_:]
    bigram, unigram = _build_base(train, vocab)
    NU, V = sum(unigram.values()), len(unigram)
    clean = lambda U: [w for u in U for w in [[x for x in u if x in vocab]] if w]
    dev_v = clean(dev); test_v = clean(test)

    # ── EARN (rate, beta) on DEV: the timescale + mixing that maximise dev likelihood
    print(f"train utts {len(train):,}  dev {len(dev_v):,}  test {len(test_v):,}  "
          f"vocab {V:,}")
    print("  earning (rate, beta) on DEV (the cache timescale + mixing weight):")
    print(f"    {'rate':>6} {'beta':>6} {'dev bits':>10}")
    best = (float('inf'), None, None)
    for rate in (0.9, 0.95, 0.98, 0.99, 0.995, 0.997):
        row = []
        for beta in (0.1, 0.2, 0.3, 0.4, 0.5):
            db = _score(dev_v, bigram, unigram, NU, V, rate, beta)
            row.append((db, rate, beta))
            if db < best[0]:
                best = (db, rate, beta)
        db, r, be = min(row)
        print(f"    {r:>6.3f} {be:>6.2f} {db:>10.3f}")
    _, brate, bbeta = best
    print(f"  -> EARNED on dev: rate {brate}, beta {bbeta}\n")

    # ── REPORT on TEST at the dev-earned params (held-out, untuned) ──────────────
    base = _score(test_v, bigram, unigram, NU, V, rate=0.0, beta=0.0)
    bbits = _score(test_v, bigram, unigram, NU, V, brate, bbeta)
    print(f"  TEST baseline (bigram + unigram, no carry): {base:6.3f} bits "
          f"(ppl {2**base:,.0f})")
    print(f"  TEST carry-conditioned (dev-earned params):  {bbits:6.3f} bits "
          f"(ppl {2**bbits:,.0f}), {base - bbits:+.3f} bits "
          f"({(2**base - 2**bbits)/2**base:+.1%} ppl)\n")

    # ── CONTROL: shuffle SENTENCE ORDER (kills cross-sentence topical adjacency
    # only; within-sentence bigrams + word frequencies unchanged -> base identical) ─
    rng = random.Random(SEED)
    shuf = test_v[:]
    rng.shuffle(shuf)
    shuf_carry = _score(shuf, bigram, unigram, NU, V, brate, bbeta)
    shuf_base = _score(shuf, bigram, unigram, NU, V, 0.0, 0.0)
    real_lift = base - bbits
    shuf_lift = shuf_base - shuf_carry            # non-topical (local-frequency) part
    topical = real_lift - shuf_lift               # the genuine accumulated-context gain
    print("  CONTROL (test SENTENCES shuffled -- cross-sentence topical adjacency "
          "destroyed):")
    print(f"    baseline {shuf_base:.3f} (== real base, as expected)  "
          f"carry {shuf_carry:.3f}  lift {shuf_lift:+.3f}\n")
    print(f"  decomposition of the {real_lift:+.3f} bit cache gain:")
    print(f"    non-topical (local frequency tracking): {shuf_lift:+.3f}")
    print(f"    TOPICAL (cross-sentence word memory):    {topical:+.3f}\n")

    genuine = real_lift > 0.05 and topical > 0.02
    if genuine:
        print(f"  ==> SIGNAL: accumulated context cuts held-out surprisal "
              f"{real_lift:.3f} bits/word\n      ({(2**base-2**bbits)/2**base:.0%} "
              f"perplexity), of which {topical:.3f} is genuine TOPICAL persistence\n"
              f"      (survives only with real sentence order) -- the Tier-5 carry "
              f"over WORD\n      IDENTITY at a slow ({brate}) timescale, the second "
              f"carry carry_revalidate\n      flagged. Where the LAST WORD's SOUND "
              f"failed (phono), ACCUMULATED word-memory\n      succeeds: the "
              f"predictive signal is topical, over time -- as the locator implied.")
    else:
        print(f"  ==> WEAK: the cache moves surprisal {real_lift:+.3f} bits but the "
              f"topical part is\n      only {topical:+.3f} (most is local-frequency "
              f"tracking) -- accumulated identity\n      adds little here. Honest "
              f"result; the topical residual is real but small.")
    return 0 if genuine else 1


if __name__ == "__main__":
    raise SystemExit(main())
