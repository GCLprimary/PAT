"""R-1: the linear organ — two rulers unfolded from the lattice
(probes 36, 36b).

The 2D field carries two diagonals: the side-vs-diagonal differential
(1 : √2, the ad-quadratum pair the contraction's z/(1+i) walks) and the
3-4-5 seam of the quartered core (hypotenuse exactly 5 against the side
ruler's 4 — the 5:4 just major third). Folded back out linearly they
become two clocks:

  IRRATIONAL FOR IDENTITY, RATIONAL FOR RHYTHM (law 1 of this build).
  The √2 ruler's stamps never repeat — by Weyl equidistribution its
  phases spread uniformly, so it can ORDER and NEST but provably cannot
  detect a period. The 5:4 ruler re-aligns every 20 positions (the
  4-against-5 polyrhythm), so it can find CYCLES but stamps nothing
  uniquely. One organ, two clocks, each unable to do the other's job.

EXACTNESS EXTENDS TO Z[√2] (law 2). A stamp is an integer pair (m, n)
meaning m + n·√2. Ordering is pure integer arithmetic: sign(m + n√2)
resolves by comparing m² against 2n² (no nonzero integer tie exists —
√2 is irrational). No float is ever evaluated in a stamp or phase
decision; float(stamp) raises. Even the √2-phase histogram bins are
exact: bin(i) = isqrt(800·i²) − 20·isqrt(2·i²) = ⌊20·frac(i√2)⌋.

>>> float(Stamp(1, 1))                    # value_never_evaluated
Traceback (most recent call last):
    ...
TypeError: a Stamp's value is never evaluated (law 2)

>>> q = 10**17
>>> p = _isqrt(2 * q * q)                 # p = floor(q * sqrt(2))
>>> Stamp(p, -q) < Stamp(0, 0) < Stamp(p + 1, -q)
True

The two stamps above straddle zero by less than 1 part in 10^17 — far
below float64 resolution at that magnitude. The integer comparator
resolves them exactly.
"""
from dataclasses import dataclass
from functools import total_ordering
from math import isqrt as _isqrt

SIDE_STEP = 4          # the side ruler advances 4 per cell (probe 36)
PHASE_PERIOD = 20      # LCM of 4 and 5: the 4-against-5 re-alignment


def _sign_of(m, n):
    """Exact sign of m + n·√2. Integer arithmetic only."""
    if m == 0 and n == 0:
        return 0
    if m >= 0 and n >= 0:
        return 1
    if m <= 0 and n <= 0:
        return -1
    if m > 0:                      # n < 0: positive iff m² > 2n²
        return 1 if m * m > 2 * n * n else -1
    return 1 if 2 * n * n > m * m else -1      # m < 0, n > 0


@total_ordering
@dataclass(frozen=True)
class Stamp:
    """An exact point on the √2 ruler: m + n·√2, as integers forever."""
    m: int
    n: int

    @classmethod
    def at(cls, position):
        """The dual-ruler stamp of a linear position: side 4i, diagonal
        4√2·i — the constant baked-in differential 4(√2−1) per cell."""
        return cls(SIDE_STEP * position, SIDE_STEP * position)

    def __sub__(self, other):
        return Stamp(self.m - other.m, self.n - other.n)

    def __eq__(self, other):
        return self.m == other.m and self.n == other.n

    def __lt__(self, other):
        return _sign_of(self.m - other.m, self.n - other.n) < 0

    def __float__(self):
        raise TypeError("a Stamp's value is never evaluated (law 2)")

    def __hash__(self):
        return hash((self.m, self.n))


class PhaseRuler:
    """The periodic channel: the 3-4-5 seam's 5:4 ruler, re-aligning
    every PHASE_PERIOD positions."""

    def __init__(self, period=PHASE_PERIOD):
        self.period = period

    def phase(self, position):
        return position % self.period

    def histogram(self, events):
        hist = [0] * self.period
        for p in events:
            hist[self.phase(p)] += 1
        return hist

    def detect_cycle(self, events):
        """-> (concentration, phase). Concentration is the peak bin over
        the mean bin; a hidden cycle stands ~an order of magnitude proud
        of noise (measured 12.8x), while the aperiodic ruler's phases
        equidistribute (Weyl) and never rise far above 1x."""
        hist = self.histogram(events)
        mean = sum(hist) / self.period
        if mean == 0:
            return 0.0, None
        peak = max(hist)
        return peak / mean, hist.index(peak)


def sqrt2_phase(position, bins=PHASE_PERIOD):
    """Exact bin of frac(position·√2): ⌊bins·frac(i√2)⌋ with isqrt only."""
    i = position
    return _isqrt(bins * bins * 2 * i * i) - bins * _isqrt(2 * i * i)


def sqrt2_histogram(events, bins=PHASE_PERIOD):
    """The blindness diagnostic: the aperiodic ruler's phase histogram.
    On any periodic signal this equidistributes — if it ever 'detects' a
    cycle, the fixture is broken, not the theorem."""
    hist = [0] * bins
    for p in events:
        hist[sqrt2_phase(p, bins)] += 1
    return hist


def sqrt2_concentration(events, bins=PHASE_PERIOD):
    hist = sqrt2_histogram(events, bins)
    mean = sum(hist) / bins
    return (max(hist) / mean) if mean else 0.0
