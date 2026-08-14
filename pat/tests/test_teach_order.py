"""F-3: the teach-order sweep — the tie-order luck, retired by measurement.

Part V's finding: the shipped learning battery's zero-confabulation
headline survived on argmax tie order (the cell/seal imposter was never
taught into collision). Under the phon gate the same assertion passes
in EVERY teach order: three pinned colliding pairs are taught in BOTH
orders, every derived form of both bases is analyzed, and each analysis
either attributes to the RIGHT base by stem-phon evidence or refuses —
the imposter never wins, whichever base arrived first. The assertion
that used to pass by accident now passes by measurement.
"""
import json
from pathlib import Path

import pytest

from pat import Agent

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def pairs():
    return json.loads((FIX / "teach_order_pairs.json").read_text(
        encoding="utf-8"))["pairs"]


def test_teach_order_sweep(tmp_path, pairs, organs):
    confabs, rows = [], []
    for pi, pair in enumerate(pairs):
        a, b = pair["a"], pair["b"]
        for oi, order in enumerate(((a, b), (b, a))):
            agent = Agent(str(tmp_path / f"store_{pi}_{oi}"),
                          seed_bases=list(order), organs=organs)
            for base in (a, b):
                for sfx, w in pair["forms"][base]:
                    act = agent.respond(f"analyze {w}").clauses[0].act
                    correct = (act.kind == "DERIVED"
                               and tuple(act.detail) == (base, sfx))
                    confab = act.kind != "REFUSE" and not correct and \
                        not (act.kind == "BARE" and act.detail[0] == base)
                    if confab:
                        confabs.append((order, w, act))
                    rows.append((order, base, w, correct, act.kind))
    n_correct = sum(r[3] for r in rows)
    print(f"\nteach-order sweep: {len(rows)} analyses across "
          f"{len(pairs)} colliding pairs x both orders; "
          f"{n_correct} correct attributions, {len(confabs)} confabs")
    for order, base, w, correct, kind in rows:
        print(f"  taught {order[0]}->{order[1]}: '{w}' -> {kind}"
              f"{'' if correct else '  (!)' if kind != 'REFUSE' else ''}")
    # law 1, now unconditional: zero confabulation in EVERY order
    assert not confabs, f"tie-order confabulation returned: {confabs}"
    # and the attribution is by measurement, not luck: every base's
    # forms resolve correctly in both orders
    assert n_correct == len(rows), \
        f"only {n_correct}/{len(rows)} correct attributions in the sweep"
