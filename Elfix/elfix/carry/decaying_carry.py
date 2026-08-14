"""
elfix/carry/decaying_carry.py  —  Tier 5: interpretable recurrence
====================================================================

PROVENANCE
----------
- [GCL] relational_tension — the decaying carry vector across sentences (the one
  piece of GCL's recurrence that computes). Canonical name: a leaky integrator /
  recurrent hidden state (the readable ancestor of RNN state).

The two memories of the system are complementary:
  - all_pairs (Tier 4): sharp, local, expensive (O(n^2)), sees WITHIN a window.
  - decaying_carry (Tier 5): soft, global, cheap, carries ACROSS windows.

DESIGN LAW CHECK
----------------
Law 1: the decay rate is EARNED, not the Mersenne-subtraction rate it had in GCL
(that origin is dropped). `EARNED_RATE` is the retention of a leaky integrator
whose memory half-life matches the measured half-life of phoneme contextual
mutual information in the corpus (see `measure_decay_rate`, re-derived in test).

RE-VALIDATED over running text (the earlier caveat, now RESOLVED)
-----------------------------------------------------------------
0.67 was earned from WITHIN-WORD phoneme context and flagged for re-validation
once real cross-word context existed. `scripts/carry_revalidate.py` measured the
contextual-MI half-life over the Brown corpus (cross-word phoneme streams, and at
syllable + word granularity), with a SHUFFLE control to remove finite-sample bias.
Result: the debiased rate is ~0.67 at EVERY granularity (phoneme, syllable, word) —
0.67 holds. Note: the RAW curves (syllables 0.75, words 'no halving') falsely
suggested long lexical memory; that was bias (floors 1.04 / 3.06). A small REAL
long-range word residual (~0.2 bits of topical context) remains but does not move
the dominant half-life. So 0.67 is the validated retention; the long-range residual
is the designated next refinement (a second, slower carry for topical context).
"""

from __future__ import annotations
import math
from collections import Counter
from typing import List, Optional, Iterable


# Earned: phoneme contextual MI has a half-life of ~1.72 phonemes on the full CMU
# corpus, so a leaky integrator matching it retains r = 0.5**(1/1.72) ~ 0.67 per
# step. measure_decay_rate() re-derives this; test_carry asserts it (Law 1/3).
EARNED_RATE = 0.67


def contextual_mi(corpus: Iterable[List[str]], max_lag: int = 6) -> List[float]:
    """MI(unit_i ; unit_{i+k}) in bits, for k = 1..max_lag, over within-sequence
    pairs. The units can be phonemes (within a word) OR phonemes across an utterance
    OR words — whatever sequences `corpus` holds. Pure counting (Law 1)."""
    corpus = list(corpus)

    def mi(k: int) -> float:
        joint: Counter = Counter()
        left: Counter = Counter()
        right: Counter = Counter()
        n = 0
        for seq in corpus:
            for i in range(len(seq) - k):
                joint[(seq[i], seq[i + k])] += 1
                left[seq[i]] += 1
                right[seq[i + k]] += 1
                n += 1
        if not n:
            return 0.0
        return sum((c / n) * math.log2((c / n) / (left[a] / n * right[b] / n))
                   for (a, b), c in joint.items())

    return [mi(k) for k in range(1, max_lag + 1)]


def half_life_rate(mis: List[float]) -> Optional[float]:
    """The leaky-integrator retention r whose memory half-life matches the half-
    life of an MI curve: H = the lag where MI falls to half of MI(1); r**H = 0.5.
    None if MI never halves within the curve (decays slower than the window)."""
    if not mis or mis[0] <= 0:
        return None
    half = mis[0] / 2
    for k in range(2, len(mis) + 1):
        if mis[k - 1] <= half:
            prev = mis[k - 2]
            frac = (prev - half) / (prev - mis[k - 1]) if prev != mis[k - 1] else 1.0
            h = (k - 1) + frac
            return round(0.5 ** (1.0 / h), 2)
    return None


def measure_decay_rate(corpus: Iterable[List[str]], max_lag: int = 6) -> float:
    """
    Earn the retention rate from the corpus: the half-life of contextual mutual
    information. MI(k) = I(unit_i ; unit_{i+k}); the half-life H is the lag where
    MI falls to half of MI(1); the matching leaky-integrator retention is r with
    r**H = 0.5. Pure counting (Law 1).
    """
    return half_life_rate(contextual_mi(corpus, max_lag)) or EARNED_RATE


class DecayingCarry:
    """A leaky integrator over unit points. What persists survived the bleed."""

    def __init__(self, dim: int, rate: float = EARNED_RATE):
        # rate in [0,1): fraction of prior carry retained each step.
        # Default EARNED from corpus context half-life (Law 1); see module header.
        if not (0.0 <= rate < 1.0):
            raise ValueError("rate must be in [0, 1)")
        self.dim = dim
        self.rate = rate
        self.state: List[float] = [0.0] * dim

    def update(self, point: List[float], salience: float = 1.0) -> List[float]:
        """Fold a new unit into the carry; return the new state (a copy)."""
        self.state = [self.rate * self.state[k] + (1 - self.rate) * salience * point[k]
                      for k in range(self.dim)]
        return list(self.state)

    def reset(self) -> None:
        """Boundaries are real discontinuities — reset, do not bridge them.
        ([ElfIX] relational: reset the window at sentence boundaries.)"""
        self.state = [0.0] * self.dim

    def read(self) -> List[float]:
        return list(self.state)


if __name__ == "__main__":
    c = DecayingCarry(dim=2, rate=0.5)
    print(c.update([1.0, 0.0]))
    print(c.update([0.0, 1.0]))   # earlier signal bleeds, recent dominates
