"""W-3 clock benchmark (not a test): candidate dwell policies vs level-v1.

Three canonical pairs x seeds 5-10, page-turned alternation, 10 turns
each. A candidate is promoted to default ONLY if accuracy >= level-v1
AND mean dwell strictly lower. (Probe 14 already killed the naive
c1-slope fast-exit; the delta policy here is the D-4 replacement shape.)

Run from a fresh checkout:  python examples/benchmark_clock.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from amem import AdaptiveDwell, CalibratedDwell, DeltaDwell, Memory
from amem import constants as K

PAIRS = {
    "easy (sep 12)": ((3, 3), (15, 14)),
    "mid  (sep 5) ": ((4, 4), (9, 9)),
    "hard (sep 3) ": ((5, 5), (8, 8)),
}
SEEDS = range(5, 11)
TURNS = 10
WARMUP_TURNS = 12

POLICIES = {
    "level-v1": AdaptiveDwell(),
    "calibrated": CalibratedDwell(min_samples=WARMUP_TURNS),
    "delta": DeltaDwell(),
}


def run(pair, policy, seed):
    (ax, ay), (bx, by) = pair
    mem = Memory(seed=seed, path=None)
    a = mem.write([(ax + dx, ay + dy) for dx, dy in K.SEED_CONSTELLATION])
    b = mem.write([(bx + dx, by + dy) for dx, dy in K.SEED_CONSTELLATION])
    order = [a, b] * (WARMUP_TURNS // 2)
    mem.sequence(order, dwell=policy)          # fill the calibration buffer
    results = mem.sequence([a, b] * (TURNS // 2), dwell=policy)
    acc = np.mean([r.identity == r.target for r in results])
    dwell = np.mean([r.dwell for r in results])
    return acc, dwell


def main():
    t0 = time.time()
    print("pair            " + "".join(f"{n:>22s}" for n in POLICIES))
    totals = {n: [0.0, 0.0] for n in POLICIES}
    for pname, pair in PAIRS.items():
        row = f"{pname}  "
        for pol_name, policy in POLICIES.items():
            accs, dws = zip(*(run(pair, policy, s) for s in SEEDS))
            acc, dw = float(np.mean(accs)), float(np.mean(dws))
            totals[pol_name][0] += acc
            totals[pol_name][1] += dw
            row += f"    {acc * 100:4.0f}% d={dw:.2f}    "
        print(row)
    print("mean            " + "".join(
        f"    {totals[n][0] / 3 * 100:4.0f}% d={totals[n][1] / 3:.2f}    "
        for n in POLICIES))

    lvl_acc, lvl_dw = totals["level-v1"][0] / 3, totals["level-v1"][1] / 3
    print("\npromotion check (accuracy >= level AND mean dwell strictly lower):")
    for name in ("calibrated", "delta"):
        acc, dw = totals[name][0] / 3, totals[name][1] / 3
        verdict = "PROMOTE" if (acc >= lvl_acc and dw < lvl_dw) else "keep level-v1"
        print(f"  {name:10s} acc {acc * 100:.0f}% vs {lvl_acc * 100:.0f}%, "
              f"dwell {dw:.2f} vs {lvl_dw:.2f}  ->  {verdict}")
    print(f"\ndone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
