"""Probe 9 / K2 and the homeostatic budget.

Law 1 verified as a test: residency = 1. Two memories resident on one
stage blend irrecoverably (measured margin +0.94 at k=1 collapsing to
+0.005 at k=2). The defined-fraction budget holds its 8-14% band across
the violence and decay ranges probed.
"""
import numpy as np

from amem import Field, cosine
from amem import constants as K
from conftest import D, V, half_cells


def resident_margin(k, bank, seed=5):
    """Probe-9 K2: imprint k patterns into ONE field, cue each with
    half-anchors, margin = own - mean(others)."""
    rng = np.random.default_rng(7)
    names = list(bank)[:k]
    e = Field(seed=seed, violence=V, decay=D)
    for n in names:
        e.stamp(bank[n]["cells"])
        for _ in range(4):
            e.beat(write_sig=False)
    margins = []
    for n in names:
        r = Field(seed=seed + 1, violence=V, decay=D)
        r.a = e.a.copy()
        r.w = e.w.copy()
        r.deploy(half_cells(bank[n]["anchors"], rng))
        for _ in range(3):
            r.beat(write_sig=False)
        own = cosine(r.w, bank[n]["orig"])
        others = (np.mean([cosine(r.w, bank[m]["orig"]) for m in names if m != n])
                  if k > 1 else 0.0)
        margins.append(own - others)
    return float(np.mean(margins))


def test_residency_one_blend_collapse(twelve_bank):
    names, lib, _ = twelve_bank
    m1 = resident_margin(1, lib)
    m2 = resident_margin(2, lib)
    # law 1: a single resident is sharply recallable...
    assert m1 >= 0.8, f"k=1 resident margin {m1:+.3f} < +0.8"
    # ...and a second resident destroys the stage's discriminability
    assert m2 <= 0.15, f"k=2 resident margin {m2:+.3f} — blending is gone?!"
    assert m2 <= m1 / 4


def _accuracy(names, lib, probes, variant):
    ok = tot = 0
    for name in names:
        for p in probes[name]:
            pick = max(names, key=lambda n: cosine(p[variant], lib[n][variant]))
            ok += int(pick == name)
            tot += 1
    return ok / tot


def test_radius_channel_capacity_k24(twentyfour_bank):
    """W-1 acceptance (D-2): the radius channel carries >= 88% at k = 24
    (probe 13 measured 90%; legacy angular code baseline 83%)."""
    names, lib, probes = twentyfour_bank
    acc_radius = _accuracy(names, lib, probes, "v2")
    acc_legacy = _accuracy(names, lib, probes, "v0")
    assert acc_radius >= 0.88, f"radius k=24 accuracy {acc_radius:.2f} < 0.88"
    # the channel must actually be the mechanism: radius beats angular
    assert acc_radius > acc_legacy, \
        f"radius {acc_radius:.2f} <= legacy {acc_legacy:.2f}"


def test_combo_mode_small_library(twentyfour_bank):
    """D-2: ring x radius combo is the optional small-library mode —
    probe 14 measured 100% through k = 16 (dilutes to 88% at 24)."""
    names, lib, probes = twentyfour_bank
    acc16 = _accuracy(names[:16], lib, probes, "v3")
    assert acc16 >= 0.95, f"combo k=16 accuracy {acc16:.2f} < 0.95"


def test_homeostatic_budget_band(three_lib):
    """Defined fraction stays in the 8-14% band across the probed
    violence x decay ranges (baseline ~10-12%)."""
    cells = three_lib["NW"]["cells"]
    for violence, decay in [(0.10, 0.03), (0.45, 0.05), (0.70, 0.09)]:
        e = Field(seed=11, violence=violence, decay=decay)
        e.stamp(cells)
        for _ in range(K.IMPRINT_BEATS):
            e.beat()
        frac = e.defined_frac()
        assert 0.08 <= frac <= 0.14, \
            f"budget {frac:.3f} outside [0.08, 0.14] at v={violence}, d={decay}"
