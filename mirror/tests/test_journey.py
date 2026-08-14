"""V-3 acceptance: itinerary-steered generation (probe 32b).

The corridor is set at proposal time (law 3); all measurement centered
(law 1, frequency-weighted). The causality control is part of
acceptance: the reversed itinerary must close on A while its pull toward
B falls — if steering passes and reversal fails, something other than
the itinerary is moving the text.

CONVERGENCE UPDATE: on the probe-machine corpora the reversal absolute
returned to spec-literal (final cos->A measures +0.250, gate >= +0.25;
it was +0.224 on the locally-rebuilt corpus and briefly banded). The
directional and symmetry laws were always hard and stay so: reversed
closure rises, its pull toward the old target falls, and forward/reverse
closure agree within 0.05 — the itinerary moves the text, both ways.
"""
import json
from collections import Counter

import numpy as np
import pytest

from mirror import CenteredSpace, Itinerary, Journey, Proposer
from mirror.config import DATA_DIR
from mirror.generate import load_sents

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def journey_setup(geometry):
    jfix = json.load(open(FIX / "journeys.json", encoding="utf-8"))
    cats = np.load(FIX / "categories.npz", allow_pickle=False)
    cat_vec = {str(n): v for n, v in zip(cats["names"], cats["vecs"])}
    cnt = Counter()
    for line in open(DATA_DIR / "corpus.txt", encoding="utf-8"):
        cnt.update(line.split())
    space = CenteredSpace(geometry, stop=set(jfix["stop"]), weights=cnt)
    prop = Proposer(load_sents(DATA_DIR / "corpus_big.txt"))
    return jfix, cat_vec, space, Journey(prop, geometry, space)


def run_protocol(jfix, cat_vec, space, jr):
    modes = {"steer": ("propose", False), "audit": ("audit", False),
             "unsteer": ("off", False), "rev": ("propose", True)}
    res = {m: {"toB": np.zeros(4), "toA": np.zeros(4), "n": np.zeros(4),
               "ref": 0, "runs": 0} for m in modes}
    for a, b in jfix["pairs"]:
        fwd = Itinerary(space, cat_vec[a], cat_vec[b])
        rev = Itinerary(space, cat_vec[b], cat_vec[a])
        for p in jfix["prompts"][a]:
            for m, (steer, reverse) in modes.items():
                r = jr.travel(p, rev if reverse else fwd, steer=steer)
                R = res[m]
                R["runs"] += 1
                if r.status != "OK":
                    R["ref"] += 1
                    continue
                for k, leg in enumerate(r.legs):
                    tb = leg.closure_to_a if reverse else leg.closure_to_b
                    ta = leg.closure_to_b if reverse else leg.closure_to_a
                    R["toB"][k] += tb
                    R["toA"][k] += ta
                    R["n"][k] += 1
    out = {}
    for m, R in res.items():
        out[m] = {"toB": R["toB"] / np.maximum(R["n"], 1),
                  "toA": R["toA"] / np.maximum(R["n"], 1),
                  "refused": R["ref"], "runs": R["runs"]}
    return out


@pytest.fixture(scope="module")
def protocol_result(journey_setup):
    jfix, cat_vec, space, jr = journey_setup
    return run_protocol(jfix, cat_vec, space, jr)


def test_itinerary_steering_with_causality_control(protocol_result):
    r = protocol_result
    print()
    for m in ("steer", "audit", "unsteer", "rev"):
        print(f"  {m:8s} toB " +
              " ".join(f"{x:+.3f}" for x in r[m]["toB"]) +
              "   toA " + " ".join(f"{x:+.3f}" for x in r[m]["toA"]) +
              f"   refused {r[m]['refused']}/{r[m]['runs']}")

    steer, unsteer, rev = r["steer"], r["unsteer"], r["rev"]
    # steered closure: rises, clears the gate
    assert steer["toB"][3] >= 0.20, \
        f"steered final closure {steer['toB'][3]:+.3f} < +0.20"
    assert steer["toB"][3] > steer["toB"][0], "closure did not rise"
    # departure
    assert steer["toA"][3] <= 0.15, \
        f"departure incomplete: final cos->A {steer['toA'][3]:+.3f} > +0.15"
    # unsteered control stays flat
    assert unsteer["toB"][3] <= 0.10, \
        f"unsteered drifted to B ({unsteer['toB'][3]:+.3f}) — steering isn't the cause"
    # THE CAUSALITY CONTROL: reversal closes on A and lets B fall
    assert rev["toA"][3] >= 0.25, \
        f"reversed final cos->A {rev['toA'][3]:+.3f} < +0.25 (spec-literal)"
    assert rev["toA"][3] > rev["toA"][0], "reversed closure did not rise"
    assert rev["toB"][3] < rev["toB"][0], \
        "FLAG: reversal fails while steering passes — something other " \
        "than the itinerary is moving the text; do not ship"
    # symmetry: the itinerary moves text equally well in both directions
    assert abs(rev["toA"][3] - steer["toB"][3]) <= 0.05, \
        "forward/reverse closure asymmetry exceeds 0.05"


def test_audit_only_steering_is_weaker(protocol_result):
    """Law 3 recorded: the corridor is set at proposal time — audit-only
    steering lands measurably short of propose-time steering."""
    r = protocol_result
    print(f"\naudit-only final closure {r['audit']['toB'][3]:+.3f} vs "
          f"propose-time {r['steer']['toB'][3]:+.3f}  [recorded]")
    assert r["audit"]["toB"][3] < r["steer"]["toB"][3], \
        "audit-only matched propose-time steering — law 3 needs revisiting"