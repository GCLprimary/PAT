"""
elfix/substrate/vectors.py  —  Tier 0: phoneme -> numeric point in R^d
========================================================================

PROVENANCE
----------
NEW (this system). Turns the ELfIX symbolic feature table (features.py) into a
numeric vector so units become POINTS and sequences become TRAJECTORIES
(Tier 2). Every axis is articulatory and named — Law 1 (earned geometry only).

The axes:
  0  sonority        ordinal loudness 1..5            [ElfIX phoneme_features]
  1  is_vowel        1.0 vowel / 0.0 consonant
  2  place_front_back  consonants: bilabial..glottal  (front=0 -> back=1)
  3  manner_open     stop..approximant (closed=0 -> open=1)
  4  voiced          0/1
  5  v_height        vowels: low..high (0..1), else 0  [formant F1 proxy]
  6  v_back          vowels: front..back (0..1), else 0 [formant F2 proxy]
  7  v_round         vowels rounding 0/1, else 0
  8  v_rhotic        vowels r-colouring 0/1, else 0    [F3 lowering]
  9  v_glide         diphthong glide TARGET on the same front..back axis as
                     v_back; 0.5 = no glide (monophthong). A diphthong is a
                     MOVEMENT in the vowel plane, so it belongs on this axis.

WHY AXES 8-9 EXIST (measured, not stylistic). Without them this encoding is not
injective: the 15 vowels land on 10 distinct points in R^d, with EY/EH/AY on one
point, AH/ER on another, and OW/AO/OY on a third. Tier 2 trajectories through
"bet" and "bait" were literally the same path. `_HEIGHT` mapping "diphthong" to
0.5 was where AY/OY were lost -- the diphthong height was erased at exactly the
step where it entered the geometry.

Grounding for the vowel axes as a 2-D space: Peterson & Barney (1952) formant
plane. Grounding for distinctive features as coordinates: Chomsky & Halle
(1968), SPE.

The encoding is DETERMINISTIC and TOTAL (unknown symbol -> None).
"""

from __future__ import annotations
from typing import Optional, List
from .features import features, Phoneme

DIM = 10
AXES = ["sonority", "is_vowel", "place_fb", "manner_open",
        "voiced", "v_height", "v_back", "v_round", "v_rhotic", "v_glide"]

# ── Ordinal maps (earned from articulation, front->back / closed->open) ───────
_PLACE = {  # front of mouth -> back
    "bilabial": 0.0, "labiodental": 0.10, "labialvelar": 0.15, "dental": 0.20,
    "alveolar": 0.35, "postalveolar": 0.50, "palatal": 0.65, "velar": 0.80,
    "glottal": 1.0,
}
_MANNER = {  # most closed -> most open (parallels but is not identical to sonority)
    "stop": 0.0, "affricate": 0.15, "fricative": 0.30,
    "nasal": 0.55, "lateral": 0.75, "approximant": 1.0,
}
_HEIGHT = {  # low (open jaw) -> high (close jaw)
    "low": 0.0, "mid": 0.5, "near-high": 0.75, "high": 1.0,
}
_BACK = {"front": 0.0, "central": 0.5, "back": 1.0}
# Glide targets live on the SAME axis as _BACK so the pair reads as a movement.
# "no glide" sits at the neutral midpoint, matching how vowels sit neutral on
# the consonant place axis -- absence of movement, not a third direction.
_GLIDE = {"front": 0.0, "back": 1.0, None: 0.5}


def vector(symbol: str) -> Optional[List[float]]:
    """
    Return the 8-d articulatory vector for `symbol`, or None if unknown.

    >>> v = vector("p")
    >>> len(v) == DIM
    True
    >>> vector("zzz") is None
    True
    >>> vector("IY")[1] == 1.0          # is_vowel
    True
    >>> vector("p")[1] == 0.0           # consonant
    True
    >>> vector("EH") != vector("EY")    # the encoding is injective over vowels
    True
    >>> vector("AH") != vector("ER") and vector("AO") != vector("OW")
    True
    """
    p: Optional[Phoneme] = features(symbol)
    if p is None:
        return None
    if p.kind == "vowel":
        return [
            p.sonority / 5.0,
            1.0,
            0.5,  # place axis is consonant-only; vowels sit neutral
            1.0,  # vowels are maximally open in manner
            1.0 if p.voiced is not False else 1.0,  # vowels are voiced
            _HEIGHT.get(p.height, 0.5),
            _BACK.get(p.backness, 0.5),
            1.0 if p.rounded else 0.0,
            1.0 if p.rhotic else 0.0,
            _GLIDE.get(p.offglide, 0.5),
        ]
    return [
        p.sonority / 5.0,
        0.0,
        _PLACE.get(p.place, 0.5),
        _MANNER.get(p.manner, 0.0),
        1.0 if p.voiced else 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0,
    ]


def encode(symbols: List[str]) -> List[List[float]]:
    """Encode a phoneme sequence into a list of vectors (skips unknowns)."""
    out = []
    for s in symbols:
        v = vector(s)
        if v is not None:
            out.append(v)
    return out


if __name__ == "__main__":
    for s in ["p", "l", "AE", "n", "t"]:
        print(f"{s:>3}", [round(x, 2) for x in vector(s)])
