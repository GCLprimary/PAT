"""
elfix/emergent/appendix.py  —  Tier 3: self-forming APPENDIX units (additive)
===============================================================================
The additive complement to the contour. milestone1 showed the sonority contour is
blind to ~52% of morpheme boundaries: a vowelless suffix (played = play+d) makes
no sonority seam. A SUBTRACTIVE refinement (geometry_boundaries_emergent) cannot
reach those. This module lets self-forming units PROPOSE the missing boundaries.

THE GEOMETRIC MOVE (why this is not just BPE / Morfessor)
--------------------------------------------------------
A candidate word-final fragment is described by its voicing-NEUTRAL articulatory
shape: (manner, place) per consonant, ('V',) per vowel. So /s/ and /z/ collapse to
ONE shape (coronal fricative), /t/ and /d/ to one (coronal stop). The model thereby
discovers that the -s/-z and -t/-d allomorphs are each a SINGLE appendix unit —
recovering allomorphy from feature geometry. Byte-Pair Encoding and frequency
morphology operate over symbol identity and structurally CANNOT merge allomorphs;
this is the readable, sound-grounded difference (SPEC Piece 3's whole novelty).

A shape is promoted to an appendix when it recurs word-finally across many DISTINCT
stems (productivity — the morphological signature), measured purely by counting:
no gradients, no stem-dictionary lookup (using "stem is a real word" would just be
the morpheme-gold's own definition — circular). Promotion is voicing-neutral shape
recurrence, full stop.

PROVENANCE
----------
- Self-forming promotion by recurrence: [NEW->original], same spirit as discover()
  (emergent_unit.py). Contrast baselines: unsupervised morphology by frequency/MDL
  — Morfessor, Creutz & Lagus (2007); BPE — Sennrich et al. (2016).
- Allomorphy as feature-geometric (voicing assimilation of the coronal inflections)
  is the articulatory grounding: [NEW->established] distinctive-feature theory.

DESIGN LAW CHECK
----------------
Law 1: the productivity threshold is corpus-relative (a fraction of the single most
productive ending), not an absolute magic number. OPEN (carried forward, NOT
closed): the exact fraction is not yet earned from first principles — standard
knee/MAD-outlier rules do NOT isolate the productive head of this heavy-tailed
distribution. The RESULT is robust to it (morpheme F1 0.57-0.63 across the top
2-5 shapes, all >> BPE ~0.33), but pinning the cutoff is the same open question the
spec already carries for the Tier-3 tightness threshold.

HONEST CAVEAT
-------------
The morpheme gold contains only DECOMPOSABLE words (stem+suffix). It therefore
cannot count false positives on monomorphemic words ending in -s/-t (bus, cat), so
the measured precision is optimistic and real-world segmentation is weaker. The
BPE baseline is scored on the same positives-only gold, so the COMPARISON is fair;
the absolute number is not a deployment estimate.

A legal-coda STEM gate (reject the cut unless the stem ends in an attested
word-final cluster) was MEASURED as a precision filter and rejected: it removes
only ~11% of decoy false positives at a ~3% true-positive cost, because most
monomorphemic stems (ox, bus) end in perfectly legal codas. The lesson is
structural: separating cat+s from ox needs stem-DISTRIBUTIONAL evidence (is the
stem a free word?), which is the morpheme-gold's own criterion — there is no
purely-geometric precision gate. Not built; documented instead.
"""
from __future__ import annotations
from collections import defaultdict
from typing import List, Dict, Tuple, Iterable, Optional, Set
from ..substrate.features import features
from .emergent_unit import geometry_boundaries


def phon_shape(sym: str) -> Optional[Tuple]:
    """Voicing-neutral articulatory shape of a phoneme: (manner, place) for a
    consonant, ('V',) for a vowel, None if unknown. Voicing is dropped on purpose
    so allomorphs (s/z, t/d) share a shape — the geometric generalization.

    >>> phon_shape("s") == phon_shape("z")    # coronal fricative, voicing-neutral
    True
    >>> phon_shape("t") == phon_shape("d")    # coronal stop
    True
    >>> phon_shape("s") == phon_shape("t")
    False
    >>> phon_shape("IY") == ("V",)
    True
    """
    f = features(sym)
    if f is None:
        return None
    return ("V",) if f.kind == "vowel" else (f.manner, f.place)


def discover_appendices(corpus: Iterable[List[str]], max_len: int = 2,
                        frac: float = 0.5) -> Set[Tuple]:
    """
    Self-forming appendix inventory: voicing-neutral word-final shapes (length 1..
    max_len) that recur across many DISTINCT stems. A shape is promoted when its
    stem-diversity is >= `frac` of the single most productive ending (scale-free,
    corpus-relative — see Law-1 note in the module header; `frac` is the open knob,
    the result is robust to it). Pure counting; no stem-dictionary lookup.
    """
    prod: Dict[Tuple, Set[Tuple]] = defaultdict(set)
    for ph in corpus:
        for k in range(1, max_len + 1):
            if len(ph) > k + 1:                       # require a stem of >= 2
                suf = tuple(phon_shape(x) for x in ph[-k:])
                if all(s is not None for s in suf):
                    prod[suf].add(tuple(ph[:-k]))
    if not prod:
        return set()
    cutoff = frac * max(len(st) for st in prod.values())
    return {suf for suf, st in prod.items() if len(st) >= cutoff}


def appendix_boundary(symbols: List[str], inventory: Set[Tuple],
                      max_len: int = 2) -> Optional[int]:
    """The single boundary proposed by the longest matching productive final
    shape, or None. Longest-match so a syllabic suffix (-es = V + coronal
    fricative) wins over its bare consonant."""
    for k in range(max_len, 0, -1):
        if len(symbols) > k + 1:
            suf = tuple(phon_shape(x) for x in symbols[-k:])
            if all(s is not None for s in suf) and suf in inventory:
                return len(symbols) - k
    return None


def geometry_boundaries_additive(symbols: List[str],
                                 inventory: Set[Tuple]) -> List[int]:
    """
    Contour boundaries PLUS the self-forming appendix boundary it misses. This is
    the ADDITIVE self-formation test: unlike the subtractive gate, it can place a
    boundary where the sonority contour has no seam, lifting morpheme recall past
    the ~52% contour ceiling. Always a SUPERSET of `geometry_boundaries`.
    """
    bs = set(geometry_boundaries(symbols))
    a = appendix_boundary(symbols, inventory)
    if a is not None and 0 < a < len(symbols):
        bs.add(a)
    return sorted(bs)
