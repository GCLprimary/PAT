"""A-3: the crown as a verb — two walks (probe/V-3 gates unchanged).

One feasible journey returns legs with rising centered closure toward
the destination; one impossible request is refused in plain language.
"""
import pytest

from pat import Agent


def test_walk_feasible_and_refused(tmp_path, organs):
    agent = Agent(str(tmp_path / "store"), organs=organs)

    act = agent.respond("walk water to music").clauses[0].act
    assert act.kind == "JOURNEY", f"feasible walk refused: {act.reason}"
    prompt, legs = act.detail
    assert len(legs) == 4
    closures = [to_b for _, to_b, _ in legs]
    print(f"\nwalk water->music from '{' '.join(prompt)}': " +
          " ".join(f"{c:+.3f}" for c in closures))
    assert closures[-1] > closures[0], "closure did not rise toward music"

    act = agent.respond("walk water to zzzquark").clauses[0].act
    assert act.kind == "REFUSE"
    assert "zzzquark" in act.reason           # names the failing endpoint


def test_walk_bad_syntax_is_alien(tmp_path, organs):
    agent = Agent(str(tmp_path / "store"), organs=organs)
    act = agent.respond("walk water toward music").clauses[0].act
    assert act.kind == "REFUSE"