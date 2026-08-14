"""A-1 + L-4: the creature survives its own death — lessons included.

Teach 5 bases through the law-2 path (refusal + confirmation), study a
page, destroy the process, construct a new Agent on the same store, and
analyze relatives of the taught bases: >= 4/5 succeed with zero
confabulation — and the lesson provenance survives death too (the
pages ledger persists; the reborn creature re-studies its pinned
pages). The original promise of the whole project, asserted at the
creature level — and the provenance file must say how it knows what it
knows.
"""
import json
from pathlib import Path

import pytest

from pat import Agent
from mirror.config import DATA_DIR as MIRROR_DATA


def test_survives_restart(tmp_path, learning_stream, relatives, organs):
    store = str(tmp_path / "creature")
    new_bases = [b for b in learning_stream["bases"]
                 if b not in learning_stream["known0"]
                 and relatives.get(b)][:5]
    assert len(new_bases) == 5

    # life 1: refusal -> confirmation -> write, five times — and one
    # page studied (L-4)
    agent = Agent(store, organs=organs)
    for b in new_bases:
        act = agent.respond(f"analyze {b}").clauses[0].act
        assert act.kind == "REFUSE"          # it genuinely doesn't know
        agent.respond(f"remember {b}")
    assert len(agent.provenance) == 5
    report = agent.study(MIRROR_DATA / "page_irregular_plurals.txt")
    assert report["conflicts"] >= 3
    del agent                                 # the process "dies"

    # life 2: same store, no seeds — it must remember being taught
    reborn = Agent(store, organs=organs)
    assert set(reborn.known) == set(new_bases)

    # L-4: lesson provenance survived death
    assert reborn.reading is not None, "the pages ledger did not wake"
    num, prov = reborn.reading.number_of("men")
    assert (num, prov) == ("pl", "lesson:irregular_plurals")
    yes, kprov = reborn.reading.knows("men")
    assert yes and kprov == "lesson:irregular_plurals"
    assert any(c["word"] == "men"
               for c in reborn.reading.lesson_conflicts)
    pages = json.loads((Path(store) / "pages.json").read_text(
        encoding="utf-8"))
    assert [p["page"] for p in pages] == ["irregular_plurals"]
    # "analyze relatives", plural: a base is recovered if the reborn
    # creature correctly analyzes EITHER of its derived forms (a modal-
    # allomorph mismatch on one form is honest physics, not amnesia)
    ok = confabs = 0
    for b in new_bases:
        recovered = False
        for sfx, w in relatives[b]:
            act = reborn.respond(f"analyze {w}").clauses[0].act
            if act.kind == "DERIVED" and act.detail[0] == b:
                recovered = True
            elif act.kind != "REFUSE" and not (
                    act.kind == "BARE" and act.detail[0] == b):
                confabs += 1
        ok += int(recovered)
    print(f"\nreborn: {ok}/5 relatives analyzed, {confabs} confabulations")
    assert ok >= 4, f"only {ok}/5 relatives recovered after restart"
    assert confabs == 0, "the reborn creature confabulated — LAW BROKEN"

    # the receipts survived too
    prov = json.loads((Path(store) / "provenance.json").read_text(
        encoding="utf-8"))
    assert {p["word"] for p in prov} == set(new_bases)
    assert all(p["refusal"] is not None for p in prov), \
        "a taught base has no recorded refusal (law 2)"
