"""Probes 10-12: the stage as a clock.

Law 2 verified as a test: hot eviction MUST fail; page-turn alternation
runs 100% correct tenancy at dwell 1 for a low-overlap pair; the hardest
measured pair (overlap ~0.62) needs dwell 2. Internal confidence
(anchor-completion) correlates with true purity (baseline r ~ +0.40).
"""
import numpy as np

from amem import Field, Memory, cosine, page_turn
from amem import constants as K
from conftest import (D, SEED_OFF, V, half_cells, imprint, make_anchors,
                      place)


def build_identity(cx, cy):
    cells = place(SEED_OFF, cx, cy)
    sig, orig = imprint(cells)
    return {"cells": cells, "anchors": make_anchors(cells), "orig": orig}


def stage_holder(engine, lib):
    scores = {n: cosine(engine.w, lib[n]["orig"]) for n in lib}
    return max(scores, key=scores.get)


def alternation_run(lib, rng, period, total=12, page_turned=True, seed=5):
    e = Field(seed=seed, violence=V, decay=D)
    e.wipe()
    tenants = list(lib)[:2]
    correct = 0
    t = 0
    while t < total:
        target = tenants[(t // period) % 2]
        if page_turned:
            page_turn(e)
        e.deploy(half_cells(lib[target]["anchors"], rng))
        for _ in range(period):
            e.beat(write_sig=False)
            correct += int(stage_holder(e, lib) == target)
            t += 1
            if t >= total:
                break
    return correct / total


def test_page_turn_alternation_dwell1_is_perfect():
    lib = {"A": build_identity(3, 3), "B": build_identity(15, 14)}
    overlap = cosine(lib["A"]["orig"], lib["B"]["orig"])
    assert overlap <= 0.47, f"pair overlap {overlap:.2f} not in the easy band"
    acc = alternation_run(lib, np.random.default_rng(7), period=1)
    assert acc == 1.0, f"page-turned dwell-1 tenancy {acc:.0%} != 100%"


def test_hot_swap_must_fail():
    """Law 2: without a page-turn the incumbent squats. This test asserts
    the FAILURE of hot eviction — if hot swapping ever starts working,
    the substrate has changed and the design must be revisited."""
    lib = {"A": build_identity(3, 3), "B": build_identity(15, 14)}
    rng = np.random.default_rng(7)

    # hot alternation: same drive, no page-turn
    acc_hot = alternation_run(lib, rng, period=1, page_turned=False)
    assert acc_hot <= 0.6, f"hot alternation {acc_hot:.0%} — eviction worked?!"

    # direct eviction attempt: A resident, cue B, 6 beats — B never lands
    e = Field(seed=9, violence=V, decay=D)
    e.wipe()
    e.deploy(half_cells(lib["A"]["anchors"], rng))
    for _ in range(4):
        e.beat(write_sig=False)
    assert stage_holder(e, lib) == "A"
    e.deploy(half_cells(lib["B"]["anchors"], rng))
    for _ in range(6):
        e.beat(write_sig=False)
        assert stage_holder(e, lib) == "A", "hot eviction succeeded?!"


def test_hard_pair_needs_dwell2():
    """Probe 12 frontier: the hardest measured pair (overlap ~0.62) is
    unreliable at dwell 1 and recovers at dwell 2. Aggregated over seeds
    because single runs sit on the frontier by construction (measured:
    dwell 1 ~77%, dwell 2 ~90-100%)."""
    lib = {"A": build_identity(5, 5), "B": build_identity(8, 8)}
    overlap = cosine(lib["A"]["orig"], lib["B"]["orig"])
    assert 0.5 <= overlap <= 0.75, \
        f"hard pair overlap {overlap:.2f} left the measured band"

    def frontier(dwell, seed, rng_seed):
        rng = np.random.default_rng(rng_seed)
        e = Field(seed=seed, violence=V, decay=D)
        ok = 0
        for t in range(10):
            target = ["A", "B"][t % 2]
            page_turn(e)
            e.deploy(half_cells(lib[target]["anchors"], rng))
            for _ in range(dwell):
                e.beat(write_sig=False)
            ok += int(stage_holder(e, lib) == target)
        return ok / 10

    seeds = range(5, 11)
    acc1 = np.mean([frontier(1, s, s * 3) for s in seeds])
    acc2 = np.mean([frontier(2, s, s * 3) for s in seeds])
    assert acc1 <= 0.9, f"dwell 1 on the hard pair: {acc1:.0%} — not hard anymore?"
    assert acc2 >= 0.85, f"dwell 2 on the hard pair: {acc2:.0%} < 85%"
    assert acc2 > acc1, "dwell 2 must buy tenancy on the hard pair"


def test_confidence_tracks_purity():
    """Probe 12 / D2: anchor-completion confidence vs true purity,
    baseline r ~ +0.40; assert r >= +0.25."""
    pairs = [((3, 3), (15, 14)), ((3, 3), (11, 11)), ((4, 4), (9, 9))]
    xs, ys = [], []
    rng = np.random.default_rng(7)
    for p1, p2 in pairs:
        lib = {"A": build_identity(*p1), "B": build_identity(*p2)}
        e = Field(seed=9, violence=V, decay=D)
        for t in range(8):
            target = ["A", "B"][t % 2]
            other = "B" if target == "A" else "A"
            page_turn(e)
            e.deploy(half_cells(lib[target]["anchors"], rng))
            for _ in range(3):
                e.beat(write_sig=False)
                xs.append(e.confidence(lib[target]["anchors"]))
                ys.append(cosine(e.w, lib[target]["orig"]) -
                          cosine(e.w, lib[other]["orig"]))
    r = float(np.corrcoef(xs, ys)[0, 1])
    assert r >= 0.25, f"confidence validity r = {r:+.3f} < +0.25"


def test_sequence_api_fixed_and_adaptive():
    mem = Memory(seed=17, path=None)
    a = mem.write(place(SEED_OFF, 3, 3))
    b = mem.write(place(SEED_OFF, 15, 14))

    seq = mem.sequence([a, b, a, b], dwell=1)
    assert [r.identity for r in seq] == [a, b, a, b]
    assert all(r.target == r.identity for r in seq)
    assert all(r.dwell == 1 for r in seq)

    seq = mem.sequence([a, b, a], dwell="adaptive")
    assert [r.identity for r in seq] == [a, b, a]
    assert all(1 <= r.dwell <= K.ADAPTIVE_CAP for r in seq)
