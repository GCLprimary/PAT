"""The clock: page-turn and dwell control for serial recall.

Design law 2: page-turn is mandatory for every tenant change. Hot eviction
is impossible (measured 6/6 failures) — the incumbent squats until the
stage is flattened. A page-turn returns activation to the gauge's nothing,
zeroes the traps, and clears every collected core code.

Dwell policies (D-4: level-v1 remains the default; the two candidates are
scaffolding behind a flag, promoted only if the benchmark shows accuracy
>= level AND strictly lower mean dwell):

  FixedDwell(n)       — n beats per tenant, unconditionally.
  AdaptiveDwell       — level v1: beat until confidence >= theta or cap.
  CalibratedDwell     — candidate: threshold self-tunes to a quantile of
                        the collected beat-1 completion distribution;
                        falls back to level before min_samples.
  DeltaDwell          — candidate: turn early at beat 2 iff (c2 - c1) is
                        below a floor AND c1 above a floor (fast
                        crystallization), else level fallback.
                        (Probe 14 killed the naive c1-slope fast-exit;
                        this is the D-4 replacement shape, not that.)

run_dwell returns (beats_used, trajectory) — the trajectory is the
confidence after each beat, feeding the runtime calibration buffer (W-3).
"""
from dataclasses import dataclass

import numpy as np

from . import constants as K


def page_turn(engine):
    """Flatten the stage for a new tenant: activation -> the gauge's
    nothing, traps -> 0, hop ages -> 0, all core codes -> 0."""
    engine.wipe()
    engine.clear_codes()


@dataclass(frozen=True)
class FixedDwell:
    beats: int = K.DWELL_DEFAULT


@dataclass(frozen=True)
class AdaptiveDwell:
    """Level v1: the shipped default."""
    theta: float = K.ADAPTIVE_THETA
    cap: int = K.ADAPTIVE_CAP


@dataclass(frozen=True)
class CalibratedDwell:
    """Candidate: threshold = quantile of collected c1 samples."""
    quantile: float = K.CLOCK_QUANTILE
    min_samples: int = K.CLOCK_MIN_SAMPLES
    theta: float = K.ADAPTIVE_THETA          # level fallback until tuned
    cap: int = K.ADAPTIVE_CAP

    def threshold(self, c1_samples):
        if c1_samples is not None and len(c1_samples) >= self.min_samples:
            return float(np.quantile(np.asarray(c1_samples), self.quantile))
        return self.theta


@dataclass(frozen=True)
class DeltaDwell:
    """Candidate: fast-crystallization early turn at beat 2."""
    delta_floor: float = K.CLOCK_DELTA_FLOOR
    c1_floor: float = K.CLOCK_C1_FLOOR
    theta: float = K.ADAPTIVE_THETA
    cap: int = K.ADAPTIVE_CAP


def run_dwell(engine, anchor_mask, policy, write_sig=False, c1_samples=None):
    """Run one tenant's dwell on the stage.

    Returns (beats_used, trajectory) where trajectory[i] is the anchor-
    completion confidence after beat i+1.
    """
    if isinstance(policy, int):
        policy = FixedDwell(policy)

    trajectory = []

    def step():
        engine.beat(write_sig=write_sig)
        c = engine.confidence(anchor_mask)
        trajectory.append(c)
        return c

    if isinstance(policy, FixedDwell):
        for _ in range(policy.beats):
            step()
        return policy.beats, trajectory

    if isinstance(policy, AdaptiveDwell):
        for b in range(1, policy.cap + 1):
            if step() >= policy.theta:
                break
        return b, trajectory

    if isinstance(policy, CalibratedDwell):
        theta = policy.threshold(c1_samples)
        for b in range(1, policy.cap + 1):
            if step() >= theta:
                break
        return b, trajectory

    if isinstance(policy, DeltaDwell):
        for b in range(1, policy.cap + 1):
            c = step()
            if c >= policy.theta:
                break
            if b == 2:
                c1, c2 = trajectory[0], trajectory[1]
                if (c2 - c1) < policy.delta_floor and c1 > policy.c1_floor:
                    break
        return b, trajectory

    raise TypeError(f"unknown dwell policy: {policy!r}")
