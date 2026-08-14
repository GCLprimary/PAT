"""Headless port of Alignment Field IV dynamics for probing.

Faithful to the JSX rules; one noted deviation: member sustainment is applied
simultaneously (accumulated from current activations) rather than sequentially.
"""
import numpy as np

GRID = 23
C = (GRID - 1) // 2
ACT_T = 0.35
TRAP_T = 0.4
OUTPOUR_TICKS, AUDIT_TICKS, INDRAW_TICKS = 3, 18, 6
BURST_R = 4

def offsets_for(d2list):
    out = []
    R = int(np.ceil(np.sqrt(max(d2list))))
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            if dx == 0 and dy == 0:
                continue
            if dx * dx + dy * dy in d2list:
                out.append((dx, dy))
    return out

OFF_INT = offsets_for([9, 16, 25])
OFF_QUAD = offsets_for([2, 8, 18, 32])
SEED = [(0, 0), (3, 0), (0, 4), (3, 4), (1, 1), (2, 2), (3, 3)]

# precompute indraw mapping: (x,y) -> target (tx,ty) or -1 if sieved/center
IN_TX = -np.ones((GRID, GRID), dtype=int)
IN_TY = -np.ones((GRID, GRID), dtype=int)
for y in range(GRID):
    for x in range(GRID):
        rx, ry = x - C, y - C
        if rx == 0 and ry == 0:
            continue
        if (rx + ry) % 2 != 0:
            continue
        tx, ty = C + (rx + ry) // 2, C + (ry - rx) // 2
        if 0 <= tx < GRID and 0 <= ty < GRID:
            IN_TX[y, x], IN_TY[y, x] = tx, ty

PARITY_OK = (IN_TX >= 0)
IS_CENTER = np.zeros((GRID, GRID), dtype=bool)
IS_CENTER[C, C] = True

def shifted(arr, dx, dy):
    """value at (x+dx, y+dy), zero outside."""
    out = np.zeros_like(arr)
    xs = slice(max(0, -dx), GRID - max(0, dx))
    ys = slice(max(0, -dy), GRID - max(0, dy))
    xs2 = slice(max(0, dx), GRID - max(0, -dx))
    ys2 = slice(max(0, dy), GRID - max(0, -dy))
    out[ys, xs] = arr[ys2, xs2]
    return out

class Engine:
    def __init__(self, seed=0, violence=0.45, decay=0.05,
                 use_int=True, use_quad=True):
        self.rng = np.random.default_rng(seed)
        self.a = np.zeros((GRID, GRID))
        self.w = np.zeros((GRID, GRID))
        self.sig = np.zeros(9)
        self.violence = violence
        self.decay = decay
        self.offs = ([o for o in OFF_INT] if use_int else []) + \
                    ([o for o in OFF_QUAD] if use_quad else [])
        self.beats = 0
        self.last_passed = 0
        self.last_rejected = 0

    def stamp(self, pts, cx, cy, w0=0.45):
        for dx, dy in pts:
            x, y = cx + dx, cy + dy
            if 0 <= x < GRID and 0 <= y < GRID:
                self.a[y, x] = 1.0
                self.w[y, x] = max(self.w[y, x], w0)

    def clear_field(self):
        self.a[:] = 0
        self.w[:] = 0

    # ── strokes ──
    def _decay_and_traps(self, mode):
        d = self.decay * 0.3 if mode == "outpour" else self.decay
        self.a -= d * self.a * (1 - 0.75 * self.w)
        self.a[self.a < 0.001] = 0
        dig = self.a > 0.6
        self.w[dig] += 0.014 * (1 - self.w[dig])
        erode = self.a < 0.2
        self.w[erode] *= 0.996

    def _sustain(self):
        active = self.a >= ACT_T
        boost = np.zeros_like(self.a)
        for dx, dy in self.offs:
            nb = shifted(self.a, dx, dy)
            nb_active = shifted(active.astype(float), dx, dy) > 0
            boost += np.where(active & nb_active, 0.022 * nb, 0.0)
        self.a = np.minimum(1.0, self.a + boost)

    def member_count(self):
        active = self.a >= ACT_T
        m = 0
        for dx, dy in self.offs:
            if dy < 0 or (dy == 0 and dx < 0):
                continue
            m += int(np.sum(active & (shifted(active.astype(float), dx, dy) > 0)))
        return m

    def _outpour_tick(self):
        maxsig = max(self.sig.max(), 0.001)
        for ry in (-1, 0, 1):
            for rx in (-1, 0, 1):
                s = self.sig[(ry + 1) * 3 + (rx + 1)] / maxsig
                if s > 0.02:
                    self.a[C + ry, C + rx] = min(1.0, self.a[C + ry, C + rx] + s)
        src = ((self.w >= 0.25) | (self.a >= 0.85)).astype(float)
        amp = self.violence
        add = np.zeros_like(self.a)
        for dy in range(-BURST_R, BURST_R + 1):
            for dx in range(-BURST_R, BURST_R + 1):
                if dx == 0 and dy == 0:
                    continue
                gate = (self.rng.random((GRID, GRID)) < 0.5)
                add += shifted(src, -dx, -dy) * gate * amp * 0.3 * \
                       self.rng.random((GRID, GRID))
        self.a = np.minimum(1.0, self.a + add)

    def _indraw_tick(self, write_sig=True):
        part = ((self.a >= 0.3) | (self.w > TRAP_T)) & ~IS_CENTER
        passed = part & PARITY_OK
        rejected = part & ~PARITY_OK
        self.last_passed += int(passed.sum())
        self.last_rejected += int(rejected.sum())
        carried = np.where(passed, 0.45 * self.a, 0.0)
        self.a = np.where(passed, self.a * 0.6, self.a)
        add = np.zeros_like(self.a)
        for y in range(GRID):
            for x in range(GRID):
                if carried[y, x] > 0:
                    tx, ty = IN_TX[y, x], IN_TY[y, x]
                    add[ty, tx] += carried[y, x]
                    if write_sig and abs(tx - C) <= 1 and abs(ty - C) <= 1:
                        self.sig[(ty - C + 1) * 3 + (tx - C + 1)] += carried[y, x]
        self.a = np.minimum(1.0, self.a + add)

    def beat(self, write_sig=True, do_outpour=True):
        if do_outpour:
            for _ in range(OUTPOUR_TICKS):
                self._outpour_tick()
                self._decay_and_traps("outpour")
                self._sustain()
        for _ in range(AUDIT_TICKS):
            self._decay_and_traps("audit")
            self._sustain()
        self.last_passed = self.last_rejected = 0
        for _ in range(INDRAW_TICKS):
            self._indraw_tick(write_sig=write_sig)
            self._decay_and_traps("indraw")
            self._sustain()
        self.beats += 1

    # ── v1-style dynamics (no strokes) for the survival test ──
    def quiet_ticks(self, n):
        for _ in range(n):
            self._decay_and_traps("audit")
            self._sustain()

    def defined_count(self):
        return int((self.w > TRAP_T).sum())

    def act_mass(self):
        return float(self.a.sum())
