"""
elfix/sonority.py  —  EARNED sonority magnitudes (Law 1)
==========================================================
Retires the longest-standing open question in the substrate (features.py): the
sonority ORDER is standard and defensible, but its SPACING (why nasals at 3, not
2.7) was a borrowed ordinal scale. This module earns the spacing from the corpus.

METHOD (non-circular by construction)
-------------------------------------
Sonority is *defined* as what rises toward the syllable nucleus and falls away
from it. So measure exactly that, from the corpus's own cluster phonotactics:

  - Syllabify every word with Maximal Onset (elfix/syllable.py). MOP uses the
    attested word-initial onset set, NOT sonority — so deriving sonority from MOP
    syllables does not assume the answer.
  - In an ONSET cluster, the segment closer to the nucleus is the more sonorous
    one (Sonority Sequencing Principle); in a CODA, the reverse. Each within-
    cluster pair (A outer, B inner) is one vote "B is more sonorous than A".
  - innerness(class) = votes-as-inner / votes-total = a pairwise win-rate, the
    earned relative sonority of each manner class. Vowels are the nucleus (never
    in a margin cluster) and pin the top of the scale.

PROVENANCE
----------
- The principle counted here: [NEW->established] Sonority Sequencing — Selkirk
  (1984), Clements (1990).
- Earned-from-corpus discipline and the open question being retired: [ElfIX]
  phoneme_features (why_piece2) — which flagged the spacing as a placeholder.
- Non-circular syllabification: elfix/syllable.py (attested onsets, Law 3).

DESIGN LAW CHECK
----------------
Law 1: the spacing now traces to a corpus count (pairwise cluster orderings).
The absolute envelope [1..5] is kept by an affine map onto the earned ranking,
because sonority is interval-arbitrary: only the ORDER and relative GAPS carry
meaning, and those are what is earned. `test_sonority` re-derives the order from
the corpus and asserts it (Law 3).
"""
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Iterable, Tuple
from .substrate.features import features
from .syllable import legal_onsets, mop_boundaries


def _manner(sym: str):
    f = features(sym)
    if f is None:
        return None
    return "vowel" if f.kind == "vowel" else f.manner


def innerness(corpus: Iterable[List[str]]) -> Dict[str, Tuple[float, int]]:
    """
    Per manner-class pairwise sonority win-rate: how often the class is the more
    sonorous (nucleus-closer) member of a within-cluster pair. Returns
    {manner_class: (innerness in [0,1], n_comparisons)}; higher = more sonorous.
    """
    corpus = list(corpus)
    onsets = legal_onsets(corpus)
    inner = defaultdict(int)
    seen = defaultdict(int)
    for phons in corpus:
        bnds = [0] + mop_boundaries(phons, onsets) + [len(phons)]
        for a, b in zip(bnds, bnds[1:]):
            syl = phons[a:b]
            vidx = [i for i, s in enumerate(syl)
                    if (f := features(s)) is not None and f.kind == "vowel"]
            if not vidx:
                continue
            onset = [_manner(s) for s in syl[:vidx[0]]]
            coda = [_manner(s) for s in syl[vidx[-1] + 1:]]
            # onset: larger index is closer to nucleus -> inner. coda: smaller index.
            for cluster, inner_is_later in ((onset, True), (coda, False)):
                k = len(cluster)
                for i in range(k):
                    for j in range(i + 1, k):
                        mi, mj = cluster[i], cluster[j]
                        if mi is None or mj is None or mi == mj:
                            continue
                        winner, loser = (mj, mi) if inner_is_later else (mi, mj)
                        inner[winner] += 1
                        seen[winner] += 1
                        seen[loser] += 1
    return {m: (inner[m] / seen[m], seen[m]) for m in seen if seen[m] > 0}


def derive_sonority(corpus: Iterable[List[str]],
                    lo: float = 1.0, hi: float = 4.0,
                    vowel: float = 5.0) -> Dict[str, float]:
    """
    Earned sonority magnitude per manner class. The interior SPACING is the
    earned cluster-innerness; the consonant envelope is affine-mapped to
    [lo, hi] (interval-arbitrary, preserves order and relative gaps), vowels at
    `vowel`. Manner classes never seen in a cluster fall back to the rank ends.

    Returns {manner_class: magnitude}. Pure counting; no gradients, no magic
    spacing (Law 1).
    """
    scores = innerness(corpus)
    cons = {m: s for m, (s, _) in scores.items() if m != "vowel"}
    if not cons:
        return {}
    smin, smax = min(cons.values()), max(cons.values())
    span = (smax - smin) or 1.0
    mag = {m: lo + (hi - lo) * (s - smin) / span for m, s in cons.items()}
    mag["vowel"] = vowel
    return mag


# ── The earned scale, frozen (Law 1 + Law 3) ──────────────────────────────────
# Magnitudes earned by derive_sonority() on the full CMU corpus (135k). Hardcoded
# here so the substrate need not re-count on every import; `test_sonority`
# RE-DERIVES the ranking from the corpus and asserts this order (Law 3 — a view
# of a corpus count, never hand-tuned). Note fricative < stop: the corpus, via
# /s/-clusters (st, sp, sk, str, ...), puts the sibilant fricative OUTERMOST, so
# the fricative class is genuinely less "nucleus-inner" than stops here. That is
# a real phonotactic fact, distinct from PHONETIC sonority (features.sonority,
# continuancy-based) which the morpheme cue still uses — the two are not collapsed.
PHONOTACTIC_SONORITY = {
    "fricative": 1.000, "affricate": 1.782, "stop": 1.953,
    "nasal": 3.095, "lateral": 3.858, "approximant": 4.000,
    "vowel": 5.000,
}


def sonority_phonotactic(symbol: str):
    """Earned (phonotactic) sonority for a symbol, or None if unknown. Used by
    the SYLLABLE contour (`syllable_boundaries`); the morpheme path keeps the
    phonetic `features.sonority`. Different measures, kept apart on purpose."""
    f = features(symbol)
    if f is None:
        return None
    return 5.0 if f.kind == "vowel" else PHONOTACTIC_SONORITY[f.manner]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    corpus = list(load_cmu().values())
    print("manner-class innerness (earned sonority win-rate):")
    for m, (s, n) in sorted(innerness(corpus).items(), key=lambda x: x[1][0]):
        print(f"  {m:12} innerness {s:.3f}   ({n:,} cluster comparisons)")
    print("\nearned magnitudes (affine to [1,4], vowels 5):")
    for m, v in sorted(derive_sonority(corpus).items(), key=lambda x: x[1]):
        print(f"  {m:12} {v:.3f}")
