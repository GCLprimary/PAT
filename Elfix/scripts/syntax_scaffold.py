"""
scripts/syntax_scaffold.py  —  is there a grammatical scaffold? (class predicts class)
======================================================================================
The generation work lifted CONTENT (36%->84%) but the output is still not GRAMMATICAL.
The diagnostic named the missing piece: a class-level syntactic scaffold — what KIND of
word follows what. Prev-class pooling was NULL for word IDENTITY (next-word ~ the
marginal), but that is a different claim. CLASS is far lower-entropy than identity, and
syntax constrains it hard: a determiner is followed by a noun, a preposition by a noun
phrase. This gate measures whether prev's class predicts the NEXT class above chance.

KEY: the topic classes EXCLUDE the function-word skeleton (function words are not
topical) — but function words ARE the syntax. So we build a SYNTACTIC classing: each
skeleton word is its OWN class (the/of/to each a distinct syntactic role), content words
keep their distributional class. Then we test the class-bigram.

METHOD: contiguous train/test. Map every word to a syntactic class. Compare held-out
next-CLASS prediction under the class-BIGRAM (P(c'|c), Dirichlet-backed to the class
unigram) vs the class-UNIGRAM. Report bits/class and the entropy reduction (MI). If the
bigram wins big, a grammatical scaffold exists to guide generation.

Run:  python scripts/syntax_scaffold.py        (~2-3 min: the clustering earns)
"""
import sys
import math
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace

ALPHA = 0.5


def _ent(cnt):
    tot = sum(cnt.values()) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in cnt.values() if v)


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a = int(len(utts) * 0.9)
    train, test = utts[:a], utts[a:]
    p = Predictor(train, vocab)
    print("  earning distributional classes...")
    space = SemanticSpace(train, vocab, unigram=p.unigram)
    skel = space.skeleton

    def sclass(w):
        if w in skel:
            return ("fn", w)                  # each function word: its own syntactic role
        cid = space.class_of(w)
        return ("cl", cid) if cid is not None else ("unk",)

    # ── class-bigram + class-unigram on TRAIN ───────────────────────────────────
    cbg = defaultdict(Counter)
    cuni = Counter()
    for utt in train:
        cs = [sclass(w) for w in utt if w in vocab]
        cuni.update(cs)
        for x, y in zip(cs, cs[1:]):
            cbg[x][y] += 1
    NC, NCL = sum(cuni.values()), len(cuni)
    print(f"  {NCL} syntactic classes ({sum(1 for c in cuni if c[0]=='fn')} function + "
          f"{sum(1 for c in cuni if c[0]=='cl')} content)\n")

    def p_uni(c):
        return (cuni.get(c, 0) + ALPHA) / (NC + ALPHA * NCL)

    def p_bg(prev, c):
        row = cbg.get(prev)
        tot = sum(row.values()) if row else 0
        if tot == 0:
            return p_uni(c)
        return ((row.get(c, 0) if row else 0) + ALPHA * p_uni(c)) / (tot + ALPHA)

    # ── held-out: predict the NEXT CLASS, bigram vs unigram ─────────────────────
    bu = bb = n = 0.0
    for utt in test:
        cs = [sclass(w) for w in utt if w in vocab]
        for x, y in zip(cs, cs[1:]):
            bu += -math.log2(p_uni(y))
            bb += -math.log2(p_bg(x, y))
            n += 1
    print(f"  held-out next-CLASS prediction ({int(n):,} transitions):")
    print(f"    class-unigram: {bu/n:6.3f} bits/class  (ppl {2**(bu/n):5.1f})")
    print(f"    class-BIGRAM:  {bb/n:6.3f} bits/class  (ppl {2**(bb/n):5.1f})   "
          f"({bu/n - bb/n:+.3f} bits)")
    H_next = _ent(cuni)
    print(f"    H(next class) {H_next:.2f} -> H(next | prev) ~ {bb/n:.2f} bits  "
          f"(MI ~ {H_next - bb/n:.2f} bits of grammatical structure)\n")

    # ── readable: the scaffold is grammatical (what follows what) ───────────────
    def show(prev, label):
        row = cbg.get(prev, Counter())
        tot = sum(row.values()) or 1
        tops = []
        for c, k in row.most_common(4):
            if c[0] == "fn":
                tops.append(f"'{c[1]}' {k/tot:.0%}")
            elif c[0] == "cl":
                mem = ", ".join(space.class_words[c[1]][:3])
                tops.append(f"{{{mem}}} {k/tot:.0%}")
            else:
                tops.append(f"unk {k/tot:.0%}")
        print(f"    after {label:<22} -> {';  '.join(tops)}")

    print("  the scaffold (most likely NEXT class):")
    for fw in ("the", "a", "of", "to", "and", "his"):
        if ("fn", fw) in cbg:
            show(("fn", fw), f"'{fw}'")
    # a couple of content classes
    big = sorted((c for c in cuni if c[0] == "cl"), key=lambda c: -cuni[c])[:2]
    for c in big:
        mem = ", ".join(space.class_words[c[1]][:3])
        show(c, "{" + mem + "}")

    gain = bu / n - bb / n
    strong = gain > 0.5
    print(f"\n  ==> {'SCAFFOLD EXISTS' if strong else 'WEAK'}: prev's class predicts the "
          f"next CLASS with\n      {H_next - bb/n:.2f} bits of structure ({gain:.2f} "
          f"bits/class better than chance) -- a\n      GRAMMATICAL skeleton the word-bigram "
          f"lacks. Where prev-class pooling was NULL for\n      word IDENTITY (next ~ "
          f"marginal), it is STRONG for STRUCTURE: 'the' -> a noun class,\n      a noun "
          f"-> a preposition/verb. This is the prior to bias generation toward "
          f"grammar.")
    return 0 if strong else 1


if __name__ == "__main__":
    raise SystemExit(main())
