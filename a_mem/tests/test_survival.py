"""Probe 1 / P1: aligned constellations survive quiet dynamics; random
bursts die. Baseline: aligned 100% of trials at full mass, random ~20%."""
import numpy as np

from amem import AbsoluteField
from amem import constants as K
from conftest import SEED_OFF, D

TRIALS = 60
TICKS = 250


def test_aligned_vs_random_survival():
    aligned, random_ = [], []
    for t in range(TRIALS):
        ea = AbsoluteField(seed=1000 + t, violence=0.0, decay=D)
        cx = 3 + int(ea.rng.integers(0, K.GRID - 11))
        cy = 3 + int(ea.rng.integers(0, K.GRID - 11))
        ea.stamp([(cx + dx, cy + dy) for dx, dy in SEED_OFF], w0=0.0)
        ea.quiet_ticks(TICKS)
        aligned.append(ea.act_mass())

        er = AbsoluteField(seed=5000 + t, violence=0.0, decay=D)
        xs = er.rng.integers(0, K.GRID, 7)
        ys = er.rng.integers(0, K.GRID, 7)
        for x, y in zip(xs, ys):
            er.a[y, x] = 1.0
        er.quiet_ticks(TICKS)
        random_.append(er.act_mass())

    aligned = np.array(aligned)
    random_ = np.array(random_)
    surv_al = float((aligned > 0.5).mean())
    surv_rn = float((random_ > 0.5).mean())

    # baseline 100% (slack: >= 90%)
    assert surv_al >= 0.9, f"aligned survival {surv_al:.2f} < 0.9"
    # baseline ~20% (slack: <= 45%)
    assert surv_rn <= 0.45, f"random survival {surv_rn:.2f} > 0.45"
    # the alignment advantage itself
    assert surv_al - surv_rn >= 0.4

    # aligned constellations survive at (near) full mass, not as embers
    assert float(aligned.mean()) >= 6.0, f"aligned mean mass {aligned.mean():.2f}"
