"""A-3: the composition battery (probe 34, pinned inputs).

One persistent creature across all 72 inputs (state accumulates, as in
the probe). Per-clause accuracy >= 90% at every k in 1..6 (measured
92-100); flatness: acc(k=6) >= acc(k=1) - 10; alien refusal 100% with
clean-clause accuracy in alien-bearing inputs >= 95%; teach->use within
input at the pinned-thread band; zero confabulation (law 1, hard).
"""
import numpy as np
import pytest

from pat import Agent


def test_composition_battery(tmp_path, composition, organs):
    agent = Agent(str(tmp_path / "store"),
                  seed_bases=composition["known0"], organs=organs)
    teachable = set(composition["teachable"])

    stats = {k: [0, 0] for k in range(1, 7)}
    thread_ok = thread_n = 0
    alien_ref = alien_n = 0
    clean_in_alien = [0, 0]
    confabs = 0

    for inp in composition["inputs"]:
        k = inp["k"]
        golds = inp["gold"]
        has_alien = any(g[0] == "ALIEN" for g in golds)
        response = agent.respond(" and ".join(inp["clauses"]))
        assert len(response.clauses) == len(golds), \
            f"segmentation broke: {len(response.clauses)} != {len(golds)}"
        for cr, gd in zip(response.clauses, golds):
            act = cr.act
            if gd[0] == "ALIEN":
                alien_n += 1
                alien_ref += int(act.kind == "REFUSE")
                continue
            if gd[0] == "NEIGHBORS":
                ok = act.kind == "NEIGHBORS" and len(act.detail) == 3
            elif gd[0] in ("LEARNED", "LEARNEDOK"):
                ok = act.kind in ("LEARNED", "KNOWN")
            elif gd[0] == "DERIVED":
                ok = act.kind == "DERIVED" and tuple(act.detail) == \
                    (gd[1], gd[2])
                if act.kind == "DERIVED" and not ok:
                    confabs += 1
            elif gd[0] == "YES":
                ok = act.kind == "YES"
            else:
                ok = False
            stats[k][0] += int(ok)
            stats[k][1] += 1
            if has_alien:
                clean_in_alien[0] += int(ok)
                clean_in_alien[1] += 1
            if gd[0] == "DERIVED" and gd[1] in teachable:
                thread_n += 1
                thread_ok += int(ok)

    acc = {k: stats[k][0] / stats[k][1] for k in range(1, 7)}
    print("\nper-clause accuracy vs k: " +
          "  ".join(f"k={k}: {acc[k]:.0%}" for k in range(1, 7)))
    clean = clean_in_alien[0] / max(clean_in_alien[1], 1)
    print(f"aliens refused {alien_ref}/{alien_n}; clean-in-alien {clean:.0%}; "
          f"teach->use {thread_ok}/{thread_n}; confabs {confabs}")

    for k in range(1, 7):
        assert acc[k] >= 0.90, f"k={k} accuracy {acc[k]:.0%} < 90%"
    assert acc[6] >= acc[1] - 0.10, "complexity curve is not flat"
    assert alien_ref == alien_n, \
        f"alien containment broken: {alien_ref}/{alien_n} refused"
    assert clean >= 0.95, f"clean clauses in alien-bearing inputs {clean:.0%}"
    assert thread_n == composition["teach_use_threads"]
    assert thread_ok >= max(1, int(thread_n * 14 / 19)), \
        f"teach->use {thread_ok}/{thread_n} below the 14/19 band"
    assert confabs == 0, f"{confabs} confabulations — LAW BROKEN"