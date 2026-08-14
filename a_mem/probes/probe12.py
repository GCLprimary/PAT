"""Probe suite 12: the clock -- how fast, and how to fail slow.

D1: frontier -- pairs at decreasing separation, fixed dwell 1-4,
    per-beat correctness and purity.
D2: internal confidence -- completion fraction of the deployed anchor
    set (machine-readable); validity = correlation with true purity.
D3: adaptive controller -- dwell until confidence >= theta or cap, then
    page-turn; compare accuracy and mean dwell against fixed clocks.
"""
import numpy as np
from gauge import Gauge, GRID, N, SEED
from gauge5 import GaugeV5

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(7)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

V, D = 0.45, 0.05

PAIRS = {
    "sep~12": ((3, 3), (15, 14)),
    "sep~8 ": ((3, 3), (11, 11)),
    "sep~5 ": ((4, 4), (9, 9)),
    "sep~3 ": ((5, 5), (8, 8)),
}

def build_identity(cx, cy):
    ea = Gauge(False, seed=21, violence=0.0, decay=D)
    ea.stamp(SEED, cx, cy, w0=0.0)
    for _ in range(80):
        ea._decay_traps("audit")
        ea._sustain()
    en = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    en.stamp(SEED, cx, cy)
    for _ in range(8):
        en.beat()
    return dict(anchors=(ea.w > 0.4), orig=(en.w > 0.4).astype(float))

libs = {}
for pname, (p1, p2) in PAIRS.items():
    A = build_identity(*p1)
    B = build_identity(*p2)
    libs[pname] = {"A": A, "B": B,
                   "overlap": cos(A["orig"], B["orig"])}

def deploy(e, ident):
    cells = np.argwhere(ident["anchors"])
    sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
    for y, x in sel:
        e.a[y, x] += 10.0 / N
    e._renorm()

def judge(e, lib, target):
    own = cos(e.w, lib[target]["orig"])
    other = cos(e.w, lib["B" if target == "A" else "A"]["orig"])
    return (own > other), own - other

def confidence(e, ident):
    mask = ident["anchors"]
    return float((e.w > 0.4)[mask].mean()) if mask.sum() else 0.0

print("pair     orig-overlap (confusability)")
for pname in PAIRS:
    print(f"{pname}   {libs[pname]['overlap']:.3f}")

print()
print("=" * 68)
print("D1 · FRONTIER — fixed dwell, 10 tenant-turns, judged on last beat")
print("=" * 68)
print("pair      dwell=1        dwell=2        dwell=3        dwell=4")
frontier = {}
for pname, lib in libs.items():
    row = []
    for p in (1, 2, 3, 4):
        e = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
        ok = 0
        purs = []
        for t in range(10):
            target = ["A", "B"][t % 2]
            e.wipe()
            deploy(e, lib[target])
            for _ in range(p):
                e.beat(write_sig=False)
            c, pur = judge(e, lib, target)
            ok += int(c)
            purs.append(pur)
        row.append((ok / 10, float(np.mean(purs))))
    frontier[pname] = row
    print(f"{pname}   " + "   ".join(f"{a * 100:3.0f}% {m:+.2f}" for a, m in row))

print()
print("=" * 68)
print("D2 · INTERNAL CONFIDENCE VALIDITY — completion vs true purity")
print("=" * 68)
xs, ys = [], []
for pname, lib in libs.items():
    e = GaugeV5(seed=9, violence=V, decay=D, decode_amp=0.0)
    for t in range(8):
        target = ["A", "B"][t % 2]
        e.wipe()
        deploy(e, lib[target])
        for b in range(3):
            e.beat(write_sig=False)
            xs.append(confidence(e, lib[target]))
            _, pur = judge(e, lib, target)
            ys.append(pur)
xs, ys = np.array(xs), np.array(ys)
r = float(np.corrcoef(xs, ys)[0, 1])
print(f"  samples: {len(xs)}   pearson r(confidence, purity) = {r:+.3f}")

print()
print("=" * 68)
print("D3 · ADAPTIVE CONTROLLER — turn page at confidence >= theta, cap 4")
print("     vs fixed clocks; 10 tenant-turns per pair")
print("=" * 68)
print("pair      theta=0.5              theta=0.7              best fixed@<=dwell")
for pname, lib in libs.items():
    line = f"{pname}  "
    dwells_used = {}
    for theta in (0.5, 0.7):
        e = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
        ok = 0
        used = []
        purs = []
        for t in range(10):
            target = ["A", "B"][t % 2]
            e.wipe()
            deploy(e, lib[target])
            for b in range(1, 5):
                e.beat(write_sig=False)
                if confidence(e, lib[target]) >= theta or b == 4:
                    break
            used.append(b)
            c, pur = judge(e, lib, target)
            ok += int(c)
            purs.append(pur)
        md = float(np.mean(used))
        dwells_used[theta] = md
        line += f"{ok * 10:3d}% pur {np.mean(purs):+.2f} dwell {md:.1f}     "
    # best fixed result with dwell <= adaptive theta=0.7 mean dwell (rounded up)
    cap = int(np.ceil(dwells_used[0.7]))
    besta, bestm = frontier[pname][min(cap, 4) - 1]
    line += f"d={min(cap, 4)}: {besta * 100:3.0f}% {bestm:+.2f}"
    print(line)
