"""The anchor writer: absolute-gauge engine.

Fixed thresholds, a real zero, no renormalization. This is the gauge that
writes the durable per-memory skeletons (anchors) via quiet dynamics —
decay + member sustainment, no strokes — until traps define. It is also
the only gauge that can see a plenum, which makes calibration (the flat-
field self-portrait) an absolute-gauge operation by law 4.
"""
import numpy as np

from . import constants as K
from .field import StrokeEngine


class AbsoluteField(StrokeEngine):
    """Absolute gauge: fixed rulers, nothing = zero."""

    normalized = False

    def _u(self):
        return 1.0

    def th_active(self):
        return K.ABS_ACTIVE

    def th_relay(self):
        return K.ABS_RELAY

    def th_dig(self):
        return K.ABS_DIG

    def th_src(self):
        return K.ABS_SRC

    def th_quiet(self):
        return K.ABS_QUIET

    def _floor(self):
        self.a[self.a < K.ABS_FLOOR] = 0.0

    def _clamp(self):
        np.minimum(self.a, 1.0, out=self.a)

    def stamp_amplitude(self):
        return K.ABS_STAMP

    def wipe(self):
        """Nothing, in the absolute gauge, is zero."""
        self.w[:] = 0.0
        self.a[:] = 0.0
        self.age[:] = 0.0

    # ── the two absolute-gauge jobs ──────────────────────────────────
    def write_anchors(self, cells, ticks=K.ANCHOR_TICKS):
        """Quiet-dynamics anchor write: stamp bare activation (no trap
        head start), let decay + member sustainment run until the aligned
        survivors dig their own traps. Returns the anchor mask (w > TRAP_T).
        """
        self.reset()
        self.stamp(cells, w0=0.0)
        self.quiet_ticks(ticks)
        return self.trap_map().copy()

    def calibrate(self, ticks=K.INDRAW_TICKS):
        """Flat-field self-portrait: saturate the lattice uniformly and run
        pure indraw. What the signature collects is the instrument's own
        geometry (a ring with a structurally dark center), not a memory.
        The result is stored by the library and never superposed onto the
        stage (law 4).
        """
        self.reset()
        self.a[:] = 1.0
        for _ in range(ticks):
            self._indraw_tick(write_sig=True)
        portrait = self.sig.copy()
        self.reset()
        return portrait
