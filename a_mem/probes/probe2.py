"""Probe suite 2: phase diagram, then memory test in the structured regime.

Suite 1 exposed a confound: at default (violence .45, decay .05) the field
saturates -- every 'original' is the same full grid, so cosine 0.998 across
the board measures the flood, not memory. Find subcritical settings first.
"""
import numpy as np
from engine import Engine, GRID, SEED, TRAP_T

np.set_printoptions(precision=3, suppress=True)

print("=" * 70)
print("P5 · PHASE DIAGRAM — defined fraction after 10 beats, one aligned seed")
print("     rows: violence | cols: decay")
print("=" * 70)
viols = [0.10, 0.20, 0.30, 0.45, 0.60]
decays = [0.03, 0.05, 0.07, 0.09, 0.11]
frac = np.zeros((len(viols), len(decays)))
for i, v in enumerate(viols):
    for j, d in enumerate(decays):
        e = Engine(seed=11, violence=v, decay=d)
        e.stamp(SEED, 8, 8)
        for _ in range(10):
            e.beat()
        frac[i, j] = e.defined_count() / (GRID * GRID)
print("           " + "  ".join(f"d={d:.2f}" for d in decays))
for i, v in enumerate(viols):
    print(f"  v={v:.2f}   " + "  ".join(f"{frac[i, j]:6.3f}" for j in range(len(decays))))
print("\n  0.000 = dead (seed lost) | ~1.0 = flood | between = structured regime")

# pick a structured setting automatically: closest to fraction 0.25
best = None
for i, v in enumerate(viols):
    for j, d in enumerate(decays):
        if best is None or abs(frac[i, j] - 0.25) < abs(best[2] - 0.25):
            best = (v, d, frac[i, j])
V, D, F = best
print(f"\n  chosen structured setting: violence={V}, decay={D} (fraction {F:.3f})")

print()
print("=" * 70)
print(f"P6 · MEMORY IN THE STRUCTURED REGIME (violence={V}, decay={D})")
print("     same protocol as P3: imprint 8 beats -> wipe -> frozen-sig rebuild")
print("=" * 70)
patterns = {
    "NW-constellation": (SEED, 3, 3),
    "SE-constellation": (SEED, 15, 14),
    "NE-line": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

sigs, originals, rebuilt = {}, {}, {}
for name, (pts, cx, cy) in patterns.items():
    ep = Engine(seed=42, violence=V, decay=D)
    ep.stamp(pts, cx, cy)
    for _ in range(8):
        ep.beat()
    sigs[name] = ep.sig.copy()
    originals[name] = (ep.w > TRAP_T).astype(float)
    ep.clear_field()
    for _ in range(6):
        ep.beat(write_sig=False)
    rebuilt[name] = ep.w.copy()

names = list(patterns)
print(f"\noriginal defined counts: " +
      ", ".join(f"{n}: {int(originals[n].sum())}" for n in names))
print("\nsignature vectors (normalized to own max):")
for n in names:
    s = sigs[n] / max(sigs[n].max(), 1e-9)
    print(f"  {n:18s} {s}")
print("\nsignature pairwise cosine (identity would be diag 1, off-diag low):")
for n1 in names:
    row = "  ".join(f"{cos(sigs[n1], sigs[n2]):.3f}" for n2 in names)
    print(f"  {n1:18s} {row}")
print("\nrebuilt-vs-original trap-map cosine:")
header = "  ".join(f"{n[:10]:>10s}" for n in names)
print(f"  {'':18s} {header}")
for n1 in names:
    vals = [cos(rebuilt[n1], originals[n2]) for n2 in names]
    print(f"  {n1:18s} " + "  ".join(f"{v:10.3f}" for v in vals))
print("\nrebuilt mass (w sum): " +
      ", ".join(f"{n}: {rebuilt[n].sum():.2f}" for n in names))

print()
print("=" * 70)
print("P7 · WHAT DOES THE SIGNATURE ACTUALLY ENCODE?")
print("     imprint a single point at angle theta, radius 6; 4 beats;")
print("     report which core cells the distillate lands in")
print("=" * 70)
import math
CC = GRID // 2
for deg in [0, 45, 90, 135, 180, 225, 270, 315]:
    th = math.radians(deg)
    x = CC + int(round(6 * math.cos(th)))
    y = CC + int(round(6 * math.sin(th)))
    ep = Engine(seed=5, violence=0.0, decay=0.02)  # no spray: pure indraw physics
    ep.a[y, x] = 1.0
    ep.w[y, x] = 0.8
    for _ in range(4):
        ep.beat(do_outpour=False)
    s = ep.sig.reshape(3, 3)
    s = s / max(s.max(), 1e-9)
    top = np.unravel_index(np.argmax(s), s.shape)
    print(f"  source at {deg:3d}°  ->  core heatmap rows {np.round(s, 2).tolist()}  peak cell (row,col)={top}")
