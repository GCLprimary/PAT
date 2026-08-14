"""Exact-arithmetic alignment harness.

Everything that decides WHETHER two cells are aligned members lives here,
and it is integer-only: distances are compared as squared integers against
the canonical families. No float arithmetic appears in this module
(enforced by tests). Mass dynamics belong to the engines, not here.
"""
import math

import numpy as np

from .constants import FAMILY_INT, FAMILY_QUAD


def offsets_for(d2list):
    """All (dx, dy) integer offsets whose squared distance is in d2list."""
    d2set = set(int(d) for d in d2list)
    r = math.isqrt(max(d2set))
    if r * r < max(d2set):
        r += 1
    out = []
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if (dx or dy) and dx * dx + dy * dy in d2set:
                out.append((dx, dy))
    return out


OFF_INT = tuple(offsets_for(FAMILY_INT))
OFF_QUAD = tuple(offsets_for(FAMILY_QUAD))
OFF_ALL = OFF_INT + OFF_QUAD


def is_member_offset(dx, dy):
    """Alignment certification for a single offset: squared-int compare."""
    d2 = dx * dx + dy * dy
    return d2 in FAMILY_INT or d2 in FAMILY_QUAD


def shifted(arr, dx, dy, grid):
    """Value at (x+dx, y+dy) for each cell; zero outside the lattice."""
    out = np.zeros_like(arr)
    xs = slice(max(0, -dx), grid - max(0, dx))
    ys = slice(max(0, -dy), grid - max(0, dy))
    xs2 = slice(max(0, dx), grid - max(0, -dx))
    ys2 = slice(max(0, dy), grid - max(0, -dy))
    out[ys, xs] = arr[ys2, xs2]
    return out


def member_pair_count(active, grid):
    """Number of certified member pairs among active cells (each pair once).

    Uses the half-plane (dy > 0, or dy == 0 and dx > 0) to deduplicate.
    """
    count = 0
    act = active.astype(np.int64)
    for dx, dy in OFF_ALL:
        if dy < 0 or (dy == 0 and dx < 0):
            continue
        count += int(np.sum(act & shifted(act, dx, dy, grid)))
    return count


def certify_pattern(cells):
    """Per-cell member degree of a set of (x, y) cells, exact arithmetic.

    Returns {cell: number of certified member partners within the set}.
    """
    cells = list(cells)
    degrees = {}
    for x, y in cells:
        d = 0
        for x2, y2 in cells:
            if (x, y) != (x2, y2) and is_member_offset(x2 - x, y2 - y):
                d += 1
        degrees[(x, y)] = d
    return degrees
