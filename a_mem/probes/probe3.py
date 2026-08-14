"""Probe suite 3: why the zero point goes hungry or blind.

P8: journey accounting -- place unit mass at every cell one at a time,
    run pure indraw physics (no spray), and classify the fate:
    ARRIVES at core / STRANDS at a parity dead-end / decays en route.
P9: supercritical signature uniformity -- how flat is the stored code
    after N beats of flood? (coefficient of variation of the 8 live cells)
"""
import numpy as np
from engine import Engine, GRID, C, SEED

np.set_printoptions(precision=3, suppress=True)

print("=" * 70)
print("P8 · JOURNEY MAP — fate of unit mass at each start cell (pure indraw)")
print("=" * 70)
# follow the deterministic contraction map cell-by-cell (no dynamics):
# a point survives a step iff parity-ok; classify pure-geometry fate.
fate = np.zeros((GRID, GRID), dtype=int)  # 0 center, 1 arrives, 2 strands
for y in range(GRID):
    for x in range(GRID):
        rx, ry = x - C, y - C
        if rx == 0 and ry == 0:
            fate[y, x] = 0
            continue
        steps = 0
        while True:
            if abs(rx) <= 1 and abs(ry) <= 1:
                fate[y, x] = 1  # inside core capture zone
                break
            if (rx + ry) % 2 != 0:
                fate[y, x] = 2  # parity dead-end before reaching core
                break
            rx, ry = (rx + ry) // 2, (ry - rx) // 2
            steps += 1
arrive = int((fate == 1).sum())
strand = int((fate == 2).sum())
print(f"cells whose geometry can reach the core:   {arrive} / {GRID * GRID - 1}  ({arrive / (GRID * GRID - 1) * 100:.1f}%)")
print(f"cells that strand at a parity dead-end:    {strand} / {GRID * GRID - 1}  ({strand / (GRID * GRID - 1) * 100:.1f}%)")
print("\nreachability map (.=arrives  x=strands  O=core):")
for y in range(GRID):
    row = ""
    for x in range(GRID):
        if abs(x - C) <= 1 and abs(y - C) <= 1:
            row += "O"
        else:
            row += "." if fate[y, x] == 1 else "x"
    print("  " + row)

print()
print("=" * 70)
print("P9 · SUPERCRITICAL SIGNATURE — how flat is the flood's memory?")
print("=" * 70)
e = Engine(seed=3, violence=0.45, decay=0.05)
e.stamp(SEED, 4, 4)
for _ in range(12):
    e.beat()
live = np.delete(e.sig, 4)  # drop the structurally-dark center
cv = live.std() / live.mean()
print(f"signature after 12 flood beats: {np.round(e.sig, 1)}")
print(f"live-cell coefficient of variation: {cv:.4f}")
print(f"(0 = perfectly uniform = zero retrievable information)")

print()
print("=" * 70)
print("P10 · TIMING — does distillate outlive the trip at subcritical decay?")
print("      unit mass at a reachable cell r=8; pure physics, decay=0.11")
print("=" * 70)
# reachable r=8 cell: need full even-parity orbit; search one
start = None
for y in range(GRID):
    for x in range(GRID):
        if fate[y, x] == 1 and max(abs(x - C), abs(y - C)) >= 7:
            start = (x, y)
            break
    if start:
        break
x0, y0 = start
ep = Engine(seed=6, violence=0.0, decay=0.11)
ep.a[y0, x0] = 1.0
ep.w[y0, x0] = 0.8
for b in range(4):
    ep.beat(do_outpour=False)
    print(f"  after beat {b + 1}: field mass={ep.act_mass():7.4f}   sig sum={ep.sig.sum():7.4f}")
print(f"\n  start cell ({x0},{y0}), Chebyshev radius {max(abs(x0 - C), abs(y0 - C))}")
