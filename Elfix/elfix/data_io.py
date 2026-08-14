"""
elfix/data_io.py  —  corpus + gold loaders
============================================
PROVENANCE: data/cmu_sample.txt and data/stress_sample.txt are samples of
ElfIX's data/cmu_preprocessed.txt and data/stress.txt (CMU Pronouncing
Dictionary, preprocessed). To run on the FULL corpus, just drop the originals
from your ElfIX archive into data/ — DEFAULT_CMU / DEFAULT_STRESS auto-detect
the full file when present and fall back to the bundled sample otherwise, so a
fresh checkout always runs and a full checkout always uses the real number.

The morpheme-boundary GOLD is derived honestly from the dictionary itself
([ElfIX] morphology / inflection_s pieces): a word W has a known boundary if
W = stem + productive_suffix and `stem` exists as its own dictionary entry whose
pronunciation is the prefix of W. This yields high-precision positive examples
with NO external annotation.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple

_HERE = Path(__file__).resolve().parent.parent
_DATA = _HERE / "data"


def _prefer(full: str, sample: str) -> Path:
    """Use the full corpus if it has been dropped in; else the bundled sample.
    Lets the gate run at full scale automatically without a fresh checkout
    breaking (the sample is always present)."""
    f = _DATA / full
    return f if f.exists() else _DATA / sample


DEFAULT_CMU = _prefer("cmu_preprocessed.txt", "cmu_sample.txt")
DEFAULT_STRESS = _prefer("stress.txt", "stress_sample.txt")

# Productive suffixes in PHONEME form (high precision; the seam is morphological).
# [ElfIX] inflection_s, morphology.
_SUFFIXES: List[List[str]] = [
    ["s"], ["z"],              # plural / 3sg  (cats, dogs)
    ["IH", "z"],              # -es  (buses)
    ["d"], ["t"], ["IH", "d"],  # past  (played, walked, wanted)
    ["IH", "NG"],             # -ing  (running)
    ["ER"], ["l", "IY"],       # -er, -ly  (faster, quickly)
    ["n", "IH", "s"],         # -ness
]


def load_cmu(path: Path = DEFAULT_CMU) -> Dict[str, List[str]]:
    """word -> phoneme list. Skips variant markers like 'a(2)'."""
    d: Dict[str, List[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "\t" not in line:
            continue
        w, phons = line.split("\t", 1)
        if "(" in w:                      # pronunciation variant -> skip
            continue
        d[w] = phons.split()
    return d


def load_syllable_counts(path: Path = DEFAULT_STRESS) -> Dict[str, int]:
    """word -> true syllable count (len of the stress-digit pattern)."""
    out: Dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "\t" not in line:
            continue
        w, pat = line.split("\t", 1)
        pat = pat.strip()
        if pat.isdigit():
            out[w] = len(pat)
    return out


def build_morpheme_gold(cmu: Dict[str, List[str]]
                        ) -> List[Tuple[str, List[str], int]]:
    """
    Return [(word, phonemes, boundary_index)] for words = stem + suffix where the
    stem is itself a dictionary entry. boundary_index is where the suffix begins.
    One source of truth (Law 3): the dictionary; the gold is a VIEW of it.
    """
    # index pronunciations -> set of phoneme tuples that are real words
    stems = {tuple(p) for p in cmu.values() if p}
    gold: List[Tuple[str, List[str], int]] = []
    for word, phons in cmu.items():
        for suf in _SUFFIXES:
            k = len(suf)
            if len(phons) > k and phons[-k:] == suf:
                stem = tuple(phons[:-k])
                if stem in stems and len(stem) >= 2:
                    gold.append((word, phons, len(phons) - k))
                    break
    return gold


if __name__ == "__main__":
    cmu = load_cmu()
    gold = build_morpheme_gold(cmu)
    print(f"cmu words: {len(cmu)}   morpheme-gold examples: {len(gold)}")
    for w, p, b in gold[:8]:
        print(f"  {w:>12}  {' '.join(p)}   | boundary at {b} -> "
              f"{' '.join(p[:b])} + {' '.join(p[b:])}")
