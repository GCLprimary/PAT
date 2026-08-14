"""R-1 acceptance (probes 36, 36b): the linear organ.

Irrational for identity, rational for rhythm: the √2 ruler orders
exactly and never repeats (Weyl-blind to period); the 5:4 ruler finds
the hidden 20-cycle at an order of magnitude above noise. Exactness
extends to Z[√2]: no float is ever evaluated in a stamp or phase
decision.
"""
import doctest
import json
from decimal import Decimal, getcontext

import numpy as np
import pytest

import mirror.rulers as rulers
from mirror import PhaseRuler, Stamp, sqrt2_concentration
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


def test_doctests_value_never_evaluated():
    failures, _ = doctest.testmod(rulers)
    assert failures == 0


def test_stamp_ordering_exact_at_1e6():
    prev = Stamp.at(0)
    for i in range(1, 1_000_001, 1):
        cur = Stamp.at(i)
        assert prev < cur
        prev = cur


def test_comparator_agrees_with_50_digit_decimal():
    """Independent ground truth: 10^4 random mixed-sign pairs checked
    against 50-digit decimal arithmetic."""
    getcontext().prec = 50
    root2 = Decimal(2).sqrt()
    rng = np.random.default_rng(11)
    for _ in range(10_000):
        m1, n1, m2, n2 = (int(x) for x in rng.integers(-10**9, 10**9, 4))
        exact = Stamp(m1, n1) < Stamp(m2, n2)
        dec = (Decimal(m1) + Decimal(n1) * root2 <
               Decimal(m2) + Decimal(n2) * root2)
        assert exact == dec, f"comparator broke at {(m1, n1, m2, n2)}"


def test_hidden_cycle_found_and_sqrt2_blind():
    fix = json.loads((FIX / "rulers_events.json").read_text(
        encoding="utf-8"))
    events = fix["events"]
    conc, phase = PhaseRuler().detect_cycle(events)
    blind = sqrt2_concentration(events)
    print(f"\n5:4 ruler: concentration {conc:.1f}x at phase {phase}; "
          f"sqrt2 ruler: {blind:.1f}x")
    assert conc >= 8.0, f"cycle concentration {conc:.1f}x < 8x"
    assert phase == fix["true_phase"], \
        f"found phase {phase}, planted {fix['true_phase']}"
    assert blind <= 2.5, \
        f"FLAG: the aperiodic ruler 'detected' a cycle ({blind:.1f}x) — " \
        f"the fixture is broken, not the theorem"