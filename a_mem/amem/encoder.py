"""The hybrid encoder (D-1) — write-time-only placement.

Probe 15 killed hash-based placement: re-deriving a lattice position from
a noisy embedding round-trips at 42%. The law that survives it: the
encoder chooses placements at WRITE time only (maximizing separation from
existing placements, D-3); recall never re-derives a placement — it goes
embedding -> nearest-neighbor match -> episode id -> anchor recall.

The embedding index is deliberately minimal (numpy cosine over stored
unit vectors) behind a protocol, so a real vector DB can replace it
without touching a_mem (D-5).
"""
from typing import Protocol, runtime_checkable

import numpy as np

from . import constants as K


class PlacementFull(RuntimeError):
    """The placement zone cannot fit another episode at the minimum
    separation (packing-limited: ~9 slots at Chebyshev-5 on the 13-wide
    zone). Grid scaling is future work, not Phase 3."""


@runtime_checkable
class EmbeddingIndex(Protocol):
    """Minimal nearest-neighbor store; replaceable by a real vector DB."""

    def add(self, key, vector):
        ...

    def nearest(self, vector):
        """-> (key, score)"""
        ...

    def __len__(self):
        ...


class NumpyEmbeddingIndex:
    """Cosine nearest-neighbor over unit-normalized stored vectors."""

    def __init__(self):
        self._vecs = {}

    @staticmethod
    def _unit(v):
        v = np.asarray(v, dtype=float).ravel()
        n = np.linalg.norm(v)
        if n == 0:
            raise ValueError("cannot index a zero embedding")
        return v / n

    def add(self, key, vector):
        self._vecs[key] = self._unit(vector)

    def nearest(self, vector):
        if not self._vecs:
            raise ValueError("nearest() on an empty index")
        q = self._unit(vector)
        scores = {k: float(q @ v) for k, v in self._vecs.items()}
        best = max(scores, key=scores.get)
        return best, scores[best]

    def __len__(self):
        return len(self._vecs)

    def keys(self):
        return list(self._vecs)


class Encoder:
    """Write-time placement optimizer + shape selection.

    `place()` returns candidate positions ranked by separation from the
    existing placements (max-min Chebyshev, corner-first deterministic
    tie-break) and raises PlacementFull when the zone cannot take another
    episode at min_sep. It also counts its own invocations — the spy that
    lets tests prove the recall path never derives a placement.
    """

    def __init__(self, grid=K.GRID, zone_min=K.PLACE_ZONE_MIN,
                 zone_max=K.PLACE_ZONE_MAX, min_sep=K.PLACE_MIN_SEP, seed=0):
        self.grid = grid
        self.zone_min, self.zone_max = zone_min, zone_max
        self.min_sep = min_sep
        self._rng_seed = seed
        self._shape_axis = None
        self.place_calls = 0        # spy: placement derivations

    # ── placement (write-time only) ──────────────────────────────────
    def place(self, placed, shape=None):
        """Ranked candidate positions for a new episode.

        placed: existing [(cx, cy), ...]. shape: offsets the pattern will
        occupy — candidates that would push any cell off the lattice are
        excluded (probe 15 silently clipped such cells; a stored pattern
        must be stored whole). Returns candidates ordered by decreasing
        minimum Chebyshev distance to the placed set (ties: lexicographic).
        Raises PlacementFull when even the best candidate sits closer than
        min_sep to an existing episode.
        """
        self.place_calls += 1
        candidates = []
        for cy in range(self.zone_min, self.zone_max + 1):
            for cx in range(self.zone_min, self.zone_max + 1):
                if shape is not None and any(
                        not (0 <= cx + dx < self.grid
                             and 0 <= cy + dy < self.grid)
                        for dx, dy in shape):
                    continue
                if placed:
                    d = min(max(abs(cx - ox), abs(cy - oy))
                            for ox, oy in placed)
                else:
                    d = self.zone_max - self.zone_min + 1
                candidates.append((-d, cx, cy))
        candidates.sort()
        if not candidates:
            raise PlacementFull("no candidate position fits this shape")
        best_sep = -candidates[0][0]
        if placed and best_sep < self.min_sep:
            raise PlacementFull(
                f"no free slot at Chebyshev >= {self.min_sep} "
                f"({len(placed)} episodes placed)")
        return [(cx, cy) for _, cx, cy in candidates]

    # ── shape selection (deterministic projection, probe 15) ─────────
    def shape_for(self, embedding):
        emb = np.asarray(embedding, dtype=float).ravel()
        if self._shape_axis is None or self._shape_axis.size != emb.size:
            axis = np.random.default_rng(self._rng_seed).normal(size=emb.size)
            self._shape_axis = axis / np.linalg.norm(axis)
        return (K.SEED_CONSTELLATION if float(emb @ self._shape_axis) > 0
                else K.LINE_CONSTELLATION)
