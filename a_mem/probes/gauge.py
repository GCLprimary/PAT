"""Dual-gauge engine for the normalization probe.

Two machines, identical dynamics, one switch:
  ABSOLUTE:   fixed thresholds (0.35/0.3/0.6...), no renorm, nothing = zero
  NORMALIZED: field renormalized to sum=1 each tick, thresholds are
              multiples of the uniform share u = 1/N, nothing = flatness

Shared deviation from v4 (both arms, for fairness): spray is proportional
to source activation, so every operation is scale-free and the ONLY
difference between arms is the gauge.
"""
import numpy as np

GRID = 23
N = GRID * GRID
C = (GRID - 1) // 2
OUTPOUR_TICKS, AUDIT_TICKS, INDRAW_TICKS = 3, 18, 6
BURST_R = 4

def offsets_for(d2list):
    out = []
    R = int(np.ceil(np.sqrt(max(d2list))))
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            if (dx or dy) and dx * dx + dy * dy in d2list:
                out.append((dx, dy))
    return out

OFF = offsets_for([9, 16, 25]) + offsets_for([2, 8, 18, 32])
SEED = [(0, 0), (3, 0), (0, 4), (3, 4), (1, 1), (2, 2), (3, 3)]

IN_TX = -np.ones((GRID, GRID), dtype=int)
IN_TY = -np.ones((GRID, GRID), dtype=int)
for y in range(GRID):
    for x in range(GRID):
        rx, ry = x - C, y - C
        if (rx or ry) and (rx + ry) % 2 == 0:
            tx, ty = C + (rx + ry) // 2, C + (ry - rx) // 2
            if 0 <= tx < GRID and 0 <= ty < GRID:
                IN_TX[y, x], IN_TY[y, x] = tx, ty
PARITY_OK = IN_TX >= 0
IS_CENTER = np.zeros((GRID, GRID), dtype=bool)
IS_CENTER[C, C] = True

def shifted(arr, dx, dy):
    out = np.zeros_like(arr)
    xs = slice(max(0, -dx), GRID - max(0, dx))
    ys = slice(max(0, -dy), GRID - max(0, dy))
    xs2 = slice(max(0, dx), GRID - max(0, -dx))
    ys2 = slice(max(0, dy), GRID - max(0, -dy))
    out[ys, xs] = arr[ys2, xs2]
    return out

class Gauge:
    def __init__(self, norm, seed=0, violence=0.45, decay=0.05):
        self.norm = norm
        self.rng = np.random.default_rng(seed)
        self.a = np.zeros((GRID, GRID))
        self.w = np.zeros((GRID, GRID))
        self.sig = np.zeros(9)
        self.violence = violence
        self.decay = decay

    # thresholds: absolute machine uses fixed rulers; normalized machine
    # uses multiples of the uniform share of current total mass
    def _u(self):
        if not self.norm:
            return 1.0  # rulers are absolute fractions of the unit cell cap
        s = self.a.sum()
        return (s / N) if s > 0 else 0.0

    def th_active(self):  return 0.35 if not self.norm else 3.0 * self._u()
    def th_relay(self):   return 0.30 if not self.norm else 2.5 * self._u()
    def th_dig(self):     return 0.60 if not self.norm else 6.0 * self._u()
    def th_src(self):     return 0.85 if not self.norm else 8.0 * self._u()
    def th_quiet(self):   return 0.20 if not self.norm else 1.5 * self._u()

    def _renorm(self):
        if self.norm:
            s = self.a.sum()
            if s > 0:
                self.a /= s

    def stamp(self, pts, cx, cy, w0=0.45):
        hi = 1.0 if not self.norm else 10.0 / N
        for dx, dy in pts:
            x, y = cx + dx, cy + dy
            if 0 <= x < GRID and 0 <= y < GRID:
                self.a[y, x] = max(self.a[y, x], hi)
                self.w[y, x] = max(self.w[y, x], w0)
        self._renorm()

    def wipe(self):
        """erasure in each gauge's native sense"""
        self.w[:] = 0
        if self.norm:
            self.a[:] = 1.0 / N      # nothing = flat
        else:
            self.a[:] = 0.0          # nothing = zero

    def _decay_traps(self, mode):
        d = self.decay * (0.3 if mode == "outpour" else 1.0)
        self.a -= d * self.a * (1 - 0.75 * self.w)
        if not self.norm:
            self.a[self.a < 0.001] = 0
        dig = self.a > self.th_dig()
        self.w[dig] += 0.014 * (1 - self.w[dig])
        erode = self.a < self.th_quiet()
        self.w[erode] *= 0.996
        self._renorm()

    def _sustain(self):
        active = self.a >= self.th_active()
        boost = np.zeros_like(self.a)
        for dx, dy in OFF:
            nb = shifted(self.a, dx, dy)
            nb_act = shifted(active.astype(float), dx, dy) > 0
            boost += np.where(active & nb_act, 0.022 * nb, 0.0)
        self.a = self.a + boost
        if not self.norm:
            self.a = np.minimum(1.0, self.a)
        self._renorm()

    def _outpour_tick(self):
        maxsig = max(self.sig.max(), 1e-12)
        core_amp = (1.0 if not self.norm else 6.0 / N)
        for ry in (-1, 0, 1):
            for rx in (-1, 0, 1):
                s = self.sig[(ry + 1) * 3 + (rx + 1)] / maxsig
                if s > 0.02:
                    self.a[C + ry, C + rx] += s * core_amp
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
        self.a = self.a + add
        if not self.norm:
            self.a = np.minimum(1.0, self.a)
        self._renorm()

    def _indraw_tick(self, write_sig=True):
        part = ((self.a >= self.th_relay()) | (self.w > 0.4)) & ~IS_CENTER
        passed = part & PARITY_OK
        carried = np.where(passed, 0.45 * self.a, 0.0)
        self.a = np.where(passed, self.a * 0.6, self.a)
        add = np.zeros_like(self.a)
        for y in range(GRID):
            for x in range(GRID):
                c = carried[y, x]
                if c > 0:
                    tx, ty = IN_TX[y, x], IN_TY[y, x]
                    add[ty, tx] += c
                    if write_sig and abs(tx - C) <= 1 and abs(ty - C) <= 1:
                        self.sig[(ty - C + 1) * 3 + (tx - C + 1)] += c
        self.a += add
        self._renorm()

    def beat(self, write_sig=True):
        for _ in range(OUTPOUR_TICKS):
            self._outpour_tick()
            self._decay_traps("outpour")
            self._sustain()
        for _ in range(AUDIT_TICKS):
            self._decay_traps("audit")
            self._sustain()
        for _ in range(INDRAW_TICKS):
            self._indraw_tick(write_sig)
            self._decay_traps("indraw")
            self._sustain()

    # metrics
    def defined_frac(self):
        return float((self.w > 0.4).mean())

    def flatness(self):
        """exp(entropy)/N of normalized shape: 1 = flat, ->0 = concentrated"""
        s = self.a.sum()
        if s <= 0:
            return float("nan")
        p = (self.a / s).ravel()
        p = p[p > 0]
        H = -(p * np.log(p)).sum()
        return float(np.exp(H) / N)
