"""
scripts/sentence_arc.py  —  is there a SUBJECT vs PREDICATE arc? (positional structure)
=======================================================================================
The class-bigram gave LOCAL grammar (of->the) but is position-blind, so the output runs
on with no sentence shape. The next structural question (the data's lead): do words have
a SUBJECT-region (early, before the verb) vs PREDICATE/OBJECT-region (late) tendency, and
where do sentences END? Both are positional, both earnable from the sentence-delimited
corpus.

THREE measurements over the syntactic classes (SyntaxScaffold's classing):
  1. POSITIONAL PROFILE  each class's mean normalized sentence position (0=first word,
                         1=last). Early classes = subject region, late = predicate/object
                         region — the subject->predicate arc, made readable.
  2. END-OF-SENTENCE     which classes COMPLETE sentences (the predicate's tail) — the
                         boundary signal generation needs to stop running on.
  3. PREDICTIVE          does conditioning the class-bigram on POSITION (early/mid/late)
                         predict the next class better than the position-blind bigram?

Run:  python scripts/sentence_arc.py        (~2-3 min: the clustering earns)
"""
import sys
import math
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold

ALPHA = 0.5


def _bucket(pos):
    return 0 if pos < 0.34 else (1 if pos < 0.67 else 2)   # early / mid / late


def _label(sc, c):
    if c[0] == "fn":
        return f"'{c[1]}'"
    if c[0] == "cl":
        return "{" + ", ".join(sc.space.class_words[c[1]][:3]) + "}"
    return "unk"


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a = int(len(utts) * 0.9)
    train, test = utts[:a], utts[a:]
    p = Predictor(train, vocab)
    print("  earning classes + scaffold...")
    space = SemanticSpace(train, vocab, unigram=p.unigram)
    sc = SyntaxScaffold(space, train, vocab)

    # ── one pass: position profile, end-rate, position-conditioned class-bigram ──
    pos_sum, pos_n = defaultdict(float), Counter()
    end_n, occ_n = Counter(), Counter()
    cbg = defaultdict(Counter)                       # position-blind class-bigram
    pbg = defaultdict(Counter)                       # (prev-class, posbucket) -> next-class
    for utt in train:
        cs = [sc.sclass(w) for w in utt if w in vocab]
        L = len(cs)
        if L < 2:
            continue
        for i, c in enumerate(cs):
            pos = i / (L - 1)
            pos_sum[c] += pos; pos_n[c] += 1
            occ_n[c] += 1
            end_n[c] += (i == L - 1)
        for i, (x, y) in enumerate(zip(cs, cs[1:])):
            cbg[x][y] += 1
            pbg[(x, _bucket(i / (L - 1)))][y] += 1
    meanpos = {c: pos_sum[c] / pos_n[c] for c in pos_n if pos_n[c] >= 50}

    # 1. POSITIONAL PROFILE — the subject->predicate arc
    ordered = sorted(meanpos, key=lambda c: meanpos[c])
    print(f"\n  POSITIONAL PROFILE (mean sentence position; the subject->predicate arc):")
    print("    SUBJECT region (earliest):")
    for c in ordered[:6]:
        print(f"      {meanpos[c]:.2f}  {_label(sc, c)}")
    print("    PREDICATE / OBJECT region (latest):")
    for c in ordered[-6:]:
        print(f"      {meanpos[c]:.2f}  {_label(sc, c)}")

    # 2. END-OF-SENTENCE — what completes a sentence
    endrate = {c: end_n[c] / occ_n[c] for c in occ_n if occ_n[c] >= 50}
    print(f"\n  END-OF-SENTENCE (classes most likely to COMPLETE a sentence):")
    for c in sorted(endrate, key=lambda c: -endrate[c])[:6]:
        print(f"      {endrate[c]:.0%}  {_label(sc, c)}")

    # 3. PREDICTIVE — does position help the class-bigram?
    NCL = len(occ_n)
    NC = sum(occ_n.values())
    def puni(c): return (occ_n.get(c, 0) + ALPHA) / (NC + ALPHA * NCL)
    def pb(table, key, c):
        row = table.get(key); tot = sum(row.values()) if row else 0
        if tot == 0:
            return puni(c)
        return (row.get(c, 0) + ALPHA * puni(c)) / (tot + ALPHA)
    bb = bp = n = 0.0
    for utt in test:
        cs = [sc.sclass(w) for w in utt if w in vocab]
        L = len(cs)
        if L < 2:
            continue
        for i, (x, y) in enumerate(zip(cs, cs[1:])):
            bb += -math.log2(pb(cbg, x, y))
            bp += -math.log2(pb(pbg, (x, _bucket(i / (L - 1))), y))
            n += 1
    print(f"\n  PREDICTIVE next-class ({int(n):,} held-out transitions):")
    print(f"    class-bigram (position-blind):  {bb/n:6.3f} bits")
    print(f"    + POSITION (early/mid/late):    {bp/n:6.3f} bits   ({bb/n - bp/n:+.3f})")

    arc = meanpos[ordered[-1]] - meanpos[ordered[0]]
    pos_gain = bb / n - bp / n
    strong = arc > 0.2
    print(f"\n  ==> {'ARC EXISTS' if strong else 'WEAK'}: classes span a sentence "
          f"position range of {arc:.2f}\n      (subject-region {meanpos[ordered[0]]:.2f} "
          f"-> predicate/object-region {meanpos[ordered[-1]]:.2f}), and sentences COMPLETE "
          f"on\n      predicate-tail classes -- a real subject->predicate ARC + boundary "
          f"signal. Position\n      adds {pos_gain:+.3f} bits to the class-bigram "
          f"({'useful prior' if pos_gain > 0.02 else 'small; the boundary/arc is the win, not next-class'}). "
          f"Wire\n      sentence position + an end-of-sentence model into generation for "
          f"bounded, arced output.")
    return 0 if strong else 1


if __name__ == "__main__":
    raise SystemExit(main())
