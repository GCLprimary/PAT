"""Probe suite 5: the two machines as a sequence.

Stage 1 (ABSOLUTE): imprint pattern, quiet dynamics only -> durable exact
  survivors (the anchor store).
Stage 2 (NORMALIZED): imprint same pattern with full strokes -> signature.
Recall on the normalized machine after wipe, four conditions:
  A: frozen signature only                      (known: margin ~ -0.05)
  B: 50% random subset of absolute survivors as activation cue, no signature
  C: matched half-anchors + frozen signature    (the sequence)
  D: half-anchors from pattern i + signature from pattern j != i (control)
Metrics: cosine confusion vs originals; completion = fraction of original
  defined cells re-defined after rebuild.
"""
import numpy as np
from gauge import Gauge, GRID, N, SEED

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(7)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

patterns = {
    "NW": (SEED, 3, 3),
    "SE": (SEED, 15, 14),
    "line": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
names = list(patterns)
V, D = 0.45, 0.05

# ── Stage 1: absolute anchor store (quiet dynamics, no strokes) ──
anchors = {}
for name, (pts, cx, cy) in patterns.items():
    e = Gauge(False, seed=21, violence=0.0, decay=D)
    e.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        e._decay_traps("audit")
        e._sustain()
    anchors[name] = (e.w > 0.4)
print("absolute anchor store (quiet dynamics, 80 ticks):")
for n in names:
    print(f"  {n:5s} survivors: {int(anchors[n].sum())}")

# ── Stage 2: normalized imprint -> signature + original ──
sigs, orig = {}, {}
for name, (pts, cx, cy) in patterns.items():
    e = Gauge(True, seed=42, violence=V, decay=D)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    sigs[name] = e.sig.copy()
    orig[name] = (e.w > 0.4).astype(float)

def recall(anchor_name=None, sig_name=None, frac=0.5, seed=5):
    e = Gauge(True, seed=seed, violence=V, decay=D)
    e.wipe()
    if sig_name is not None:
        e.sig = sigs[sig_name].copy()
    if anchor_name is not None:
        cells = np.argwhere(anchors[anchor_name])
        k = max(1, int(len(cells) * frac))
        pick = cells[rng.choice(len(cells), size=k, replace=False)]
        for y, x in pick:
            e.a[y, x] = 10.0 / N
        e._renorm()
    for _ in range(6):
        e.beat(write_sig=False)
    return e.w.copy()

def report(title, builds):
    M = np.array([[cos(builds[n1], orig[n2]) for n2 in names] for n1 in names])
    diag = float(np.mean(np.diag(M)))
    off = float((M.sum() - np.trace(M)) / (M.size - len(names)))
    comp = [float((builds[n] > 0.4)[orig[n] > 0].mean()) if orig[n].sum() else 0.0
            for n in names]
    print(f"\n{title}")
    print(f"           " + "  ".join(f"{n:>6s}" for n in names) + "    completion")
    for i, n1 in enumerate(names):
        print(f"  {n1:5s}   " + "  ".join(f"{M[i, j]:6.3f}" for j in range(len(names)))
              + f"    {comp[i]:.2f}")
    print(f"  margin: {diag - off:+.3f}")
    return diag - off

print()
print("=" * 66)
print("RECALL CONDITIONS (normalized machine, wipe = flatten, rebuild 6)")
print("=" * 66)
mA = report("A · signature only",
            {n: recall(None, n) for n in names})
mB = report("B · half-anchors only (50% random subset, no signature)",
            {n: recall(n, None) for n in names})
mC = report("C · matched half-anchors + signature (the sequence)",
            {n: recall(n, n) for n in names})
# mismatched: anchors from row pattern, signature from the NEXT pattern
mis = {n: recall(n, names[(i + 1) % len(names)]) for i, n in enumerate(names)}
mD = report("D · MISMATCHED half-anchors + wrong signature (control)", mis)

print()
print("=" * 66)
print("E · SPARSER CUE — completion vs anchor fraction (matched, with sig)")
print("=" * 66)
print("frac   margin   mean completion")
for frac in (0.15, 0.30, 0.50, 0.75):
    builds = {n: recall(n, n, frac=frac, seed=13) for n in names}
    M = np.array([[cos(builds[n1], orig[n2]) for n2 in names] for n1 in names])
    diag = float(np.mean(np.diag(M)))
    off = float((M.sum() - np.trace(M)) / (M.size - len(names)))
    comp = np.mean([float((builds[n] > 0.4)[orig[n] > 0].mean()) for n in names])
    print(f"{frac:.2f}   {diag - off:+.3f}   {comp:.2f}")

print()
print(f"summary margins  A:{mA:+.3f}  B:{mB:+.3f}  C:{mC:+.3f}  D(mismatch):{mD:+.3f}")
