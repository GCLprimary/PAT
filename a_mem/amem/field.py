"""The stage: normalized-gauge field engine.

A homeostatic 2D lattice whose activation is renormalized to sum = 1 every
tick. All thresholds are multiples of the uniform share u = 1/N. "Nothing"
is the flat state (a == 1/N everywhere), not zero.

The shared stroke dynamics (decay/traps, member sustainment, spray outpour,
sieved indraw) live in StrokeEngine; the absolute gauge (amem.absolute)
subclasses it with fixed rulers and a real zero.

Design law 3: the core selects, it never paints. The outpour stroke here is
spray-only — the signature is collected during indraw but is never decoded
back onto the lattice. (The probe campaign measured that both additive and
multiplicative decoding degrade recall.)
"""
import numpy as np

from . import constants as K
from .contraction import contraction_for
from .harness import OFF_ALL, shifted


class StrokeEngine:
    """Shared wave dynamics; gauge-specific rulers supplied by subclasses."""

    normalized = None  # set by subclass

    def __init__(self, grid=K.GRID, seed=0, violence=K.VIOLENCE, decay=K.DECAY):
        self.grid = grid
        self.n = grid * grid
        self.center = (grid - 1) // 2
        self.rng = np.random.default_rng(seed)
        self.a = np.zeros((grid, grid))
        self.w = np.zeros((grid, grid))
        self.sig = np.zeros(9)
        # radius channel (Phase 3, D-2): mass-weighted hop age per cell and
        # the age-binned core codes. sig stays the legacy 9-vector.
        self.age = np.zeros((grid, grid))
        self.sig_rad = np.zeros((9, K.HOP_BINS))
        self.sig_ring = np.zeros(25)
        self.sig_rr = np.zeros((25, K.HOP_BINS))
        self.violence = violence
        self.decay = decay
        self.contraction = contraction_for(grid)
        self.beats = 0
        self.last_passed = 0
        self.last_rejected = 0

    # ── gauge interface ──────────────────────────────────────────────
    def _u(self):
        raise NotImplementedError

    def th_active(self):
        raise NotImplementedError

    def th_relay(self):
        raise NotImplementedError

    def th_dig(self):
        raise NotImplementedError

    def th_src(self):
        raise NotImplementedError

    def th_quiet(self):
        raise NotImplementedError

    def _renorm(self):
        pass

    def _clamp(self):
        pass

    def stamp_amplitude(self):
        raise NotImplementedError

    def wipe(self):
        """Erase to this gauge's native nothing (activation and traps only)."""
        raise NotImplementedError

    # ── state management ─────────────────────────────────────────────
    def clear_codes(self):
        """Zero every collected core code (all gauges of the signature)."""
        self.sig[:] = 0.0
        self.sig_rad[:] = 0.0
        self.sig_ring[:] = 0.0
        self.sig_rr[:] = 0.0

    def reset(self):
        """Hard zero of all state: a fresh, never-written engine."""
        self.a[:] = 0.0
        self.w[:] = 0.0
        self.age[:] = 0.0
        self.clear_codes()

    def stamp(self, cells, w0=K.STAMP_W0):
        """Imprint a set of absolute (x, y) cells at stamp amplitude."""
        hi = self.stamp_amplitude()
        for x, y in cells:
            if 0 <= x < self.grid and 0 <= y < self.grid:
                self.a[y, x] = max(self.a[y, x], hi)
                self.w[y, x] = max(self.w[y, x], w0)
        self._renorm()

    # ── strokes ──────────────────────────────────────────────────────
    def _decay_traps(self, mode):
        d = self.decay * (K.OUTPOUR_DECAY_SCALE if mode == "outpour" else 1.0)
        self.a -= d * self.a * (1.0 - K.TRAP_SHIELD * self.w)
        self._floor()
        dig = self.a > self.th_dig()
        self.w[dig] += K.TRAP_DIG_RATE * (1.0 - self.w[dig])
        erode = self.a < self.th_quiet()
        self.w[erode] *= K.TRAP_ERODE
        self._renorm()

    def _floor(self):
        pass

    def _sustain(self):
        active = self.a >= self.th_active()
        member_mass = self.a * active
        support = np.zeros_like(self.a)
        for dx, dy in OFF_ALL:
            support += shifted(member_mass, dx, dy, self.grid)
        self.a = self.a + K.SUSTAIN_RATE * support * active
        self._clamp()
        self._renorm()

    def _blend_new_mass(self, add):
        """Fresh (age-0) mass arriving at a cell dilutes its hop age,
        mass-weighted (probe 13/14 GaugeCap)."""
        tot = self.a + add
        with np.errstate(invalid="ignore", divide="ignore"):
            self.age = np.where(tot > 0,
                                self.age * self.a / np.maximum(tot, 1e-12),
                                0.0)

    def _outpour_tick(self):
        src = np.where((self.w >= K.ANCHOR_SRC_W) | (self.a >= self.th_src()),
                       self.a, 0.0)
        amp = self.violence
        add = np.zeros_like(self.a)
        for dy in range(-K.BURST_R, K.BURST_R + 1):
            for dx in range(-K.BURST_R, K.BURST_R + 1):
                if dx == 0 and dy == 0:
                    continue
                gate = self.rng.random((self.grid, self.grid)) < K.SPRAY_GATE_P
                add += shifted(src, -dx, -dy, self.grid) * gate * amp * \
                    K.SPRAY_SCALE * self.rng.random((self.grid, self.grid))
        self._blend_new_mass(add)
        self.a = self.a + add
        self._clamp()
        self._renorm()

    def _indraw_tick(self, write_sig=True):
        con = self.contraction
        part = ((self.a >= self.th_relay()) | (self.w > K.TRAP_T)) & ~con.is_center
        passed, rejected = con.sieve(part)
        self.last_passed += int(passed.sum())
        self.last_rejected += int(rejected.sum())
        carried = np.where(passed, K.CARRY_FRAC * self.a, 0.0)
        self.a = np.where(passed, self.a * K.RETAIN_FRAC, self.a)

        # one inward hop: scatter carried mass along the (injective) map
        vals = carried.ravel()[con.src_flat]
        add = np.zeros(self.n, dtype=self.a.dtype)
        np.add.at(add, con.dst_flat, vals)

        # hop-age transport: mass arrives one hop older; destination age is
        # the mass-weighted blend of its retained mass and the arrival
        hop = self.age.ravel()[con.src_flat] + 1.0
        live = vals > 0
        dst = con.dst_flat[live]
        prev = self.a.ravel()[dst]
        arriving = vals[live]
        new_age = self.age.copy()
        new_age.ravel()[dst] = (self.age.ravel()[dst] * prev +
                                hop[live] * arriving) / \
            np.maximum(prev + arriving, 1e-12)

        if write_sig:
            bins = np.clip(np.rint(hop).astype(np.int64) - 1, 0, K.HOP_BINS - 1)
            core = con.sig_at_src >= 0
            np.add.at(self.sig, con.sig_at_src[core], vals[core])
            np.add.at(self.sig_rad,
                      (con.sig_at_src[core], bins[core]), vals[core])
            ring = con.ring_at_src >= 0
            np.add.at(self.sig_ring, con.ring_at_src[ring], vals[ring])
            np.add.at(self.sig_rr,
                      (con.ring_at_src[ring], bins[ring]), vals[ring])

        self.a = self.a + add.reshape(self.grid, self.grid)
        self.age = new_age
        self._clamp()
        self._renorm()

    def beat(self, write_sig=True):
        for _ in range(K.OUTPOUR_TICKS):
            self._outpour_tick()
            self._decay_traps("outpour")
            self._sustain()
        for _ in range(K.AUDIT_TICKS):
            self._decay_traps("audit")
            self._sustain()
        self.last_passed = self.last_rejected = 0
        for _ in range(K.INDRAW_TICKS):
            self._indraw_tick(write_sig=write_sig)
            self._decay_traps("indraw")
            self._sustain()
        self.beats += 1

    def quiet_ticks(self, n):
        """Quiet dynamics only: decay + member sustainment, no strokes."""
        for _ in range(n):
            self._decay_traps("audit")
            self._sustain()

    # ── metrics ──────────────────────────────────────────────────────
    def trap_map(self):
        return self.w > K.TRAP_T

    def defined_count(self):
        return int((self.w > K.TRAP_T).sum())

    def defined_frac(self):
        return float((self.w > K.TRAP_T).mean())

    def act_mass(self):
        return float(self.a.sum())

    def flatness(self):
        """exp(entropy)/N of the activation shape: 1 = flat, ->0 = a point."""
        s = self.a.sum()
        if s <= 0:
            return float("nan")
        p = (self.a / s).ravel()
        p = p[p > 0]
        h = -(p * np.log(p)).sum()
        return float(np.exp(h) / self.n)

    def confidence(self, anchor_mask):
        """Anchor-completion fraction: how much of the deployed skeleton
        has been re-defined by the field. The machine-readable recall
        confidence (probe 12: r ~ +0.40 against true purity)."""
        total = int(anchor_mask.sum())
        if total == 0:
            return 0.0
        return float((self.w > K.TRAP_T)[anchor_mask].mean())


