"""A-3: the learning battery (probe 33, pinned stream).

Memory ON beats memory OFF by >= 40 points on the final third (measured
60); zero confabulation in BOTH arms (law 1, hard); and every ON gain
traces to a logged write (law 2 — the provenance log must cover the
bases behind the accuracy delta).
"""
import numpy as np
import pytest

from pat import Agent


def run_arm(store, stream, organs, memory_on):
    agent = Agent(store, seed_bases=stream["known0"], organs=organs)
    new_bases = set(stream["bases"]) - set(stream["known0"])
    log = []
    for kind, gold_b, w in stream["tasks"]:
        act = agent.respond(f"analyze {w}").clauses[0].act
        correct = (kind == "bare" and act.kind == "BARE"
                   and act.detail[0] == gold_b) or \
                  (kind == "derived" and act.kind == "DERIVED"
                   and act.detail[0] == gold_b)
        confab = (act.kind != "REFUSE") and not correct and \
                 not (kind == "derived" and act.kind == "BARE"
                      and act.detail[0] == gold_b)
        log.append((kind, gold_b, correct, confab, act.kind))
        # law 2: the refusal of a bare unknown is the teachable moment;
        # the world confirms and the creature writes — never silently
        if memory_on and kind == "bare" and act.kind == "REFUSE":
            agent.respond(f"remember {gold_b}")
    return agent, log


def final_third_accuracy(log):
    third = len(log) // 3
    return float(np.mean([c for _, _, c, _, _ in log[-third:]])) * 100


def test_learning_battery(tmp_path, learning_stream, organs):
    on_agent, on_log = run_arm(str(tmp_path / "on"), learning_stream,
                               organs, memory_on=True)
    _, off_log = run_arm(str(tmp_path / "off"), learning_stream,
                         organs, memory_on=False)

    on_final = final_third_accuracy(on_log)
    off_final = final_third_accuracy(off_log)
    gap = on_final - off_final
    on_confabs = sum(cf for _, _, _, cf, _ in on_log)
    off_confabs = sum(cf for _, _, _, cf, _ in off_log)
    print(f"\nmemory ON  final-third {on_final:.0f}%  "
          f"confabs {on_confabs}  writes {len(on_agent.provenance)}")
    print(f"memory OFF final-third {off_final:.0f}%  confabs {off_confabs}")
    print(f"learning gap: {gap:.0f} points")

    # law 1: the refusal spine is total — zero confabulation, both arms
    assert on_confabs == 0, f"{on_confabs} confabulations with memory ON"
    assert off_confabs == 0, f"{off_confabs} confabulations with memory OFF"
    # the learning gap
    assert gap >= 40, f"learning gap {gap:.0f} < 40 points"

    # law 2: every ON gain traces to a logged write with a refusal
    taught = {p["word"] for p in on_agent.provenance
              if p["taught_by"] != "<seeded>"}
    new_bases = set(learning_stream["bases"]) - set(learning_stream["known0"])
    third = len(on_log) // 3
    gained = {b for kind, b, correct, _, _ in on_log[-third:]
              if correct and b in new_bases}
    untraced = gained - taught
    assert not untraced, \
        f"ON gains without provenance (silent learning?!): {untraced}"
    for p in on_agent.provenance:
        if p["word"] in gained:
            assert p["refusal"] is not None, \
                f"'{p['word']}' was taught without a recorded refusal"