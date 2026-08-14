"""
elfix/syllable.py  —  earned syllable-boundary gold (Maximal Onset)
=====================================================================
A heuristic-but-EARNED syllable-boundary reference, used to evaluate the Tier 2
sonority geometry on the job it is actually built for (syllabification), as
opposed to morphology (where the contour is structurally blind to ~half the
boundaries — see scripts/milestone1).

PROVENANCE
----------
- Legal-onset set: [ElfIX] onset_legality (why_piece1) — the inventory of legal
  onsets is a VIEW of one ground table (Law 3), re-derived from the corpus, never
  hand-listed. Here the ground table is the dictionary itself: an onset is legal
  iff it is attested WORD-INITIALLY somewhere in the corpus.
- Syllabification rule: [NEW->established] the Maximal Onset Principle — Kahn
  (1976), Selkirk (1982): a medial consonant cluster gives as many consonants as
  legally possible to the FOLLOWING syllable's onset; the remainder is the coda.

DESIGN LAW CHECK
----------------
Law 1 (earned geometry): the legal-onset set is counted from the corpus, not
declared. Law 3 (one source of truth): `legal_onsets` is a re-derivable view of
the dictionary; `test_syllable` asserts every gold onset is attested initially.

HONESTY
-------
This is a heuristic gold, NOT ground truth (CMU carries no syllable boundaries).
MOP is the standard textbook rule but real syllabification has ambisyllabicity
and stress effects it ignores. Reported as a reference, labelled as such — it is
INDEPENDENT of sonority, which is exactly what makes it a fair test of the
sonority geometry.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Iterable
from .substrate.features import features


def _is_vowel(sym: str) -> bool:
    f = features(sym)
    return f is not None and f.kind == "vowel"


def legal_onsets(corpus: Iterable[List[str]]) -> set:
    """
    Earned onset inventory: every consonant cluster attested word-INITIALLY in
    the corpus (the run of consonants before the first vowel of each word), plus
    the empty onset (a vowel-initial syllable). A view of the dictionary (Law 3).

    Single consonants come for free (many words begin with each); 2- and
    3-clusters (pl, tr, str, spl, ...) appear because words begin with them. We
    store FULL attested initial clusters; medial legality is tested by whether a
    cluster's suffix is itself in this set.

    >>> ons = legal_onsets([["s","t","r","IY","t"], ["t","IY"], ["AE","t"]])
    >>> ("s","t","r") in ons and ("t",) in ons and () in ons
    True
    """
    onsets = {()}
    for phons in corpus:
        cluster = []
        for s in phons:
            if _is_vowel(s):
                break
            if features(s) is None:      # unknown symbol -> stop the onset run
                break
            cluster.append(s)
        if cluster:
            onsets.add(tuple(cluster))
    return onsets


def mop_boundaries(phons: List[str], onsets: set) -> List[int]:
    """
    Maximal-Onset syllable boundaries for one word. Nuclei are the vowels; for
    each medial consonant run between two nuclei, the SECOND syllable's onset is
    the longest suffix of the run that is a legal onset, and the boundary sits at
    the start of that onset. Returns sorted interior boundary indices.

    >>> ons = legal_onsets([["s","t","r","IY","t"], ["k","AE","t"]])
    >>> mop_boundaries(["EH","k","s","t","r","AH"], ons)   # ek.stra (str onset)
    [2]
    >>> mop_boundaries(["k","AE","t"], ons)                 # monosyllable
    []
    """
    vows = [i for i, s in enumerate(phons) if _is_vowel(s)]
    bounds = []
    for v1, v2 in zip(vows, vows[1:]):
        run = phons[v1 + 1:v2]                 # consonants between the two nuclei
        split = len(run)                       # fallback: whole run is coda
        for k in range(len(run) + 1):          # shortest k -> longest onset suffix
            if tuple(run[k:]) in onsets:
                split = k
                break
        bound = v1 + 1 + split
        if 0 < bound < len(phons):
            bounds.append(bound)
    return sorted(set(bounds))


def build_syllable_gold(cmu: Dict[str, List[str]]
                        ) -> List[Tuple[str, List[str], List[int]]]:
    """
    [(word, phonemes, [boundary indices])] for every multisyllabic word, the
    boundaries placed by Maximal Onset over the corpus-earned onset set. One
    source of truth (Law 3): the dictionary; gold is a re-derived VIEW of it.
    """
    onsets = legal_onsets(cmu.values())
    gold = []
    for word, phons in cmu.items():
        if sum(1 for s in phons if _is_vowel(s)) >= 2:
            b = mop_boundaries(phons, onsets)
            if b:
                gold.append((word, phons, b))
    return gold


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=False)
    print("syllable.py doctests OK")
