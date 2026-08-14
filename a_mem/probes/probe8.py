"""Probe suite 8: the selector composition.

Write time: store (signature, anchor-set) pairs in a library.
Recall time: a noisy re-imprint produces a fresh signature; classify it
against the library (nearest cosine); deploy the winning anchor set at 50%;
rebuild with no signature painting at all.
Tests: classification accuracy across seeds, and end-to-end margin.
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

# library at write time: sig prototype + anchors + original, seed 42
anchors, lib_sig, orig = {}, {}, {}
for name, (pts, cx, cy) in patterns.items():
    ea = Gauge(False, seed=21, violence=0.0, decay=D)
    ea.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        ea._decay_traps("audit")
        ea._sustain()
    anchors[name] = (ea.w > 0.4)
    en = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    en.stamp(pts, cx, cy)
    for _ in range(8):
        en.beat()
    lib_sig[name] = en.sig.copy()
    orig[name] = (en.w > 0.4).astype(float)

print("=" * 66)
print("S1 · CLASSIFICATION — fresh imprints under new seeds vs library")
print("=" * 66)
seeds = [77, 101, 202, 303, 404]
correct = 0
total = 0
for sd in seeds:
    for name, (pts, cx, cy) in patterns.items():
        e = GaugeV5(seed=sd, violence=V, decay=D, decode_amp=0.0)
        e.stamp(pts, cx, cy)
        for _ in range(8):
            e.beat()
        scores = {n: cos(e.sig, lib_sig[n]) for n in names}
        pick = max(scores, key=scores.get)
        total += 1
        correct += int(pick == name)
print(f"  accuracy: {correct}/{total} = {correct / total * 100:.0f}%  (chance 33%)")

print()
print("=" * 66)
print("S2 · END-TO-END AUTONOMOUS RECALL — noisy sig -> classify ->")
print("     deploy that anchor set at 50% -> rebuild, no painting")
print("=" * 66)
builds = {}
for name, (pts, cx, cy) in patterns.items():
    # experience a noisy episode of the pattern, keep only its signature
    e = GaugeV5(seed=77, violence=V, decay=D, decode_amp=0.0)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    probe_sig = e.sig.copy()
    pick = max(names, key=lambda n: cos(probe_sig, lib_sig[n]))
    # total wipe, deploy classified anchors, rebuild
    r = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
    r.wipe()
    cells = np.argwhere(anchors[pick])
    k = max(1, len(cells) // 2)
    sel = cells[rng.choice(len(cells), size=k, replace=False)]
    for y, x in sel:
        r.a[y, x] = 10.0 / N
    r._renorm()
    for _ in range(6):
        r.beat(write_sig=False)
    builds[name] = r.w.copy()
M = np.array([[cos(builds[n1], orig[n2]) for n2 in names] for n1 in names])
diag = float(np.mean(np.diag(M)))
off = float((M.sum() - np.trace(M)) / (M.size - len(names)))
print(f"           " + "  ".join(f"{n:>6s}" for n in names))
for i, n1 in enumerate(names):
    print(f"  {n1:5s}   " + "  ".join(f"{M[i, j]:6.3f}" for j in range(len(names))))
print(f"  margin: {diag - off:+.3f}   (anchors-with-known-identity benchmark: +0.730)")
