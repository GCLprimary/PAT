"""
elfix/substrate/features.py  —  Tier 0 substrate (the feature space)
======================================================================

PROVENANCE
----------
PORTED, faithfully, from ElfIX `cleankit/phoneme_features.py` (why_piece2).
The inventory, the "differ only where they differ" representation, and the
ordinal sonority scale are kept verbatim in spirit. Grounded in published
distinctive-feature theory:
  - Jakobson, Fant & Halle (1952), Preliminaries to Speech Analysis
  - Chomsky & Halle (1968), The Sound Pattern of English (SPE)
  - Clements (1985) / Sagey (1986), Feature Geometry
Vowel height/backness as a 2-D space is grounded in the formant plane:
  - Peterson & Barney (1952).

DESIGN LAW CHECK
----------------
Law 1 (earned geometry only): the axes here are articulation, not invention.
This is the one place geometry is GIVEN rather than built.

OPEN QUESTION (largely retired — see elfix/sonority.py)
---------------------------------------------------------
This `sonority` field is the PHONETIC scale (continuancy/openness ordinal: stops
1 ... vowels 5). Its spacing was the borrowed placeholder ElfIX flagged. It is
now joined by an EARNED PHONOTACTIC scale derived from corpus cluster orderings
(elfix/sonority.py): the two are KEPT APART on purpose (dual scale), because
they genuinely disagree on /s/ — phonetically sonorant-ish (continuant), but the
outermost appendix of every s-cluster phonotactically. The morpheme path uses
this phonetic scale (the coda-reversal plural cue needs s > stop); the SYLLABLE
contour uses the earned phonotactic scale (syllable F1 0.86 -> 0.93). What
remains open: this phonetic spacing itself is still ordinal, not measured — but
it is now a deliberate, documented companion to an earned scale, not an
un-interrogated placeholder.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Phoneme:
    """A phoneme's articulatory feature vector (ported from ElfIX)."""
    symbol: str
    kind: str                       # "consonant" | "vowel"
    place: Optional[str] = None     # consonant features (None for vowels)
    manner: Optional[str] = None
    voiced: Optional[bool] = None
    height: Optional[str] = None    # vowel features (None for consonants)
    backness: Optional[str] = None
    rounded: Optional[bool] = None
    rhotic: Optional[bool] = None   # r-coloured nucleus: ER vs AH
    offglide: Optional[str] = None  # diphthong glide target: "front"|"back"|None
    sonority: float = 0.0           # shared scalar; governs syllable structure


def _c(sym, place, manner, voiced, son):
    return Phoneme(sym, "consonant", place=place, manner=manner,
                   voiced=voiced, sonority=son)


def _v(sym, height, backness, rounded, rhotic=False, offglide=None):
    return Phoneme(sym, "vowel", height=height, backness=backness,
                   rounded=rounded, rhotic=rhotic, offglide=offglide,
                   sonority=5.0)


# ── Consonants (General American) ─────────────────────────────────────────────
_CONSONANTS = {
    "p":  _c("p",  "bilabial",     "stop",         False, 1.0),
    "b":  _c("b",  "bilabial",     "stop",         True,  1.0),
    "t":  _c("t",  "alveolar",     "stop",         False, 1.0),
    "d":  _c("d",  "alveolar",     "stop",         True,  1.0),
    "k":  _c("k",  "velar",        "stop",         False, 1.0),
    "g":  _c("g",  "velar",        "stop",         True,  1.0),
    "f":  _c("f",  "labiodental",  "fricative",    False, 2.0),
    "v":  _c("v",  "labiodental",  "fricative",    True,  2.0),
    "TH": _c("TH", "dental",       "fricative",    False, 2.0),  # thin
    "DH": _c("DH", "dental",       "fricative",    True,  2.0),  # this
    "s":  _c("s",  "alveolar",     "fricative",    False, 2.0),
    "z":  _c("z",  "alveolar",     "fricative",    True,  2.0),
    "SH": _c("SH", "postalveolar", "fricative",    False, 2.0),  # ship
    "ZH": _c("ZH", "postalveolar", "fricative",    True,  2.0),  # measure
    "h":  _c("h",  "glottal",      "fricative",    False, 2.0),
    "CH": _c("CH", "postalveolar", "affricate",    False, 1.5),  # chip
    "JH": _c("JH", "postalveolar", "affricate",    True,  1.5),  # jump
    "m":  _c("m",  "bilabial",     "nasal",        True,  3.0),
    "n":  _c("n",  "alveolar",     "nasal",        True,  3.0),
    "NG": _c("NG", "velar",        "nasal",        True,  3.0),  # sing
    "l":  _c("l",  "alveolar",     "lateral",      True,  4.0),
    "r":  _c("r",  "alveolar",     "approximant",  True,  4.0),
    "j":  _c("j",  "palatal",      "approximant",  True,  4.0),  # yes
    "w":  _c("w",  "labialvelar",  "approximant",  True,  4.0),
}

# ── Vowels (General American) ─────────────────────────────────────────────────
# Vowels are (height, backness, rounded, rhotic, offglide). The last two exist
# because without them the inventory is NOT injective: EH/EY, AH/ER and AO/OW
# share every other feature, and in the R^d encoding (vectors.py) AY and OY
# collapsed onto them as well -- 15 vowels landing on 10 distinct points, which
# no downstream tier could recover from. `offglide` also retires the category
# error of `height="diphthong"`: a diphthong's glide is a DIRECTION, not a
# height, which is the trajectory-shaped reading Tier 2 already assumes.
_VOWELS = {
    "IY": _v("IY", "high",      "front",   False),                    # beat
    "IH": _v("IH", "near-high", "front",   False),                    # bit
    "EY": _v("EY", "mid",       "front",   False, offglide="front"),  # bait
    "EH": _v("EH", "mid",       "front",   False),                    # bet
    "AE": _v("AE", "low",       "front",   False),                    # bat
    "AH": _v("AH", "mid",       "central", False),                    # but
    "ER": _v("ER", "mid",       "central", False, rhotic=True),       # bird
    "UW": _v("UW", "high",      "back",    True),                     # boot
    "UH": _v("UH", "near-high", "back",    True),                     # book
    "OW": _v("OW", "mid",       "back",    True,  offglide="back"),   # boat
    "AO": _v("AO", "mid",       "back",    True),                     # bought
    "AA": _v("AA", "low",       "back",    False),                    # bother
    "AY": _v("AY", "low",       "central", False, offglide="front"),  # bite
    "AW": _v("AW", "low",       "central", False, offglide="back"),   # bout
    "OY": _v("OY", "mid",       "back",    True,  offglide="front"),  # boy
}

_TABLE = {**_CONSONANTS, **_VOWELS}


def features(symbol: str) -> Optional[Phoneme]:
    """
    Return the Phoneme feature vector for `symbol`, or None if unknown.
    Total: defined for every input (unknown -> None, never raises).

    >>> p, q = features("p"), features("b")
    >>> p.place == q.place and p.manner == q.manner and p.voiced != q.voiced
    True
    >>> features("zzz") is None
    True
    >>> features("s").sonority < features("l").sonority
    True
    """
    return _TABLE.get(symbol)


def sonority(symbol: str) -> Optional[float]:
    """Sonority scalar for a symbol, or None if unknown."""
    p = _TABLE.get(symbol)
    return None if p is None else p.sonority


def inventory() -> list[str]:
    """All known phoneme symbols (consonants then vowels)."""
    return list(_TABLE.keys())


if __name__ == "__main__":
    print("inventory size:", len(inventory()))
    print("p :", features("p"))
    print("IY:", features("IY"))
