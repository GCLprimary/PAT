"""S-0 batteries (grades forecasts S1 and S2).

S1 — the organs generalize off language: recognition of known
patterns under channel noise >= 95%, refusal of unknown patterns
>= 98%, confabulations == 0 (the honesty invariant crosses worlds
unchanged).

S2 — NO THRESHOLD TRANSFERS (the forecast's strongest claim, 95%):
the sensor theta is DERIVED from the measured window on sensor data
(sweep_theta's provenance: imposter ceiling vs noisy-self p5), the
window must be OPEN, theta strictly inside it, and the language
constants (0.98 shape, 0.77 phon) must NOT have been imported. A
theta that equals a language constant here would mean somebody
transferred instead of measuring — the test fails on principle.
"""
import tempfile
from pathlib import Path

import pytest

from amem.api import Memory
from mirror.loop import THETA_DEFAULT
from mirror.gate import THETA_PHON
from world import (SensorMemory, SensorWorld, sweep_theta, N_KNOWN)


@pytest.fixture(scope="module")
def world():
    w = SensorWorld(seed=17)
    w.populate()
    return w


@pytest.fixture(scope="module")
def swept(world):
    return sweep_theta(world)


@pytest.fixture(scope="module")
def pipeline(world, swept, tmp_path_factory):
    theta, _, _ = swept
    mem = Memory(seed=3,
                 path=str(tmp_path_factory.mktemp("sensor") / "store"),
                 autosave=False)
    return SensorMemory(world, mem, theta)


def test_s2_theta_is_derived_not_transferred(swept):
    theta, ceiling, p5 = swept
    print(f"\nsensor window: imposter ceiling {ceiling:.4f} < "
          f"noisy-self p5 {p5:.4f}; theta = {theta} (derived)")
    assert ceiling < p5, \
        "the sensor window CLOSED — noise level vs pattern length " \
        "needs re-measuring before any threshold exists"
    assert ceiling < theta < p5
    assert abs(theta - THETA_DEFAULT) > 1e-9 and \
        abs(theta - THETA_PHON) > 1e-9, \
        "the sensor theta equals a LANGUAGE constant — a threshold " \
        "transferred instead of being measured (S2 broken)"


def test_s1_recognition(world, pipeline):
    ok = n = 0
    for name, pattern in world.known.items():
        for _ in range(5):
            got = pipeline.recognize(world.noisy(pattern))
            ok += int(got == name)
            n += 1
    print(f"\nrecognition under noise: {ok}/{n} = {ok/n*100:.1f}%")
    assert n == N_KNOWN * 5
    assert ok / n >= 0.95, f"recognition {ok/n:.3f} < 95%"


def test_s1_refusal_and_zero_confabs(world, pipeline):
    refused = confabs = 0
    n = 200
    for _ in range(n):
        got = pipeline.recognize(world.unknown_pattern())
        if got is None:
            refused += 1
        else:
            confabs += 1
    print(f"\nunknown patterns: {refused}/{n} refused, "
          f"{confabs} confabulations")
    assert refused / n >= 0.98, f"refusal {refused/n:.3f} < 98%"
    assert confabs == 0, \
        f"{confabs} confabulations — THE INVARIANT BROKE CROSSING WORLDS"
