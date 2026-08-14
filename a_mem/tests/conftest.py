"""Shared probe-protocol helpers.

These replicate the exact write/recall protocols of probe suites 1-12 so
the measured numbers become regression baselines. Statistical baselines
carry +-10% slack; the design laws are hard assertions.
"""
import numpy as np
import pytest

from amem import AbsoluteField, Field, cosine
from amem import constants as K

V, D = K.VIOLENCE, K.DECAY

SEED_OFF = K.SEED_CONSTELLATION
LINE_OFF = ((0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3))


def place(offsets, cx, cy):
    """Offsets -> absolute cells at (cx, cy)."""
    return [(cx + dx, cy + dy) for dx, dy in offsets]


def make_anchors(cells, seed=21):
    """Probe stage-1 anchor write: absolute gauge, quiet dynamics."""
    e = AbsoluteField(seed=seed, violence=0.0, decay=D)
    return e.write_anchors(cells)


def imprint(cells, seed=42):
    """Probe stage-2 normalized imprint: 8 beats, collect signature.

    Returns (sig, orig trap map as float mask).
    """
    e = Field(seed=seed, violence=V, decay=D)
    e.stamp(cells)
    for _ in range(K.IMPRINT_BEATS):
        e.beat()
    return e.sig.copy(), e.trap_map().astype(float)


def imprint_codes(cells, seed=42):
    """Imprint collecting every core code gauge (probe 13/14 protocol).

    Returns dict with v0 (9), v2 (54 radius), v3 (150 combo), orig.
    """
    e = Field(seed=seed, violence=V, decay=D)
    e.stamp(cells)
    for _ in range(K.IMPRINT_BEATS):
        e.beat()
    return {"v0": e.sig.copy(), "v2": e.sig_rad.ravel().copy(),
            "v3": e.sig_rr.ravel().copy(), "orig": e.trap_map().astype(float)}


def half_cells(anchor_mask, rng, fraction=0.5):
    cells = np.argwhere(anchor_mask)
    k = max(1, int(len(cells) * fraction))
    pick = cells[rng.choice(len(cells), size=k, replace=False)]
    return [(int(x), int(y)) for y, x in pick]


def rebuild(deploy, seed=5, beats=K.REBUILD_BEATS):
    """Wipe-to-flat, deploy cue cells, complete. Returns the field."""
    e = Field(seed=seed, violence=V, decay=D)
    e.wipe()
    e.deploy(deploy)
    for _ in range(beats):
        e.beat(write_sig=False)
    return e


def confusion_margin(builds, origs, names):
    """mean(diagonal) - mean(off-diagonal) of the cosine confusion matrix."""
    m = np.array([[cosine(builds[n1], origs[n2]) for n2 in names]
                  for n1 in names])
    diag = float(np.mean(np.diag(m)))
    off = float((m.sum() - np.trace(m)) / (m.size - len(names)))
    return diag - off, m


THREE_PATTERNS = {
    "NW": place(SEED_OFF, 3, 3),
    "SE": place(SEED_OFF, 15, 14),
    "line": place(LINE_OFF, 12, 3),
}


@pytest.fixture(scope="session")
def three_lib():
    """The canonical 3-identity library (probes 5-8, 10-11)."""
    lib = {}
    for name, cells in THREE_PATTERNS.items():
        sig, orig = imprint(cells)
        lib[name] = {"cells": cells, "anchors": make_anchors(cells),
                     "sig": sig, "orig": orig}
    return lib


@pytest.fixture(scope="session")
def twentyfour_bank():
    """The probe-13 capacity bank: 16 constellations + 8 lines, imprinted
    with all core code gauges (library seed 42, probes 77 & 101)."""
    bank = []
    pos_c = [(3, 3), (15, 14), (3, 14), (14, 3), (9, 3), (3, 9), (14, 9),
             (9, 14), (6, 6), (12, 12), (6, 12), (12, 6), (9, 9), (3, 6),
             (15, 6), (6, 15)]
    for i, (cx, cy) in enumerate(pos_c):
        bank.append((f"C{i:02d}", place(SEED_OFF, cx, cy)))
    pos_l = [(2, 2), (11, 16), (2, 16), (11, 2), (2, 9), (11, 9), (6, 4),
             (6, 13)]
    for i, (cx, cy) in enumerate(pos_l):
        bank.append((f"L{i}", place(LINE_OFF, cx, cy)))
    lib = {name: imprint_codes(cells) for name, cells in bank}
    probes = {name: [imprint_codes(cells, seed=s) for s in (77, 101)]
              for name, cells in bank}
    return [b[0] for b in bank], lib, probes


@pytest.fixture(scope="session")
def twelve_bank():
    """The probe-9 capacity bank: 8 constellations + 4 lines."""
    bank = []
    for i, (cx, cy) in enumerate([(3, 3), (15, 14), (3, 14), (14, 3),
                                  (9, 3), (3, 9), (14, 9), (9, 14)]):
        bank.append((f"C{i}", place(SEED_OFF, cx, cy)))
    for i, (cx, cy) in enumerate([(2, 2), (11, 16), (2, 16), (11, 2)]):
        bank.append((f"L{i}", place(LINE_OFF, cx, cy)))
    lib = {}
    for name, cells in bank:
        sig, orig = imprint(cells)
        lib[name] = {"cells": cells, "sig": sig, "orig": orig,
                     "anchors": make_anchors(cells)}
    probes = {name: [imprint(rec["cells"], seed=s)[0] for s in (77, 101)]
              for name, rec in lib.items()}
    return [b[0] for b in bank], lib, probes
