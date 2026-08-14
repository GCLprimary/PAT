"""Probe suite 6: v5 composition acceptance tests.

T1: decode-amp sweep -- signature-alone recall with the inverse-spiral
    decoder (old blob decoder scored margin -0.050).
T2: THE acceptance test -- matched half-anchors + decoded signature (C)
    vs half-anchors alone (B, benchmark +0.653), at each decode amp.
T3: sparse-anchor rescue -- at anchor fractions 0.10/0.20/0.35, does the
    decoded gist help where cues are too thin to complete alone?
"""
import numpy as np
from gauge import Gauge, GRID, N, SEED
from gauge5 import GaugeV5

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

# anchor store (absolute machine, quiet dynamics)
anchors = {}
for name, (pts, cx, cy) in patterns.items():
    e = Gauge(False, seed=21, violence=0.0, decay=D)
    e.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        e._decay_traps("audit")
        e._sustain()
    anchors[name] = (e.w > 0.4)

# normalized imprint -> signatures + originals (v5 engine for imprint too)
sigs, orig = {}, {}
for name, (pts, cx, cy) in patterns.items():
    e = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    sigs[name] = e.sig.copy()
    orig[name] = (e.w > 0.4).astype(float)

def recall(anchor_name, sig_name, decode_amp, frac=0.5, seed=5):
    e = GaugeV5(seed=seed, violence=V, decay=D, decode_amp=decode_amp)
    e.wipe()
    if sig_name is not None:
        e.sig = sigs[sig_name].copy()
    if anchor_name is not None:
        cells = np.argwhere(anchors[anchor_name])
        k = max(1, int(round(len(cells) * frac)))
        pick = cells[rng.choice(len(cells), size=k, replace=False)]
        for y, x in pick:
            e.a[y, x] = 10.0 / N
        e._renorm()
    for _ in range(6):
        e.beat(write_sig=False)
    return e.w.copy()

def margin(builds):
    M = np.array([[cos(builds[n1], orig[n2]) for n2 in names] for n1 in names])
    diag = float(np.mean(np.diag(M)))
    off = float((M.sum() - np.trace(M)) / (M.size - len(names)))
    return diag - off, M

print("=" * 66)
print("T1 · DECODED SIGNATURE ALONE — margin vs decode amp")
print("     (blob decoder scored -0.050)")
print("=" * 66)
for amp in (0.02, 0.06, 0.12, 0.25):
    m, _ = margin({n: recall(None, n, amp) for n in names})
    print(f"  amp={amp:.2f}   margin {m:+.3f}")

print()
print("=" * 66)
print("T2 · ACCEPTANCE — matched half-anchors + decoded sig vs B=+0.653")
print("=" * 66)
mB, MB = margin({n: recall(n, None, 0.0) for n in names})
print(f"  B  (anchors alone, this run):        {mB:+.3f}")
best = None
for amp in (0.0, 0.02, 0.06, 0.12, 0.25):
    m, M = margin({n: recall(n, n, amp, seed=6) for n in names})
    flag = "  <-- C > B" if m > mB else ""
    print(f"  C  amp={amp:.2f}:                        {m:+.3f}{flag}")
    if best is None or m > best[1]:
        best = (amp, m, M)
amp_star, mC, MC = best
print(f"\n  best C at amp={amp_star}: {mC:+.3f}   (acceptance: {'PASS' if mC > mB else 'FAIL'})")
print("  best-C confusion matrix:")
print(f"           " + "  ".join(f"{n:>6s}" for n in names))
for i, n1 in enumerate(names):
    print(f"  {n1:5s}   " + "  ".join(f"{MC[i, j]:6.3f}" for j in range(len(names))))

print()
print("=" * 66)
print("T3 · SPARSE-ANCHOR RESCUE — margin at thin cue fractions")
print("=" * 66)
print("frac    no sig    decoded sig (best amp)   rescue")
for frac in (0.10, 0.20, 0.35):
    m0, _ = margin({n: recall(n, None, 0.0, frac=frac, seed=17) for n in names})
    m1, _ = margin({n: recall(n, n, amp_star, frac=frac, seed=17) for n in names})
    print(f"{frac:.2f}    {m0:+.3f}    {m1:+.3f}                  {m1 - m0:+.3f}")
