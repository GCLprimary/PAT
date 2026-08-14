"""
elfix/readout/recognition.py  —  Tier 7: confidence-gated commitment
======================================================================

PROVENANCE
----------
PORTED, near-verbatim, from cleankit `recognition_score.py` +
`score_to_temperature.py` (both doctest-green in the source). Canonical name:
adaptive / entropy-aware decoding. The point is that certainty is MEASURED
(how strongly the input is recognised), never a dialled constant.

  score = 1.0 (strong recognition) -> low  T -> sharpen, commit
  score = 0.0 (novel, no basis)    -> high T -> flatten, stay open

DESIGN LAW CHECK
----------------
Law 1: T_low / T_high are inspectable numbers, not tuned magic. N is the single
human-set window width, named and visible.
"""

from __future__ import annotations
from typing import Sequence, Callable

DEFAULT_WINDOW_N = 10


def recognition_ratio(stream: Sequence[str],
                      in_store: Callable[[str], bool],
                      n: int = DEFAULT_WINDOW_N) -> float:
    """
    Fraction of the last N stream symbols present in the store. Always [0, 1].
    Divides by N (not len(window)) so little evidence yields a LOW score —
    "no basis, stay open" — not false confidence. (cleankit KNOWN_GAPS sec E.)

    >>> known = {"a", "b", "c"}
    >>> recognition_ratio(list("aaaaaaaaaX"), lambda s: s in known, 10)  # 9 of 10
    0.9
    >>> recognition_ratio(list("ab"), lambda s: s in known, 10)   # short -> low
    0.2
    >>> recognition_ratio([], lambda s: s in known, 10)
    0.0
    """
    if n <= 0:
        raise ValueError("window N must be positive")
    if not stream:
        return 0.0
    window = list(stream)[-n:]
    hits = sum(1 for s in window if in_store(s))
    return hits / n


def score_to_temperature(score: float, t_low: float = 0.3,
                         t_high: float = 2.0) -> float:
    """
    Map recognition score [0,1] to reshape temperature. Linear, two visible
    constants. Higher score -> lower T (commit); lower score -> higher T (open).

    >>> score_to_temperature(1.0)
    0.3
    >>> score_to_temperature(0.0)
    2.0
    >>> round(score_to_temperature(0.5), 4)
    1.15
    >>> score_to_temperature(1.5)        # clamped
    0.3
    """
    if t_low <= 0:
        raise ValueError("t_low must be > 0")
    if t_high <= t_low:
        raise ValueError("t_high must be > t_low")
    s = 0.0 if score < 0.0 else (1.0 if score > 1.0 else float(score))
    return round(t_high - s * (t_high - t_low), 10)


def recognition_temperature(stream: Sequence[str],
                            in_store: Callable[[str], bool],
                            n: int = DEFAULT_WINDOW_N,
                            t_low: float = 0.3, t_high: float = 2.0) -> float:
    """Compose the two: stream -> recognition ratio -> temperature."""
    return score_to_temperature(recognition_ratio(stream, in_store, n),
                                t_low, t_high)
