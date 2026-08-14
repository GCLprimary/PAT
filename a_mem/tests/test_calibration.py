"""Law 4: calibration is an absolute-gauge operation.

The normalized gauge cannot see a plenum — uniformity sits below its own
relative thresholds, so its flat-field signature is exactly zero. The
absolute engine sees the plenum and returns the instrument's self-
portrait: a ring with a structurally dark center. The portrait is stored;
it is never superposed onto the stage.
"""
import numpy as np

from amem import AbsoluteField, Field, Memory
from amem import constants as K
from conftest import SEED_OFF, place


def test_normalized_gauge_is_blind_to_the_plenum():
    e = Field(seed=1)
    e.wipe()                       # a == 1/N everywhere
    for _ in range(K.INDRAW_TICKS):
        e._indraw_tick(write_sig=True)
        e._renorm()
    assert np.all(e.sig == 0.0), "normalized gauge saw the plenum?!"


def test_absolute_flat_portrait_is_ring_with_dark_center():
    portrait = AbsoluteField(seed=1).calibrate()
    ring = np.delete(portrait, 4)
    assert portrait[4] == 0.0, "core center must be structurally dark"
    assert np.all(ring > 0.0), "every live core cell must collect mass"
    # the plenum is isotropic; the portrait must be nearly so
    assert ring.max() / ring.min() <= 1.05


def test_calibration_is_deterministic_geometry():
    p1 = AbsoluteField(seed=1).calibrate()
    p2 = AbsoluteField(seed=999).calibrate()
    assert np.array_equal(p1, p2), "the self-portrait is geometry, not noise"


def test_memory_calibrate_stores_never_paints():
    mem = Memory(seed=5, path=None)
    mem.write(place(SEED_OFF, 3, 3))
    a_before = mem.stage.a.copy()
    w_before = mem.stage.w.copy()
    portrait = mem.calibrate()
    # stored...
    assert mem.library.flat_sig is not None
    assert np.array_equal(mem.library.flat_sig, portrait)
    assert mem.stats()["calibrated"]
    # ...never superposed onto the stage
    assert np.array_equal(mem.stage.a, a_before)
    assert np.array_equal(mem.stage.w, w_before)
