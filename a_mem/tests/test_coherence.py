"""Probe 1 / P0: bounds, NaN, determinism, empty-stays-empty — plus the
library persistence round-trip (acceptance item)."""
import numpy as np

from amem import AbsoluteField, Field, Memory
from amem import constants as K
from conftest import SEED_OFF, place

CELLS = place(SEED_OFF, 4, 4)


def run_beats(engine, n=12):
    engine.stamp(CELLS)
    for _ in range(n):
        engine.beat()
    return engine


def test_bounds_and_nan_absolute():
    e = run_beats(AbsoluteField(seed=1))
    assert (e.a >= 0).all() and (e.a <= 1).all()
    assert (e.w >= 0).all() and (e.w <= 1).all()
    assert not np.isnan(e.a).any() and not np.isnan(e.w).any()
    assert not np.isnan(e.sig).any()


def test_bounds_and_nan_normalized():
    e = run_beats(Field(seed=1))
    assert (e.a >= 0).all() and (e.a <= 1).all()
    assert (e.w >= 0).all() and (e.w <= 1).all()
    assert not np.isnan(e.a).any() and not np.isnan(e.w).any()
    assert not np.isnan(e.sig).any()
    assert np.isclose(e.a.sum(), 1.0)


def test_determinism_under_seed():
    for cls in (AbsoluteField, Field):
        e1 = run_beats(cls(seed=7))
        e2 = run_beats(cls(seed=7))
        assert np.array_equal(e1.a, e2.a)
        assert np.array_equal(e1.w, e2.w)
        assert np.array_equal(e1.sig, e2.sig)


def test_empty_absolute_stays_dead():
    e = AbsoluteField(seed=7)
    for _ in range(6):
        e.beat()
    assert e.act_mass() == 0.0
    assert e.defined_count() == 0
    assert e.sig.sum() == 0.0


def test_flat_normalized_stays_flat():
    """Nothing in the normalized gauge is flatness; beats must not
    manufacture structure out of it."""
    e = Field(seed=7)
    e.wipe()
    for _ in range(6):
        e.beat()
    assert np.isclose(e.flatness(), 1.0)
    assert e.defined_count() == 0
    assert e.sig.sum() == 0.0


def test_library_round_trip(tmp_path):
    store = str(tmp_path / "store")
    mem = Memory(seed=3, path=store)
    a = mem.write(place(SEED_OFF, 3, 3))
    b = mem.write(place(SEED_OFF, 15, 14))
    mem.calibrate()

    mem2 = Memory(seed=3, path=store)
    assert set(mem2.library.mids()) == {a, b}
    for mid in (a, b):
        e1, e2 = mem.library.get(mid), mem2.library.get(mid)
        assert np.allclose(e1.sig, e2.sig)
        assert np.array_equal(e1.anchors, e2.anchors)
        assert np.array_equal(e1.imprint, e2.imprint)
        assert e1.meta["pattern"] == e2.meta["pattern"]
    assert np.allclose(mem.library.flat_sig, mem2.library.flat_sig)

    c = mem2.write(place(SEED_OFF, 3, 14))
    assert c not in (a, b)


def test_forget_removes_entry(tmp_path):
    mem = Memory(seed=3, path=str(tmp_path / "store"))
    a = mem.write(place(SEED_OFF, 3, 3))
    mem.forget(a)
    assert len(mem.library) == 0
    mem2 = Memory(seed=3, path=str(tmp_path / "store"))
    assert len(mem2.library) == 0
