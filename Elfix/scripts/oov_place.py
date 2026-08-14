"""
scripts/oov_place.py  —  when does READING a word beat GUESSING it from its shape?
==================================================================================
The morphology->class bridge is weak (scripts/oov_gate: ~0.10 cosine to the true
class, a cold guess from shape). But PLACEMENT is distributional — so as a new word
is READ, its accumulating context should place it ever closer to its true class. This
finds the CROSSOVER: after how many occurrences does context-placement beat the
morphological cold-start? That is the point where the system should stop guessing from
shape and trust what it has read.

METHOD: build the space on the corpus (every word has a true class + signature). Take
frequent, decomposable content words as 'held-out OOV'. In one corpus pass, collect
each one's anchor co-occurrence occurrence-by-occurrence. Accumulate and, at
checkpoints k, PLACE it from the first k occurrences (SemanticSpace.place) and measure
cosine of its true signature to the placed class's centroid. Compare to the MORPHOLOGY
cold-start (constant) and the CEILING (its own true centroid).

Run:  python scripts/oov_place.py        (~1-2 min)
"""
import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.semantic import SemanticSpace, _dot
from elfix.oov import build_suffix_class, infer_class
from elfix.lexicon.ortho_affix import decompose

CAP = 80
CHECKPOINTS = [1, 2, 3, 5, 10, 20, 40, 80]
MIN_FREQ = 40


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    unigram = Counter(w for u in utts for w in u if w in vocab)
    space = SemanticSpace(utts, vocab, unigram=unigram)
    suffix_dom = build_suffix_class(space, cmu.__contains__)

    # held-out = frequent, decomposable content words (recur enough; have a morphology)
    held = {}
    for w, cid in space.word_class.items():
        if unigram[w] >= MIN_FREQ and decompose(w, cmu.__contains__):
            held[w] = cid
    print(f"{len(space.class_words)} classes; {len(held):,} frequent decomposable "
          f"words to place\n")

    # one corpus pass: ordered anchor-context per held-out word (capped)
    win = space.params["window"]
    ctx = defaultdict(list)
    for utt in utts:
        ws = [w for w in utt if w in vocab]
        for i, w in enumerate(ws):
            if w in held and len(ctx[w]) < CAP:
                c = Counter(ws[j] for j in range(max(0, i - win), min(len(ws), i + win + 1))
                            if j != i and ws[j] in space.anchor_set)
                if c:
                    ctx[w].append(c)

    # morphology cold-start baseline + ceiling
    morph = ceil = 0.0
    nm = 0
    for w, cid in held.items():
        sig = space.signatures[w]
        ceil += _dot(sig, space.centroids[cid])
        mcid, _ = infer_class(w, space, cmu.__contains__, suffix_dom)
        if mcid is not None:
            morph += _dot(sig, space.centroids[mcid])
            nm += 1
    ceil /= len(held)
    morph /= max(1, nm)

    # context-placement curve
    cos = {k: 0.0 for k in CHECKPOINTS}
    exact = {k: 0 for k in CHECKPOINTS}
    counted = {k: 0 for k in CHECKPOINTS}
    for w, cid in held.items():
        sig = space.signatures[w]
        acc = Counter()
        occ = ctx[w]
        for k in range(1, len(occ) + 1):
            acc += occ[k - 1]
            if k in cos:
                pcid, _ = space.place(acc, sum(acc.values()))
                if pcid is not None:
                    cos[k] += _dot(sig, space.centroids[pcid])
                    exact[k] += (pcid == cid)
                    counted[k] += 1

    print(f"  morphology cold-start (guess from shape): cosine {morph:.3f}")
    print(f"  ceiling (own true centroid):              cosine {ceil:.3f}\n")
    print(f"  context-placement as the word is READ:")
    print(f"    {'occ':>4}{'cosine':>9}{'exact%':>9}{'vs morph':>10}")
    crossover = None
    for k in CHECKPOINTS:
        if counted[k]:
            c = cos[k] / counted[k]
            e = exact[k] / counted[k]
            tag = "context wins" if c > morph else ""
            if c > morph and crossover is None:
                crossover = k
            print(f"    {k:>4}{c:>9.3f}{e:>8.0%}  {c - morph:>+8.3f}  {tag}")

    print(f"\n  ==> CROSSOVER at ~{crossover} occurrence(s): once a new word has been "
          f"read that\n      many times, its own accumulated CONTEXT places it better "
          f"than the morphological\n      guess from its SHAPE — rising from {morph:.2f} "
          f"toward the {ceil:.2f} ceiling. So the\n      system should cold-start a new "
          f"word from morphology, then RE-PLACE it by context\n      as it reads — sound "
          f"for the very first sighting, distribution once it has evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
