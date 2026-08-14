"""T-1 batteries: taught-word citizenship (probe 59) — the lantern
finding made law, plus T-4's anagram guard.

Law 1: citizenship is decided by receipts. Pron on file -> FULL
citizen (derivation index joined, children certify, restart-proof).
No pron -> PARTIAL citizen (receipt kept, inflections refuse by
name). Law 2: the transform proposes; only attestation asserts — a
predicted pronunciation may REPORT, never certify. Law 5: the ear
extends to teaching (7.5% of teachable words collide with a known
spelling; aalen/alan pinned).
"""
import json
import shutil
from pathlib import Path

import pytest

from pat import Agent
from pat.reading import ReadingSession

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"
STORE = Path(__file__).resolve().parent.parent / "data" / "store"
SIDE_BIO = "derivable: sigh+ed; read-taught epoch 1, pruned epoch 5"


@pytest.fixture(scope="module")
def fx():
    return json.loads((FIX / "citizenship_sample.json").read_text(
        encoding="utf-8"))


@pytest.fixture()
def lived(tmp_path):
    """A disposable copy of the canonical store — the lived Pat,
    safe to teach."""
    shutil.copytree(STORE, tmp_path / "s")
    return str(tmp_path / "s")


def line(agent, text):
    return agent.respond(text).lines()[0]


# ── the LANTERN battery: full citizenship, restart-proof ─────────────
def test_lantern_full_citizen_with_session(lived):
    a = Agent(lived)
    assert line(a, "remember lantern") == \
        "learned 'lantern' — you taught me just now"
    assert line(a, "analyze lanterns") == "'lanterns' = 'lantern' + -s"
    assert a.reading.knows("lantern") == (True, "taught")
    a.save()
    reborn = Agent(lived)                     # death and rebirth
    assert line(reborn, "analyze lanterns") == \
        "'lanterns' = 'lantern' + -s"
    assert line(reborn, "know lantern") == "yes, I know 'lantern' (taught)"
    assert reborn.reading.knows("side") == (True, SIDE_BIO)


def test_lantern_sessionless_vintage_path(tmp_path):
    """Without a reading session the Part VI repertoire path carries
    the same citizenship — teach, certify, survive restart."""
    a = Agent(str(tmp_path / "bare"))
    a.respond("remember lantern")
    assert line(a, "analyze lanterns") == "'lanterns' = 'lantern' + -s"
    reborn = Agent(str(tmp_path / "bare"))
    assert line(reborn, "analyze lanterns") == \
        "'lanterns' = 'lantern' + -s"


# ── the 50-stem unlock sample (pool probe-exact) ─────────────────────
def test_unlock_sample_ge_95(organs, fx):
    pool = fx["pool"]
    assert (pool["stems"], pool["children"]) == (6076, 7005)
    assert pool["ear_collisions"] / pool["teachable"] == \
        pytest.approx(0.075, abs=0.0005)
    s = ReadingSession(organs, seed_bases=[])
    for stem in fx["sample"]:
        s.teach(stem, "taught")
    ok = tot = 0
    for stem, kids in fx["sample"].items():
        for sfx, child in kids.items():
            tot += 1
            mode, gb, gs, verdict = s.analyze_word(child)
            ok += int((mode, gb, gs, verdict)
                      == ("BOUND", stem, sfx, "OK"))
    print(f"\nunlock sample: {ok}/{tot} children certify "
          f"({ok/tot*100:.1f}%)")
    assert ok / tot >= 0.95


# ── the ear clause (law 5, aalen/alan pinned) ────────────────────────
def test_ear_clause_at_teach_time(lived, fx):
    a = Agent(lived)
    case = fx["ear_case"]
    a.respond(f"remember {case['hears']}")
    assert line(a, f"remember {case['teach']}") == (
        f"learned '{case['teach']}' — you taught me just now "
        f"(ear: identical to '{case['hears']}', which I already know)")


# ── the partial citizen (zorp, verbatim refusals) ────────────────────
def test_partial_citizen_verbatim(lived):
    a = Agent(lived)
    n0 = a.bases_total()
    assert line(a, "remember zorp") == \
        "learned 'zorp' — you taught me just now " \
        "(partial: no pronunciation on file)"
    assert line(a, "analyze zorps") == "refuse: no pronunciation on file"
    assert line(a, "know zorp") == \
        "yes, I know 'zorp' (taught; no pronunciation on file)"
    assert a.bases_total() == n0 + 1
    reborn = Agent(lived)                     # the receipt survives
    assert line(reborn, "know zorp") == \
        "yes, I know 'zorp' (taught; no pronunciation on file)"
    assert line(reborn, "analyze zorps") == \
        "refuse: no pronunciation on file"
    assert line(reborn, "remember zorp") == "I already know 'zorp'"


# ── law 2: predicted pronunciations REPORT, never certify ────────────
def test_predicted_pron_reports_never_certifies(lived, fx):
    a = Agent(lived)
    stem = fx["predicted_case"]["stem"]
    guess = fx["predicted_case"]["guess"]
    a.respond(f"remember {stem}")
    got = line(a, f"analyze {guess}")
    assert got == (f"'{guess}' — derivable by rule from "
                   f"'{stem}'+-s; pronunciation predicted, not attested")
    assert "CERTIFY" not in got and " = " not in got
    # the oracle cannot be talked into it either
    v = line(a, f"verify {guess} = {stem}+s")
    assert v.startswith("REFUSE")


def test_no_predicted_pron_in_any_certification(organs, fx):
    """Structural: across the sample, analysis of a spelling with no
    pron on file NEVER yields a certification — only REPORT or
    refusal."""
    corpus = organs.embedder.corpus
    s = ReadingSession(organs, seed_bases=[])
    checked = 0
    for stem in fx["sample"]:
        s.teach(stem, "taught")
        guess = stem + "s"
        if guess in corpus:
            continue
        # the engine's certification surface is corpus-keyed: a
        # spelling without a pron cannot even be asked
        with pytest.raises(KeyError):
            s.analyze_word(guess)
        checked += 1
    assert checked >= 10


# ── T-4: the anagram guard ───────────────────────────────────────────
def test_anagram_guard_pinned(lived, fx):
    a = Agent(lived)
    c = fx["anagram_case"]
    got = line(a, f"verify {c['word']} = {c['base']}+{c['sfx']}")
    assert got.startswith("REFUSE — same sounds, different order — "
                          "the compass tells them apart")
    # and the guard does not overreach: the true pair still certifies
    assert line(a, "verify painting = paint+ing") == \
        "CERTIFY — paint+ing, pair-exact, mined"
