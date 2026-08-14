"""R-2 acceptance (probe 36): the stamped register bank.

Distance-blind single dependencies at every gap; nesting decided by
exact stamps where the unstamped bank falls to chance. Stack behavior
earned from arithmetic, not from a stack.
"""
import json

import numpy as np
import pytest

from mirror import RegisterBank, Stamp, UnstampedBank
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def streams():
    return json.loads((FIX / "register_streams.json").read_text(
        encoding="utf-8"))


def replay(bank, events):
    got = []
    for ev in events:
        if ev[0] == "open":
            bank.open({"num": ev[2]}, Stamp.at(ev[1]))
        else:
            reg = bank.close(Stamp.at(ev[1]))
            got.append(reg.features["num"] if reg else None)
    return got


def test_single_dependencies_distance_blind(streams):
    by_gap = {}
    for trial in streams["singles"]:
        ok = replay(RegisterBank(), trial["events"]) == trial["gold"]
        g = trial["gap"]
        by_gap.setdefault(g, [0, 0])
        by_gap[g][0] += int(ok)
        by_gap[g][1] += 1
    print("\nsingles: " + "  ".join(
        f"gap {g}: {c}/{n}" for g, (c, n) in sorted(by_gap.items())))
    for g, (c, n) in by_gap.items():
        assert c == n, f"single dependency failed at gap {g}: {c}/{n}"


def test_nested_stamped_perfect_unstamped_chance(streams):
    stamped_ok = 0
    for trial in streams["nested"]:
        stamped_ok += int(replay(RegisterBank(), trial["events"])
                          == trial["gold"])
    n = len(streams["nested"])
    assert stamped_ok == n, f"stamped bank {stamped_ok}/{n} on nested"

    rng = np.random.default_rng(47)
    unstamped_ok = sum(
        int(replay(UnstampedBank(rng), t["events"]) == t["gold"])
        for t in streams["nested"])
    rate = unstamped_ok / n
    print(f"\nnested: stamped {stamped_ok}/{n}, unstamped {rate:.0%}")
    assert 0.30 <= rate <= 0.70, \
        f"FLAG: unstamped bank at {rate:.0%} — if this is materially " \
        f"above chance the generator's streams stopped being nested"