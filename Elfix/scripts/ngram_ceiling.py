"""
scripts/ngram_ceiling.py  —  is the 1st-order ceiling crossable by MORE class context?
======================================================================================
The class-BIGRAM (the syntactic scaffold) gave local grammar but the output stalls
inside a constituent ('president kennedy president kennedy ...') — it lacks phrase
CLOSURE. The question: does a higher-order class n-gram (trigram) recover that, or is
the missing structure not n-gram-able at all? Two confounds to separate:

  - at FINE granularity the trigram is DATA-STARVED (381^3 contexts) and overfits;
  - so we SWEEP class coarseness K and measure the trigram's gain over the bigram on
    held-out next-class. If a well-estimated (coarse) trigram buys real headroom, the
    ceiling is cheap (n-grams). If even the coarse trigram adds ~nothing, the missing
    structure is HIERARCHICAL (constituents), not linear — no flat n-gram captures it.

FINDING (reproduced here): the trigram crosses from hurting to helping around K~32-64
(confirming the sparsity confound), but where it helps the gain is NEGLIGIBLE
(~+0.02-0.03 bits/class, a tenth of the bigram's own gain). So higher-order class
n-grams add no real structure at ANY granularity -> the 1st-order ceiling is a
HIERARCHY problem (phrase structure), not a context-length one.

Run:  python scripts/ngram_ceiling.py        (~3-4 min: clusters at several K)
"""
import sys
import math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.semantic import build_anchors, _cooccurrence, _ppmi_signature, _kmeans, _dot

ALPHA = 0.5
KS = [8, 16, 32, 64, 128, 256]


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a = int(len(utts) * 0.9)
    train, test = utts[:a], utts[a:]
    unigram = Counter(w for u in train for w in u if w in vocab)
    print("  co-occurrence + PPMI signatures (ALL words, function words included)...")
    anchors = build_anchors(unigram, 600)
    cooc, amarg, wmarg, n = _cooccurrence(train, vocab, set(anchors), 2)
    sig = {}
    for w, cw in cooc.items():
        if wmarg[w] >= 5:
            s = _ppmi_signature(cw, wmarg[w], amarg, n, 40)
            if s:
                sig[w] = s
    clust = sorted(sig, key=lambda w: -unigram[w])[:2500]
    print(f"  {len(sig):,} signed words; sweeping class coarseness K\n")
    print(f"  {'K':>5}{'order1':>9}{'order2':>9}{'order3':>9}{'tri-gain':>10}")

    best_gain = -9.9
    for K in KS:
        cents, _ = _kmeans(clust, sig, K, 8, 0)
        wc = {w: max(range(len(cents)), key=lambda j: _dot(sig[w], cents[j])) for w in sig}
        sc = lambda w: wc.get(w, -1)
        uni, bg, tg = Counter(), defaultdict(Counter), defaultdict(Counter)
        for utt in train:
            cs = [sc(w) for w in utt if w in vocab]
            uni.update(cs)
            for x, y in zip(cs, cs[1:]):
                bg[x][y] += 1
            for x, y, z in zip(cs, cs[1:], cs[2:]):
                tg[(x, y)][z] += 1
        NC, NCL = sum(uni.values()), len(uni)
        pu = lambda c: (uni.get(c, 0) + ALPHA) / (NC + ALPHA * NCL)
        def pb(x, c):
            r = bg.get(x); t = sum(r.values()) if r else 0
            return pu(c) if t == 0 else (r.get(c, 0) + ALPHA * pu(c)) / (t + ALPHA)
        def pt(x, y, c):
            r = tg.get((x, y)); t = sum(r.values()) if r else 0
            return pb(y, c) if t == 0 else (r.get(c, 0) + ALPHA * pb(y, c)) / (t + ALPHA)
        b1 = b2 = b3 = m = 0.0
        for utt in test:
            cs = [sc(w) for w in utt if w in vocab]
            for i in range(1, len(cs)):
                c = cs[i]
                b1 += -math.log2(pu(c)); b2 += -math.log2(pb(cs[i - 1], c))
                b3 += -math.log2(pt(cs[i - 2] if i >= 2 else -1, cs[i - 1], c)); m += 1
        gain = b2 / m - b3 / m
        best_gain = max(best_gain, gain)
        print(f"  {K:>5}{b1/m:>9.3f}{b2/m:>9.3f}{b3/m:>9.3f}{gain:>+10.3f}")

    print(f"\n  ==> best trigram gain over bigram across all K: {best_gain:+.3f} bits/class.")
    print("      Higher-order class n-grams add ~nothing (negligible where well-estimated,")
    print("      sparsity-damaged where fine). The structure the output LACKS (phrase")
    print("      closure: 'close the noun phrase, start a predicate') is HIERARCHICAL, not")
    print("      linear -- no flat n-gram captures it. The 1st-order ceiling needs")
    print("      constituent structure, not more context. (A measured fork-decision.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
