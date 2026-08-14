"""V5 composition: normalized gauge + inverse-spiral decoder.

The decoder replaces the center-blob core glow: each core cell's stored
signature value is emitted along that cell's outward orbit under
multiplication by (1+i) -- retracing the contraction backward, so the
-45-degrees-per-hop twist is undone by construction. Radius is left
unresolved (the signature never stored hop counts); the field's own
dynamics -- anchors, audit, members -- select where along the ray the
content sticks.
"""
import numpy as np
from gauge import Gauge, GRID, N, C

# outward orbits of the 8 live core cells under z -> z*(1+i)
CORE_ORBITS = {}
for ry in (-1, 0, 1):
    for rx in (-1, 0, 1):
        if rx == 0 and ry == 0:
            continue
        orbit = []
        x, y = rx, ry
        while True:
            x, y = x - y, x + y
            gx, gy = C + x, C + y
            if not (0 <= gx < GRID and 0 <= gy < GRID):
                break
            orbit.append((gx, gy))
            if len(orbit) > 12:
                break
        CORE_ORBITS[(ry + 1) * 3 + (rx + 1)] = orbit

class GaugeV5(Gauge):
    def __init__(self, seed=0, violence=0.45, decay=0.05, decode_amp=0.06):
        super().__init__(True, seed=seed, violence=violence, decay=decay)
        self.decode_amp = decode_amp

    def _outpour_tick(self):
        # inverse-spiral decode instead of center blob
        tot = self.sig.sum()
        if tot > 0 and self.decode_amp > 0:
            S = self.a.sum()
            budget = self.decode_amp * (S if S > 0 else 1.0)
            for k, orbit in CORE_ORBITS.items():
                q = self.sig[k] / tot
                if q <= 0 or not orbit:
                    continue
                share = budget * q / len(orbit)
                for gx, gy in orbit:
                    self.a[gy, gx] += share
        # anchored / strong cells spray locally (unchanged, proportional)
        src = np.where((self.w >= 0.25) | (self.a >= self.th_src()), self.a, 0.0)
        amp = self.violence
        add = np.zeros_like(self.a)
        from gauge import shifted, BURST_R
        for dy in range(-BURST_R, BURST_R + 1):
            for dx in range(-BURST_R, BURST_R + 1):
                if dx == 0 and dy == 0:
                    continue
                gate = self.rng.random((GRID, GRID)) < 0.5
                add += shifted(src, -dx, -dy) * gate * amp * 0.3 * \
                       self.rng.random((GRID, GRID))
        self.a = self.a + add
        self._renorm()
