"""
scripts/semantic_carry.py  —  does TOPIC (semantic-class memory) add over word memory?
======================================================================================
The prev-class pooling failed (semantic_gate): next-word identity is the function-word
marginal, so conditioning on prev's category does nothing. But the carry showed the
real signal is ACCUMULATED TOPIC — and that carry tracks exact WORD identity. The
semantic layer's one remaining predictive shot: GENERALISE the topic from exact words
to distributional CLASSES. When 'president' is read, a class-carry also primes
'senate, congress, governor' (its class) — so an unseen-but-on-topic word is predicted.

Test (contiguous held-out, causal/online, Dirichlet base):
  P(next) = (1-bw-bc) P_base(next|prev) + bw P_word-cache(next) + bc P_class-cache(next)
where P_class-cache(w) = (decaying activation of w's class) x (w's frequency share of
its class). The decisive comparison: does adding the class-cache (bc>0) beat the
word-cache alone? If yes, the distributional semantics generalise topic and earn a
predictive role; if no, the classes are real readable STRUCTURE but add nothing the
word-cache didn't already have.

Run:  python scripts/semantic_carry.py        (~1-2 min: the clustering earns)
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor, CarryCache
from elfix.semantic import SemanticSpace, SemanticCarry

ALPHA = 0.1
RATE = 0.99          # the slow topical timescale (carry_predict)
K_BACK = 5.0


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a, b = int(len(utts) * 0.8), int(len(utts) * 0.9)
    train, test = utts[:a], utts[b:]
    p = Predictor(train, vocab)
    U, NU, V = p.unigram, sum(p.unigram.values()), len(p.unigram)
    print(f"train utts {len(train):,}  test utts {len(test):,}  vocab {V:,}")
    print("  earning distributional classes (clustering)...")
    space = SemanticSpace(train, vocab, unigram=U)
    print(f"  {len(space.class_words)} classes over {len(space.word_class):,} content "
          f"words ({len(space.skeleton)} skeleton excluded)\n")

    test_v = [[w for w in u if w in vocab] for u in test]
    test_v = [u for u in test_v if u]

    def p_base(prev, nxt):
        cnt = p.bigram.get(prev)
        att = sum(cnt.values()) if cnt else 0
        p_uni = (U.get(nxt, 0) + ALPHA) / (NU + ALPHA * V)
        if att == 0:
            return p_uni
        return (cnt.get(nxt, 0) + K_BACK * p_uni) / (att + K_BACK)

    def score(bw, bc):
        """Measures the ACTUAL wired objects: CarryCache (words) + SemanticCarry
        (content-weighted class topic)."""
        wc = CarryCache(rate=RATE)
        sc = SemanticCarry(space, U, rate=RATE)
        bits, n = 0.0, 0
        for utt in test_v:
            prev = None
            for w in utt:
                if prev is not None:
                    pmix = ((1 - bw - bc) * p_base(prev, w)
                            + bw * wc.prob(w) + bc * sc.prob(w))
                    bits += -math.log2(pmix)
                    n += 1
                wc.observe(w)
                sc.observe(w)
                prev = w
        return bits / n if n else 0.0

    base = score(0.0, 0.0)
    word = score(0.4, 0.0)
    cls = score(0.0, 0.2)
    both = min(score(0.3, 0.15), score(0.35, 0.1), score(0.3, 0.2))
    print(f"  {'model':<28}{'bits/word':>10}{'ppl':>9}")
    for name, bv in (("base (bigram+unigram)", base),
                     ("+ word-cache (topic by WORD)", word),
                     ("+ class-cache (topic by CLASS)", cls),
                     ("+ word + class cache", both)):
        print(f"  {name:<28}{bv:>10.3f}{2**bv:>9,.0f}")
    add = word - both
    print(f"\n  class-cache adds over word-cache alone: {add:+.3f} bits/word")
    strong = add > 0.02
    if strong:
        print(f"  ==> SIGNAL: distributional CLASSES generalise topic beyond exact "
              f"words ({add:+.3f}\n      bits over the word-cache) -- the semantic layer "
              f"EARNS a predictive role: it\n      primes on-topic words the word-cache "
              f"never saw. Wire it as a topical prior.")
    else:
        print(f"  ==> WEAK: the class-cache adds {add:+.3f} bits over the word-cache -- "
              f"the topic the\n      classes capture is already captured by exact-word "
              f"recency on this corpus. The\n      distributional classes are real, "
              f"readable STRUCTURE (elfix/semantic) and TYPE the\n      locator's "
              f"surprises, but they do not add a PREDICTIVE signal here. Honest result.")
    return 0 if strong else 1


if __name__ == "__main__":
    raise SystemExit(main())
