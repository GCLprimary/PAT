"""Probe suite 10: the stage as a clock -- serial recall.

Schedule: cue A -> beats -> cue B -> beats -> cue C -> beats -> cue A.
S1: hot swap (no clearing; the new cue must evict the resident).
S2: page-turn (flatten the stage before each new cue; clean baseline).
Per beat: which identity holds the stage, and how purely.
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
    "A": (SEED, 3, 3),
    "B": (SEED, 15, 14),
    "C": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
names = list(patterns)
V, D = 0.45, 0.05

lib = {}
for name, (pts, cx, cy) in patterns.items():
    ea = Gauge(False, seed=21, violence=0.0, decay=D)
    ea.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        ea._decay_traps("audit")
        ea._sustain()
    en = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    en.stamp(pts, cx, cy)
    for _ in range(8):
        en.beat()
    lib[name] = dict(anchors=(ea.w > 0.4), orig=(en.w > 0.4).astype(float))

def cue(e, name):
    cells = np.argwhere(lib[name]["anchors"])
    sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
    for y, x in sel:
        e.a[y, x] += 10.0 / N
    e._renorm()

def stage_report(e):
    scores = {n: cos(e.w, lib[n]["orig"]) for n in names}
    top = max(scores, key=scores.get)
    second = max(v for n, v in scores.items() if n != top)
    return top, scores[top] - second, scores

SCHEDULE = ["A", "B", "C", "A"]
BEATS = 4

for mode in ("S1 hot swap", "S2 page-turn"):
    print("=" * 68)
    print(f"{mode} — schedule A -> B -> C -> A, {BEATS} beats each")
    print("=" * 68)
    e = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
    e.wipe()
    print("cued  beat   stage-holder   purity   (residue of previous tenant)")
    prev = None
    for step, name in enumerate(SCHEDULE):
        if mode.startswith("S2"):
            e.wipe()
        cue(e, name)
        for b in range(BEATS):
            e.beat(write_sig=False)
            top, purity, scores = stage_report(e)
            res = f"   prev {prev}: {scores[prev]:.2f}" if prev and prev != name else ""
            mark = "" if top == name else "   <-- WRONG TENANT"
            print(f"  {name}    {b + 1}      {top}            {purity:+.3f}{res}{mark}")
        prev = name
    print()

print("=" * 68)
print("S3 · SWAP LATENCY — beats until the new tenant holds the stage")
print("     (hot swap, averaged over 6 random A->B pairs and seeds)")
print("=" * 68)
lat = []
fails = 0
for trial in range(6):
    a, b = rng.choice(names, size=2, replace=False)
    e = GaugeV5(seed=100 + trial, violence=V, decay=D, decode_amp=0.0)
    e.wipe()
    cue(e, a)
    for _ in range(4):
        e.beat(write_sig=False)
    cue(e, b)
    got = None
    for t in range(1, 7):
        e.beat(write_sig=False)
        top, _, _ = stage_report(e)
        if top == b:
            got = t
            break
    if got is None:
        fails += 1
    else:
        lat.append(got)
if lat:
    print(f"  mean latency: {np.mean(lat):.1f} beats   (n={len(lat)}, failures: {fails}/6)")
else:
    print(f"  eviction failed in all {fails}/6 trials")
