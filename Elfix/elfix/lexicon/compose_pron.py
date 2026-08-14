"""
elfix/lexicon/compose_pron.py  —  Stage 2: compose a pronunciation via allomorphy
=================================================================================
pron(word) = pron(stem) + allomorph(suffix | stem-final phoneme), a stressless
ARPABET sequence matching cmu_preprocessed. The -s/-z and -t/-d allomorph
selection is EXACTLY the voicing-conditioned merge emergent/appendix.py earned —
the geometry that SEGMENTS the allomorphs is the geometry that GENERATES them.

PROVENANCE
----------
- The allomorphy (that -s/-z, -t/-d are one morpheme): emergent/appendix.py
  (earned, voicing-neutral shape recurrence).
- The voicing / sibilant / coronal-stop conditioning: [NEW->established] English
  inflectional phonology; the conditioning CLASSES are articulatory facts read
  from substrate/features.py (Law 1).

DESIGN LAW CHECK
----------------
Law 1/6: a readable, earned phonological rule — every branch is a feature test you
can recompute by hand, not a learned mapping. Stress is out of scope (the corpus
is stressless ARPABET); v1 covers the INFLECTIONAL suffixes only.
"""
from __future__ import annotations
from typing import List, Optional
from ..substrate.features import features

_SIBILANT = {"s", "z", "SH", "ZH", "CH", "JH"}     # -s -> syllabic /IH z/
_CORONAL_STOP = {"t", "d"}                          # -ed -> syllabic /IH d/


def _voiced(ph: str) -> bool:
    f = features(ph)
    return True if f is None else (f.kind == "vowel" or bool(f.voiced))


def _allomorph(suffix: str, last: str) -> Optional[List[str]]:
    """The earned allomorph of an inflectional suffix given the stem-final phoneme.
    None for suffixes without a v1 rule (derivational — deferred)."""
    if suffix in ("s", "es"):                       # plural / 3sg / possessive-less
        if last in _SIBILANT:
            return ["IH", "z"]
        return ["z"] if _voiced(last) else ["s"]
    if suffix == "ed":                              # past / participle
        if last in _CORONAL_STOP:
            return ["IH", "d"]
        return ["d"] if _voiced(last) else ["t"]
    if suffix == "ing":
        return ["IH", "NG"]
    if suffix == "er":
        return ["ER"]
    if suffix == "est":
        return ["IH", "s", "t"]
    return None


def compose(stem_pron: List[str], suffix: str) -> Optional[List[str]]:
    """
    Compose pron = stem_pron + earned allomorph(suffix | stem-final phoneme).
    None if the suffix has no v1 allomorph rule.

    >>> compose(["k", "AE", "t"], "s")        # voiceless -> /s/
    ['k', 'AE', 't', 's']
    >>> compose(["d", "AO", "g"], "s")        # voiced -> /z/
    ['d', 'AO', 'g', 'z']
    >>> compose(["b", "AH", "s"], "s")        # sibilant -> syllabic /IH z/
    ['b', 'AH', 's', 'IH', 'z']
    >>> compose(["w", "AO", "k"], "ed")       # voiceless -> /t/
    ['w', 'AO', 'k', 't']
    >>> compose(["w", "AO", "n", "t"], "ed")  # coronal stop -> syllabic /IH d/
    ['w', 'AO', 'n', 't', 'IH', 'd']
    """
    if not stem_pron:
        return None
    allo = _allomorph(suffix, stem_pron[-1])
    return None if allo is None else list(stem_pron) + allo