class Field(StrokeEngine):
    """The normalized stage. Thresholds ride the uniform share u = sum/N."""

    normalized = True

    def _u(self):
        s = self.a.sum()
        return (s / self.n) if s > 0 else 0.0

    def th_active(self):
        return K.NORM_ACTIVE_U * self._u()

    def th_relay(self):
        return K.NORM_RELAY_U * self._u()

    def th_dig(self):
        return K.NORM_DIG_U * self._u()

    def th_src(self):
        return K.NORM_SRC_U * self._u()

    def th_quiet(self):
        return K.NORM_QUIET_U * self._u()

    def _renorm(self):
        s = self.a.sum()
        if s > 0:
            self.a /= s

    def stamp_amplitude(self):
        return K.NORM_STAMP_U / self.n

    def wipe(self):
        """Nothing, in the normalized gauge, is flatness — not zero.
        Flat mass has no journey behind it: hop age resets with it."""
        self.w[:] = 0.0
        self.a[:] = 1.0 / self.n
        self.age[:] = 0.0

    def deploy(self, cells, amplitude=None):
        """Additively install cue cells (anchor deployment), then renorm."""
        amp = (K.NORM_CUE_U / self.n) if amplitude is None else amplitude
        for x, y in cells:
            if 0 <= x < self.grid and 0 <= y < self.grid:
                self.a[y, x] += amp
        self._renorm()
