"""A-2: the alien law, hard — verbs the repertoire has never seen are
refused BY NAME, and one bad clause poisons nothing (law 4)."""
import pytest

from pat import Agent

ALIENS = ["translate", "rhyme", "summarize", "conjugate", "pronounce",
          "spell", "delete", "count", "sing", "define"]


def test_alien_verbs_refused_by_name(tmp_path, organs):
    agent = Agent(str(tmp_path / "store"), seed_bases=["help"],
                  organs=organs)
    for verb in ALIENS:
        act = agent.respond(f"{verb} water").clauses[0].act
        assert act.kind == "REFUSE", f"'{verb}' was not refused"
        assert f"'{verb}'" in act.reason, \
            f"the refusal does not name the alien verb: {act.reason!r}"


def test_one_bad_clause_poisons_nothing(tmp_path, organs, relatives):
    agent = Agent(str(tmp_path / "store"), seed_bases=["help"],
                  organs=organs)
    sfx, w = relatives["help"][0] if "help" in relatives else ("ing", "helping")
    r = agent.respond(f"analyze {w} and translate water and know help")
    kinds = [c.act.kind for c in r.clauses]
    assert kinds[1] == "REFUSE"               # the alien, contained
    assert r.clauses[0].act.kind == "DERIVED" \
        and r.clauses[0].act.detail[0] == "help"
    assert kinds[2] == "YES"                  # the clause after survives
