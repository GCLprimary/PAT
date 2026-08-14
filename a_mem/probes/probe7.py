"""Probe suite 7: multiplicative composition -- signature as prior, not mass.

The additive decoder failed composition because renormalization makes every
emitted unit compete with anchor regrowth. Fix under test: the decoded
signature becomes a per-cell PRIOR that multiplies the spray (gain field),
adding zero mass. Gist modulates; anchors supply the substance.
"""
import numpy as np
from gauge import Gauge, GRID, N, SEED, shifted, BURST_R
from gauge5 import GaugeV5, CORE_ORBITS

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(7)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

class GaugeV5M(GaugeV5):
    """decoded signature as multiplicative prior on the spray"""
    def __init__(self, seed=0, violence=0.45, decay=0.05, gain=2.0):
        super().__init__(seed=seed, violence=violence, decay=decay, decode_amp=0.0)
        self.gain = gain

    def prior_map(self):
        pm = np.zeros((GRID, GRID))
        tot = self.sig.sum()
        if tot <= 0:
            return pm
        for k, orbit in CORE_ORBITS.items():
            q = self.sig[k] / tot
            if q <= 0:
                continue
            for i, (gx, gy) in enumerate(orbit):
                # widen the ray one cell to each side so the prior covers
                # the neighborhood the ray passes through, not just the bone
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        x, y = gx + dx, gy + dy
                        if 0 <= x < GRID and 0 <= y < GRID:
                            pm[y, x] += q
        m = pm.max()
        return pm / m if m > 0 else pm

    def _outpour_tick(self):
        prior = self.prior_map()
        src = np.where((self.w >= 0.25) | (self.a >= self.th_src()), self.a, 0.0)
        amp = self.violence
        add = np.zeros_like(self.a)
        for dy in range(-BURST_R, BURST_R + 1):
            for dx in range(-BURST_R, BURST_R + 1):
                if dx == 0 and dy == 0:
                    continue
                gate = self.rng.random((GRID, GRID)) < 0.5
                add += shifted(src, -dx, -dy) * gate * amp * 0.3 * \
                       self.rng.random((GRID, GRID))
        if self.sig.sum() > 0 and self.gain > 0:
            add *= (1.0 + self.gain * prior)
        self.a = self.a + add
        self._renorm()

patterns = {
    "NW": (SEED, 3, 3),
    "SE": (SEED, 15, 14),
    "line": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
names = list(patterns)
V, D = 0.45, 0.05

anchors = {}
for name, (pts, cx, cy) in patterns.items():
    e = Gauge(False, seed=21, violence=0.0, decay=D)
    e.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        e._decay_traps("audit")
        e._sustain()
    anchors[name] = (e.w > 0.4)

sigs, orig = {}, {}
for name, (pts, cx, cy) in patterns.items():
    e = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    sigs[name] = e.sig.copy()
    orig[name] = (e.w > 0.4).astype(float)

def recall(anchor_name, sig_name, gain, frac=0.5, seed=5):
    e = GaugeV5M(seed=seed, violence=V, decay=D, gain=gain)
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
print("M1 · ACCEPTANCE, MULTIPLICATIVE — half-anchors + prior vs anchors")
print("=" * 66)
mB, _ = margin({n: recall(n, None, 0.0) for n in names})
print(f"  B (anchors alone):     {mB:+.3f}")
best = None
for g in (0.5, 1.0, 2.0, 4.0, 8.0):
    m, M = margin({n: recall(n, n, g, seed=6) for n in names})
    flag = "  <-- C > B" if m > mB else ""
    print(f"  C gain={g:4.1f}:          {m:+.3f}{flag}")
    if best is None or m > best[1]:
        best = (g, m, M)
g_star, mC, MC = best
print(f"\n  best C at gain={g_star}: {mC:+.3f}   acceptance: {'PASS' if mC > mB else 'FAIL'}")
print(f"           " + "  ".join(f"{n:>6s}" for n in names))
for i, n1 in enumerate(names):
    print(f"  {n1:5s}   " + "  ".join(f"{MC[i, j]:6.3f}" for j in range(len(names))))

print()
print("=" * 66)
print("M2 · SPARSE-ANCHOR RESCUE, MULTIPLICATIVE")
print("=" * 66)
print("frac    no sig    prior (best gain)    rescue")
for frac in (0.10, 0.20, 0.35):
    m0, _ = margin({n: recall(n, None, 0.0, frac=frac, seed=17) for n in names})
    m1, _ = margin({n: recall(n, n, g_star, frac=frac, seed=17) for n in names})
    print(f"{frac:.2f}    {m0:+.3f}    {m1:+.3f}              {m1 - m0:+.3f}")

print()
print("=" * 66)
print("M3 · DISAMBIGUATION — mismatched prior control (anchors i, sig j!=i)")
print("=" * 66)
mis = {n: recall(n, names[(i + 1) % len(names)], g_star, seed=6)
       for i, n in enumerate(names)}
mD, _ = margin(mis)
print(f"  matched C:    {mC:+.3f}")
print(f"  mismatched D: {mD:+.3f}   (want D << C: prior must carry identity)")
