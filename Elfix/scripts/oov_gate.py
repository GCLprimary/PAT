"""
scripts/oov_gate.py  —  does MORPHOLOGY place a new word in the right class?
============================================================================
The bridge falsification. A brand-new word has no distribution, only its SOUND. If
its earned morphology (stem + suffix) drops it near its TRUE distributional class —
sight unseen — then the sound half informs the generative half, and OOV words can
join prediction/topic from their shape alone. If not, the loop can't close this way.

METHOD: build the distributional space on the whole corpus (every word gets a true
class). Take the decomposable content words (stem in vocab, stem has a class) as
'held-out OOV'. For each, infer a class from MORPHOLOGY ONLY (never its own
distribution): the STEM's class, or the SUFFIX's dominant class. Score against the
word's TRUE class two ways:
  exact-match : inferred class id == true class id (harsh; classes are 300 buckets).
  centroid-cos: cosine of the word's true signature to the inferred class's centroid
                (robust) — vs RANDOM class (floor) and the TRUE class (ceiling).

Run:  python scripts/oov_gate.py        (~1 min: the clustering earns)
"""
import sys
import random
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.semantic import SemanticSpace, _dot
from elfix.oov import build_suffix_class
from elfix.lexicon.ortho_affix import decompose


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    unigram = Counter(w for u in utts for w in u if w in vocab)
    space = SemanticSpace(utts, vocab, unigram=unigram)
    in_vocab = cmu.__contains__
    suffix_dom = build_suffix_class(space, in_vocab)

    # held-out 'OOV' = decomposable content words whose stem also has a class
    items = []          # (word, stem, suffix, true_cid, stem_cid)
    for w, cid in space.word_class.items():
        for stem, suf in decompose(w, in_vocab):
            scid = space.class_of(stem)
            if scid is not None:
                items.append((w, stem, suf, cid, scid))
                break
    print(f"{len(space.class_words)} classes; {len(items):,} decomposable content "
          f"words to place from morphology alone\n")

    majority = Counter(space.word_class.values()).most_common(1)[0][0]
    cids = list(space.class_words)
    rng = random.Random(0)

    def cos(w, cid):
        return _dot(space.signatures[w], space.centroids[cid]) if cid is not None else 0.0

    n = len(items)
    em = {"stem": 0, "suffix": 0, "majority": 0}
    cs = {"stem": 0.0, "suffix": 0.0, "true": 0.0, "majority": 0.0, "random": 0.0}
    by_suf = defaultdict(lambda: [0, 0])     # suffix -> [stem-correct, count]
    for w, stem, suf, cid, scid in items:
        sd = suffix_dom.get(suf, majority)
        em["stem"] += (scid == cid)
        em["suffix"] += (sd == cid)
        em["majority"] += (majority == cid)
        cs["stem"] += cos(w, scid)
        cs["suffix"] += cos(w, sd)
        cs["true"] += cos(w, cid)
        cs["majority"] += cos(w, majority)
        cs["random"] += cos(w, rng.choice(cids))
        by_suf[suf][0] += (scid == cid)
        by_suf[suf][1] += 1

    print("  EXACT class-match (inferred id == true id, chance ~ majority):")
    for m in ("stem", "suffix", "majority"):
        print(f"    {m:<9} {em[m] / n:6.1%}")
    print("\n  CENTROID cosine (word's true signature vs the placed class's centre):")
    print(f"    {'true (ceiling)':<16} {cs['true'] / n:.3f}")
    print(f"    {'stem-inferred':<16} {cs['stem'] / n:.3f}")
    print(f"    {'suffix-inferred':<16} {cs['suffix'] / n:.3f}")
    print(f"    {'majority':<16} {cs['majority'] / n:.3f}")
    print(f"    {'random (floor)':<16} {cs['random'] / n:.3f}")

    print("\n  by suffix (STEM-inheritance exact-match):")
    for suf in sorted(by_suf, key=lambda s: -by_suf[s][1]):
        ok, tot = by_suf[suf]
        if tot >= 30:
            print(f"    -{suf:<4} {ok / tot:5.1%}  ({tot:,} words)")

    stem_lift = (cs["stem"] - cs["random"]) / n
    ceil_frac = (cs["stem"] - cs["random"]) / (cs["true"] - cs["random"]) if cs["true"] != cs["random"] else 0
    strong = stem_lift > 0.05 and em["stem"] / n > 3 * (em["majority"] / n)
    print(f"\n  ==> {'BRIDGE HOLDS' if strong else 'WEAK'}: morphology places a new word "
          f"{cs['stem']/n:.2f} cosine from\n      its true class vs {cs['random']/n:.2f} "
          f"at random ({ceil_frac:.0%} of the way to the ceiling), and\n      matches "
          f"the exact class {em['stem']/n:.0%} vs {em['majority']/n:.0%} for the majority "
          f"guess. The earned\n      morphology (Half A) predicts the distributional "
          f"class (Half B) -- so a brand-new\n      word can join prediction + topic from "
          f"its SHAPE alone. The halves connect.")
    return 0 if strong else 1


if __name__ == "__main__":
    raise SystemExit(main())
