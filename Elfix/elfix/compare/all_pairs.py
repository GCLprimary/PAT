"""
elfix/compare/all_pairs.py  —  Tier 4: counted all-pairs attention
====================================================================

PROVENANCE
----------
- The mechanism: [Mind_Space] EXAMINE — the `Sync.` node turned into the N x N
  comparator (the 4x4 grid generalised). Seeded by [cleankit] similarity_recall
  (stream overlap) and [GCL] fft_normalize (a spectral alternate distance).
- Canonical name: [NEW->established] attention — Bahdanau et al. (2014),
  Vaswani et al. (2017), Attention Is All You Need — but in the READABLE
  variant: scores are counted similarities in the feature space, NOT learned
  Q*K. The O(n^2) cost buys simultaneity without surrendering interpretability.

DESIGN LAW CHECK
----------------
Law 6: no learned projections. Every weight w[i][j] is a cosine you can recompute
by hand from two readable feature vectors.
"""

from __future__ import annotations
from typing import List
import math


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def attention(points: List[List[float]], temperature: float = 1.0
              ) -> List[List[float]]:
    """
    All-pairs counted attention over a list of unit points. Returns a row-
    normalised weight matrix W where W[i][j] is how much unit i attends to
    unit j, based on cosine similarity in the readable feature space, sharpened
    by `temperature` (lower = sharper; pairs with Tier 7's recognition T).

    >>> W = attention([[1,0],[1,0],[0,1]])
    >>> len(W) == 3 and len(W[0]) == 3
    True
    >>> round(sum(W[0]), 6)            # rows sum to 1
    1.0
    >>> W[0][1] > W[0][2]             # unit 0 attends to its twin over its opposite
    True
    """
    n = len(points)
    if n == 0:
        return []
    t = max(1e-6, temperature)
    sims = [[_cosine(points[i], points[j]) for j in range(n)] for i in range(n)]
    W = []
    for i in range(n):
        exps = [math.exp(sims[i][j] / t) for j in range(n)]
        z = sum(exps) or 1.0
        W.append([e / z for e in exps])
    return W


def attended(points: List[List[float]], temperature: float = 1.0
             ) -> List[List[float]]:
    """Context-mixed points: each unit replaced by its attention-weighted blend."""
    W = attention(points, temperature)
    n = len(points)
    dim = len(points[0]) if points else 0
    out = []
    for i in range(n):
        out.append([sum(W[i][j] * points[j][k] for j in range(n))
                    for k in range(dim)])
    return out
