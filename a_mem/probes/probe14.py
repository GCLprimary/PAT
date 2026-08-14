"""Probe suite 14: V3 combo capacity + D-4 slope clock.

Part A: V3 = ring(24 cells) x radius(6 hop bins) = 144-dim code, same bank
        of 24 identities; compared against V0/V1/V2 on identical imprints.
Part B: clock v2 -- completion at beat 1 as a slope signal: turn immediately
        if c1 >= S_HI (easy), else continue to level theta or cap (hard).
        Compared against fixed-1, fixed-3, and the v1 level controller.
"""
import numpy as np
from gauge import Gauge, GRID, N, C, SEED, shifted, BURST_R
from gauge import IN_TX, IN_TY, PARITY_OK, IS_CENTER
from gauge5 import GaugeV5

np.set_printoptions(precision=3, suppress=True)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

V, D = 0.45, 0.05
LINE = [(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)]

class GaugeCap(GaugeV5):
    def __init__(self, **kw):
        super().__init__(decode_amp=0.0, **kw)
        self.age = np.zeros((GRID, GRID))
        self.sig9 = np.zeros(9)
        self.sig_ring = np.zeros(25)
        self.sig_rad = np.zeros((9, 6))
        self.sig_rr = np.zeros((25, 6))   # V3: ring cell x hop bin

    def _blend_new_mass(self, add):
        tot = self.a + add
        self.age = np.where(tot > 0, self.age * self.a / np.maximum(tot, 1e-12), 0.0)

    def _outpour_tick(self):
        src = np.where((self.w >= 0.25) | (self.a >= self.th_src()), self.a, 0.0)
        add = np.zeros_like(self.a)
        for dy in range(-BURST_R, BURST_R + 1):
            for dx in range(-BURST_R, BURST_R + 1):
                if dx == 0 and dy == 0:
                    continue
                gate = self.rng.random((GRID, GRID)) < 0.5
                add += shifted(src, -dx, -dy) * gate * self.violence * 0.3 * \
                       self.rng.random((GRID, GRID))
        self._blend_new_mass(add)
        self.a = self.a + add
        self._renorm()

    def _indraw_tick(self, write_sig=True):
        part = ((self.a >= self.th_relay()) | (self.w > 0.4)) & ~IS_CENTER
        passed = part & PARITY_OK
        carried = np.where(passed, 0.45 * self.a, 0.0)
        self.a = np.where(passed, self.a * 0.6, self.a)
        add = np.zeros_like(self.a)
        new_age = self.age.copy()
        for y in range(GRID):
            for x in range(GRID):
                c = carried[y, x]
                if c <= 0:
                    continue
                tx, ty = IN_TX[y, x], IN_TY[y, x]
                hop_age = self.age[y, x] + 1.0
                prev = add[ty, tx] + self.a[ty, tx]
                add[ty, tx] += c
                new_age[ty, tx] = (new_age[ty, tx] * prev + hop_age * c) / max(prev + c, 1e-12)
                drx, dry = tx - C, ty - C
                if write_sig:
                    b = min(max(int(round(hop_age)) - 1, 0), 5)
                    if abs(drx) <= 2 and abs(dry) <= 2:
                        ridx = (dry + 2) * 5 + (drx + 2)
                        self.sig_ring[ridx] += c
                        self.sig_rr[ridx, b] += c
                    if abs(drx) <= 1 and abs(dry) <= 1:
                        idx9 = (dry + 1) * 3 + (drx + 1)
                        self.sig9[idx9] += c
                        self.sig_rad[idx9, b] += c
        self.a += add
        self.age = new_age
        self._renorm()

bank = []
pos_c = [(3, 3), (15, 14), (3, 14), (14, 3), (9, 3), (3, 9), (14, 9), (9, 14),
         (6, 6), (12, 12), (6, 12), (12, 6), (9, 9), (3, 6), (15, 6), (6, 15)]
for i, (cx, cy) in enumerate(pos_c):
    bank.append((f"C{i:02d}", SEED, cx, cy))
