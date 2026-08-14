"""
elfix/trajectory/trajectory.py  —  Tier 2: sequences as trajectories
======================================================================

PROVENANCE
----------
- Path-as-object: [Mind_Space] (numbers encoded as walks).
- Sonority slope as the load-bearing scalar: [ElfIX] slope_source (why_piece3),
  "more dimension, not more window" (factored modelling — Brown et al. 1992).
- Trajectory-as-unit grounding: [NEW->established] Articulatory Phonology,
  Browman & Goldstein (1986-1992): speech units ARE dynamical trajectories.
- Boundaries at sonority minima: [NEW->established] Sonority Sequencing
  Principle — Selkirk (1984), Clements (1990).

This is the rung where "sound forms shapes" stops being a slogan: the arch of
`plant` (p l AE n t) rising to the vowel and falling to the edges IS the
trajectory, earned entirely from Tier 0. No imported shape.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from ..substrate.features import sonority
from ..substrate.vectors import vector


@dataclass
class Trajectory:
    """A word's path through the feature space."""
    symbols: List[str]
    points: List[List[float]] = field(default_factory=list)   # R^DIM per symbol
    contour: List[float] = field(default_factory=list)        # sonority per symbol

    @classmethod
    def of(cls, symbols: List[str], son=None) -> "Trajectory":
        """Build a trajectory. `son` selects the sonority scale for the CONTOUR:
        default is phonetic (`features.sonority`, used by the morpheme path); pass
        `sonority.sonority_phonotactic` for the earned syllable contour. The
        feature `points` are always the phonetic vectors — only the contour shifts.
        """
        son = son or sonority
        pts, con, syms = [], [], []
        for s in symbols:
            v = vector(s)
            so = son(s)
            if v is None or so is None:
                continue
            pts.append(v)
            con.append(so)
            syms.append(s)
        return cls(symbols=syms, points=pts, contour=con)

    # ── sonority shape readers (earned from the contour) ──────────────────────
    def peaks(self) -> List[int]:
        """Indices of sonority local maxima (syllable nuclei candidates)."""
        c = self.contour
        out = []
        for i in range(len(c)):
            left = c[i] > c[i - 1] if i > 0 else True
            right = c[i] >= c[i + 1] if i < len(c) - 1 else True
            # a peak is strictly greater than at least one neighbour, >= the other
            if ((i == 0 or c[i] >= c[i - 1]) and (i == len(c) - 1 or c[i] >= c[i + 1])
                    and (i == 0 or c[i] > c[i - 1] or i == len(c) - 1 or c[i] > c[i + 1])):
                out.append(i)
        return out

    def minima(self) -> List[int]:
        """Indices of sonority local minima BETWEEN peaks (syllable seams)."""
        c = self.contour
        pk = self.peaks()
        seams = []
        for a, b in zip(pk, pk[1:]):
            # lowest point strictly between two peaks -> the seam
            lo_i, lo_v = a + 1, float("inf")
            for i in range(a + 1, b):
                if c[i] <= lo_v:
                    lo_v, lo_i = c[i], i
            seams.append(lo_i)
        return seams

    def coda_reversals(self) -> List[int]:
        """
        Indices where sonority RISES after a fall in the final falling tail —
        the 'appendix seam' (e.g. ...T(1) S(2) in 'cats'). English allows a
        sonority-reversing appendix at the word edge, and that reversal very
        often marks an APPENDED morpheme (-s, -z, -t, -d, -TH). Earned purely
        from the contour. See trajectory docstring / spec Piece 3.
        """
        c = self.contour
        out = []
        for i in range(1, len(c)):
            if c[i] > c[i - 1]:                 # a rise ...
                # ... that occurs after the last peak (i.e. in the coda tail)
                if all(c[j] <= c[i - 1] for j in range(i)) is False:
                    if i - 1 >= (self.peaks()[-1] if self.peaks() else 0):
                        out.append(i)
        return out

    def syllable_count(self) -> int:
        """Number of sonority peaks = predicted syllable count."""
        return max(1, len(self.peaks()))

    def __len__(self) -> int:
        return len(self.symbols)


if __name__ == "__main__":
    t = Trajectory.of(["p", "l", "AE", "n", "t"])
    print("symbols:", t.symbols)
    print("contour:", t.contour)
    print("peaks  :", t.peaks(), "-> syllables:", t.syllable_count())
    c = Trajectory.of(["k", "AE", "t", "s"])   # cats
    print("cats contour:", c.contour, "coda reversals:", c.coda_reversals())
