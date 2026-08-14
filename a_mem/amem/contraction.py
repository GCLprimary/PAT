"""The parity-sieved inward contraction — pure integer geometry.

The contraction maps each non-center cell z = (rx, ry) to z / (1 + i):
    target = ((rx + ry) // 2, (ry - rx) // 2)
defined only when (rx + ry) is even (the parity sieve). Odd-parity cells
are rejected — on a saturated lattice exactly half of the 528 non-center
cells pass and half strand (the 264/264 theorem, tests/test_sieve.py).

Everything here is decision geometry: parity checks and integer division
after the parity check. No float arithmetic appears in this module.
Mass transport (what fraction of activation rides the map) is dynamics
and lives in the engines.
"""
from functools import lru_cache

import numpy as np


class Contraction:
    """Precomputed inward map and signature-collection indices for a grid."""

    def __init__(self, grid):
        if grid % 2 == 0 or grid < 7:
            raise ValueError("grid must be odd and >= 7")
        self.grid = grid
        c = (grid - 1) // 2
        self.center = c

        tx = np.full((grid, grid), -1, dtype=np.int64)
        ty = np.full((grid, grid), -1, dtype=np.int64)
        sig_index = np.full((grid, grid), -1, dtype=np.int64)
        ring_index = np.full((grid, grid), -1, dtype=np.int64)
        for y in range(grid):
            for x in range(grid):
                rx, ry = x - c, y - c
                if rx == 0 and ry == 0:
                    continue
                if (rx + ry) % 2 != 0:
                    continue
                gx = c + (rx + ry) // 2
                gy = c + (ry - rx) // 2
                if 0 <= gx < grid and 0 <= gy < grid:
                    tx[y, x], ty[y, x] = gx, gy
                    if abs(gx - c) <= 1 and abs(gy - c) <= 1:
                        sig_index[y, x] = (gy - c + 1) * 3 + (gx - c + 1)
                    if abs(gx - c) <= 2 and abs(gy - c) <= 2:
                        ring_index[y, x] = (gy - c + 2) * 5 + (gx - c + 2)

        self.parity_ok = tx >= 0
        self.is_center = np.zeros((grid, grid), dtype=bool)
        self.is_center[c, c] = True

        # flat scatter indices for vectorized transport
        src = np.argwhere(self.parity_ok)                    # (k, 2) as (y, x)
        self.src_flat = src[:, 0] * grid + src[:, 1]
        self.dst_flat = ty[src[:, 0], src[:, 1]] * grid + tx[src[:, 0], src[:, 1]]
        self.sig_at_src = sig_index[src[:, 0], src[:, 1]]    # -1 if not core-bound
        self.ring_at_src = ring_index[src[:, 0], src[:, 1]]  # -1 if not ring-bound
        self.tx, self.ty = tx, ty

        # the inward map z -> z // (1 + i) is injective: every destination
        # receives from at most one source. The hop-age blend (radius
        # channel) relies on this; certify it at construction.
        if len(set(int(d) for d in self.dst_flat)) != len(self.dst_flat):
            raise AssertionError("contraction map lost injectivity")

    def sieve(self, part):
        """Split a participation mask into (passed, rejected) by parity."""
        passed = part & self.parity_ok & ~self.is_center
        rejected = part & ~self.parity_ok & ~self.is_center
        return passed, rejected

    def transport(self, carried, sig, write_sig):
        """Scatter carried mass one hop inward; collect core arrivals in sig.

        `carried` is a full-grid array that is zero outside passed cells.
        Returns the arrival array (same shape). Mutates sig in place when
        write_sig is set.
        """
        flat = carried.ravel()
        vals = flat[self.src_flat]
        add = np.zeros(self.grid * self.grid, dtype=carried.dtype)
        np.add.at(add, self.dst_flat, vals)
        if write_sig:
            core_bound = self.sig_at_src >= 0
            np.add.at(sig, self.sig_at_src[core_bound], vals[core_bound])
        return add.reshape(self.grid, self.grid)

    def journey_fate(self):
        """Pure-geometry fate of each cell: 0 center, 1 reaches core, 2 strands."""
        grid, c = self.grid, self.center
        fate = np.zeros((grid, grid), dtype=np.int64)
        for y in range(grid):
            for x in range(grid):
                rx, ry = x - c, y - c
                if rx == 0 and ry == 0:
                    continue
                while True:
                    if abs(rx) <= 1 and abs(ry) <= 1:
                        fate[y, x] = 1
                        break
                    if (rx + ry) % 2 != 0:
                        fate[y, x] = 2
                        break
                    rx, ry = (rx + ry) // 2, (ry - rx) // 2
        return fate


@lru_cache(maxsize=None)
def contraction_for(grid):
    return Contraction(grid)