pos_l = [(2, 2), (11, 16), (2, 16), (11, 2), (2, 9), (11, 9), (6, 4), (6, 13)]
for i, (cx, cy) in enumerate(pos_l):
    bank.append((f"L{i}", LINE, cx, cy))
names_all = [b[0] for b in bank]

def imprint(pts, cx, cy, seed):
    e = GaugeCap(seed=seed, violence=V, decay=D)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    return dict(v0=e.sig9.copy(), v1=e.sig_ring.copy(),
                v2=e.sig_rad.ravel().copy(), v3=e.sig_rr.ravel().copy())

print("Part A: imprinting 24 x 3 ...")
lib, probes = {}, {}
for name, pts, cx, cy in bank:
    lib[name] = imprint(pts, cx, cy, 42)
    probes[name] = [imprint(pts, cx, cy, s) for s in (77, 101)]

print("\n k    V0      V1      V2      V3(combo)")
for k in (12, 16, 20, 24):
    sub = names_all[:k]
    row = []
    for variant in ("v0", "v1", "v2", "v3"):
        ok = tot = 0
        for name in sub:
            for p in probes[name]:
                pick = max(sub, key=lambda n: cos(p[variant], lib[n][variant]))
                ok += int(pick == name)
                tot += 1
        row.append(ok / tot)
    print(f"{k:3d}   " + "   ".join(f"{r * 100:4.0f}%" for r in row))

print()
print("=" * 66)
print("Part B: CLOCK v2 (slope) vs fixed and level controllers")
print("=" * 66)
PAIRS = {"easy(sep12)": ((3, 3), (15, 14)),
         "mid(sep5)  ": ((4, 4), (9, 9)),
         "hard(sep3) ": ((5, 5), (8, 8))}
rng = np.random.default_rng(7)

def build_id(cx, cy):
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

libs = {p: {"A": build_id(*a), "B": build_id(*b)} for p, (a, b) in PAIRS.items()}

def deploy(e, ident):
    cells = np.argwhere(ident["anchors"])
    sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
    for y, x in sel:
        e.a[y, x] += 10.0 / N
    e._renorm()

def conf(e, ident):
    m = ident["anchors"]
    return float((e.w > 0.4)[m].mean()) if m.sum() else 0.0

S_HI, THETA, CAP = 0.55, 0.7, 4

def run_clock(lib, policy, turns=10, seed=5):
    e = GaugeV5(seed=seed, violence=V, decay=D, decode_amp=0.0)
    ok = 0
    dwells = []
    for t in range(turns):
        tgt = ["A", "B"][t % 2]
        oth = "B" if tgt == "A" else "A"
        e.wipe()
        deploy(e, lib[tgt])
        b = 0
        while True:
            e.beat(write_sig=False)
            b += 1
            c = conf(e, lib[tgt])
            if policy == "fixed1" and b >= 1: break
            if policy == "fixed3" and b >= 3: break
            if policy == "level" and (c >= THETA or b >= CAP): break
            if policy == "slope":
                if b == 1 and c >= S_HI: break          # crystallized fast: easy
                if c >= THETA or b >= CAP: break        # else level fallback
        dwells.append(b)
        ok += int(cos(e.w, lib[tgt]["orig"]) > cos(e.w, lib[oth]["orig"]))
    return ok / turns, float(np.mean(dwells))

print("pair          fixed1        fixed3        level-v1      slope-v2")
tot = {p: [0, 0] for p in ("fixed1", "fixed3", "level", "slope")}
for pname, lib2 in libs.items():
    line = f"{pname}  "
    for pol in ("fixed1", "fixed3", "level", "slope"):
        acc, dw = run_clock(lib2, pol)
        tot[pol][0] += acc; tot[pol][1] += dw
        line += f"{acc * 100:3.0f}% d{dw:.1f}     "
    print(line)
print("mean          " + "     ".join(
    f"{tot[p][0] / 3 * 100:3.0f}% d{tot[p][1] / 3:.1f}" for p in ("fixed1", "fixed3", "level", "slope")))
