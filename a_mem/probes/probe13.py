"""Probe suite 13: D-2 capacity levers.

Three core designs, same field physics:
  V0 baseline  -- 3x3 capture, 8 live cells (the measured ~8-10 ceiling)
  V1 ring      -- 5x5 capture tap (24 live cells): 'additional cores' as an
                  extended ring; arrivals recorded en route, transport unchanged
  V2 radius    -- 3x3 capture but arrivals binned by hop age (6 bins):
                  the spiral-twist key -- angle AND radius
Bank: 24 identities (16 constellation positions + 8 line positions).
Library seed 42; probes seeds 77 & 101; accuracy vs k in {8,12,16,20,24}.
"""
import numpy as np
from gauge import Gauge, GRID, N, C, SEED, shifted, BURST_R
from gauge5 import GaugeV5

np.set_printoptions(precision=3, suppress=True)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

V, D = 0.45, 0.05
LINE = [(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)]

bank = []
pos_c = [(3, 3), (15, 14), (3, 14), (14, 3), (9, 3), (3, 9), (14, 9), (9, 14),
         (6, 6), (12, 12), (6, 12), (12, 6), (9, 9), (3, 6), (15, 6), (6, 15)]
for i, (cx, cy) in enumerate(pos_c):
    bank.append((f"C{i:02d}", SEED, cx, cy))
pos_l = [(2, 2), (11, 16), (2, 16), (11, 2), (2, 9), (11, 9), (6, 4), (6, 13)]
for i, (cx, cy) in enumerate(pos_l):
    bank.append((f"L{i}", LINE, cx, cy))
names_all = [b[0] for b in bank]

class GaugeCap(GaugeV5):
    """adds: age field (mass-weighted hop count), ring tap, radius bins"""
    def __init__(self, **kw):
        super().__init__(decode_amp=0.0, **kw)
        self.age = np.zeros((GRID, GRID))
        self.sig9 = np.zeros(9)          # V0
        self.sig_ring = np.zeros(25)     # V1 (5x5; center stays dark)
        self.sig_rad = np.zeros((9, 6))  # V2 (cell x hop-age bin)

    def _blend_new_mass(self, add):
        tot = self.a + add
        with np.errstate(invalid="ignore", divide="ignore"):
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
        from gauge import IN_TX, IN_TY, PARITY_OK, IS_CENTER
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
                # mass-weighted age blend at destination
                new_age[ty, tx] = (new_age[ty, tx] * prev + hop_age * c) / max(prev + c, 1e-12)
                drx, dry = tx - C, ty - C
                if write_sig:
                    if abs(drx) <= 2 and abs(dry) <= 2:
                        self.sig_ring[(dry + 2) * 5 + (drx + 2)] += c
                    if abs(drx) <= 1 and abs(dry) <= 1:
                        idx9 = (dry + 1) * 3 + (drx + 1)
                        self.sig9[idx9] += c
                        b = min(int(round(hop_age)) - 1, 5)
                        self.sig_rad[idx9, max(b, 0)] += c
        self.a += add
        self.age = new_age
        self._renorm()

def imprint(pts, cx, cy, seed):
    e = GaugeCap(seed=seed, violence=V, decay=D)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    return dict(v0=e.sig9.copy(), v1=e.sig_ring.copy(), v2=e.sig_rad.ravel().copy())

print("imprinting 24 identities x 3 seeds (library + 2 probes)...")
lib, probes = {}, {}
for name, pts, cx, cy in bank:
    lib[name] = imprint(pts, cx, cy, 42)
    probes[name] = [imprint(pts, cx, cy, s) for s in (77, 101)]

print()
print("=" * 66)
print("CLASSIFICATION ACCURACY vs k  (V0 9-cell | V1 ring-24 | V2 radius)")
print("=" * 66)
print(" k    V0 base   V1 ring   V2 radius")
results = {}
for k in (8, 12, 16, 20, 24):
    sub = names_all[:k]
    row = []
    for variant in ("v0", "v1", "v2"):
        ok = tot = 0
        for name in sub:
            for p in probes[name]:
                pick = max(sub, key=lambda n: cos(p[variant], lib[n][variant]))
                ok += int(pick == name)
                tot += 1
        row.append(ok / tot)
    results[k] = row
    print(f"{k:3d}   " + "   ".join(f"{r * 100:5.0f}%" for r in row))

print()
print("worst confusion at k=24 per variant:")
for variant in ("v0", "v1", "v2"):
    pairs = [(cos(lib[a][variant], lib[b][variant]), a, b)
             for i, a in enumerate(names_all) for b in names_all[i + 1:]]
    pairs.sort(reverse=True)
    print(f"  {variant}: {pairs[0][1]}~{pairs[0][2]} cos={pairs[0][0]:.3f}")

print()
print("D-2 acceptance target: >=25 ids at >=90% -- nearest achieved:")
for variant, label in (("v0", "V0"), ("v1", "V1"), ("v2", "V2")):
    best_k = max((k for k in results if results[k][("v0", "v1", "v2").index(variant)] >= 0.90),
                 default=None)
    acc24 = results[24][("v0", "v1", "v2").index(variant)]
    print(f"  {label}: >=90% holds through k={best_k}   (k=24 accuracy {acc24 * 100:.0f}%)")
