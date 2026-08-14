"""Probe suite 16: mid-phase sweep of unprobed claims.

Q1 (R-2): cue-route on the SHIPPED package -- k=12 bank, partial-anchor
    cues at 50% and 25%, top-1 accuracy of the classify_cue route.
Q2 (D-3): relocation efficacy -- store P1; add colliding P2 (overlap ~0.62)
    as-is vs relocated below the 0.45 danger line; measure BOTH margins.
Q3 (open): U-curve replication -- 5 sequential imprints x 6 seeds; trap
    survival by age. Does primacy+recency reproduce, or was it seed noise?
"""
import numpy as np
import sys, tempfile, shutil

np.set_printoptions(precision=3, suppress=True)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

SEED_PTS = [(0, 0), (3, 0), (0, 4), (3, 4), (1, 1), (2, 2), (3, 3)]
LINE = [(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)]

print("=" * 66)
print("Q1 · CUE-ROUTE ON SHIPPED PACKAGE — k=12, partial-anchor cues")
print("=" * 66)
from amem.api import Memory
tmp = tempfile.mkdtemp()
mem = Memory(seed=5, path=tmp)
bank = []
for i, (cx, cy) in enumerate([(3, 3), (15, 14), (3, 14), (14, 3),
                              (9, 3), (3, 9), (14, 9), (9, 14)]):
    bank.append([(cx + dx, cy + dy) for dx, dy in SEED_PTS])
for (cx, cy) in [(2, 2), (11, 16), (2, 16), (11, 2)]:
    bank.append([(cx + dx, cy + dy) for dx, dy in LINE])
mids = [mem.write(p) for p in bank]
rng = np.random.default_rng(11)
for frac in (0.5, 0.25):
    ok = tot = 0
    for i, (mid, pat) in enumerate(zip(mids, bank)):
        anchors = np.argwhere(mem.library.get(mid).anchors) if hasattr(mem.library, "get") else None
        cells = pat  # cue from the pattern's own cells (subset)
        for s in range(3):
            r2 = np.random.default_rng(100 + 10 * i + s)
            k = max(2, int(round(len(cells) * frac)))
            pick_cells = [cells[j] for j in r2.choice(len(cells), size=k, replace=False)]
            res = mem.recall(cue=pick_cells)
            ok += int(res.identity == mid)  # corrected: RecallResult.identity (initial run misread this and scored 0%)
            tot += 1
    print(f"  cue fraction {frac:.2f}: {ok}/{tot} = {ok / tot * 100:3.0f}%")
shutil.rmtree(tmp, ignore_errors=True)

print()
print("=" * 66)
print("Q2 · D-3 RELOCATION EFFICACY — colliding write vs relocated write")
print("=" * 66)
sys.path.insert(0, "/home/claude/probe")
from gauge import Gauge, GRID, N
from gauge5 import GaugeV5
V, D = 0.45, 0.05

def build_id(cx, cy):
    ea = Gauge(False, seed=21, violence=0.0, decay=D)
    ea.stamp(SEED_PTS, cx, cy, w0=0.0)
    for _ in range(80):
        ea._decay_traps("audit")
        ea._sustain()
    en = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    en.stamp(SEED_PTS, cx, cy)
    for _ in range(8):
        en.beat()
    return dict(anchors=(ea.w > 0.4), orig=(en.w > 0.4).astype(float))

def pair_margins(lib, seeds=(5, 6, 7)):
    outs = []
    for sd in seeds:
        rng2 = np.random.default_rng(sd)
        ms = []
        for tgt in ("P1", "P2"):
            oth = "P2" if tgt == "P1" else "P1"
            e = GaugeV5(seed=sd, violence=V, decay=D, decode_amp=0.0)
            e.wipe()
            cells = np.argwhere(lib[tgt]["anchors"])
            sel = cells[rng2.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
            for y, x in sel:
                e.a[y, x] += 10.0 / N
            e._renorm()
            for _ in range(4):
                e.beat(write_sig=False)
            ms.append(cos(e.w, lib[tgt]["orig"]) - cos(e.w, lib[oth]["orig"]))
        outs.append(ms)
    arr = np.array(outs)
    return arr.mean(axis=0)

P1 = build_id(5, 5)
collide = {"P1": P1, "P2": build_id(8, 8)}      # overlap ~0.62 (danger zone)
reloc = {"P1": P1, "P2": build_id(13, 13)}       # relocated below 0.45
print(f"  stored-pair overlap: collide={cos(collide['P1']['orig'], collide['P2']['orig']):.3f}"
      f"  relocated={cos(reloc['P1']['orig'], reloc['P2']['orig']):.3f}")
m_c = pair_margins(collide)
m_r = pair_margins(reloc)
print(f"  margins (P1, P2)  as-collided: {m_c[0]:+.3f}, {m_c[1]:+.3f}")
print(f"  margins (P1, P2)  relocated:   {m_r[0]:+.3f}, {m_r[1]:+.3f}")

print()
print("=" * 66)
print("Q3 · U-CURVE REPLICATION — 5 sequential imprints x 6 seeds")
print("=" * 66)
positions = [(3, 3), (15, 14), (3, 14), (14, 3), (9, 9)]
ids = [build_id(*p) for p in positions]
surv = np.zeros((6, 5))
for si, sd in enumerate((5, 9, 13, 21, 33, 47)):
    e = GaugeV5(seed=sd, violence=V, decay=D, decode_amp=0.0)
    for (cx, cy) in positions:
        e.stamp(SEED_PTS, cx, cy)
        for _ in range(4):
            e.beat(write_sig=False)
    for age, ident in enumerate(reversed(ids)):     # age 0 = newest
        mask = ident["orig"] > 0
        surv[si, age] = float((e.w > 0.4)[mask].mean())
print("age (0=newest):      0      1      2      3      4(first)")
print("mean survival:    " + "  ".join(f"{v:.2f}" for v in surv.mean(axis=0)))
print("std:              " + "  ".join(f"{v:.2f}" for v in surv.std(axis=0)))
u = surv.mean(axis=0)
print(f"\nU-shape test (ends > middle): newest {u[0]:.2f}, oldest {u[4]:.2f}, "
      f"middle mean {u[1:4].mean():.2f} -> "
      f"{'U-CURVE REPLICATES' if u[0] > u[1:4].mean() and u[4] > u[1:4].mean() else 'NOT REPLICATED'}")
