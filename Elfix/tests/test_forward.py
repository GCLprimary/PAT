"""Tests for the integrated forward pass + morpheme->word rung (elfix/forward.py).
Checks the law-bearing properties: centre+width at every rung (Law 4), normalised
attention (Tier 4), recognition->temperature wiring (Tier 7), and honest
composition (Law 6 — the rung is counted, with a degenerate single-child case)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.forward import (forward, compose, syllable_units, morpheme_units,
                           forward_utterance, word_unit)
from elfix.substrate.vectors import DIM
from elfix.trajectory.trajectory import Trajectory
from elfix.emergent.emergent_unit import discover, auto_quanta
from elfix.emergent.appendix import discover_appendices
from elfix.data_io import load_cmu
from elfix.running_text import Token

RUNNING = ["r", "AH", "n", "IH", "NG"]
PLANT = ["p", "l", "AE", "n", "t"]


def test_every_unit_carries_centre_and_width():
    for u in syllable_units(RUNNING):
        assert len(u.centre) == DIM
        assert isinstance(u.width, float) and u.width >= 0.0


def test_attention_rows_normalised_and_recognition_bounded():
    r = forward(RUNNING)
    assert len(r.attention) == len(r.units)
    for row in r.attention:
        assert abs(sum(row) - 1.0) < 1e-9
    assert 0.0 <= r.recognition <= 1.0
    assert len(r.carry) == DIM


def test_rung_composes_all_symbols_into_a_word():
    r = forward(RUNNING)
    assert r.word.level == "word"
    assert r.word.symbols == RUNNING                 # the word spans its syllables
    assert r.word.width >= 0.0


def test_single_child_compose_inherits_width_exactly():
    """Degenerate rung (Law-honest): a one-syllable word's width is that
    syllable's width — between-spread is zero, no hidden inflation."""
    units = syllable_units(PLANT)
    assert len(units) == 1
    assert abs(compose(units).width - units[0].width) < 1e-9


def test_morpheme_to_word_rung():
    """The same `compose` lifts MORPHEME units to a word: cat+s -> two morpheme
    units -> one word unit spanning them (the rung is level-agnostic)."""
    appendix = discover_appendices(list(load_cmu().values()))
    units = morpheme_units(["k", "AE", "t", "s"], appendix)    # cat + s
    assert len(units) >= 2 and units[-1].symbols == ["s"]
    word = compose(units, "word")
    assert word.level == "word" and word.symbols == ["k", "AE", "t", "s"]


def test_word_unit_composes_from_syllables():
    u = word_unit("running", load_cmu()["running"])
    assert u is not None and u.level == "word" and u.symbols == ["running"]
    assert len(u.centre) == DIM and u.width >= 0.0


def test_forward_utterance_runs_the_full_ladder_over_words():
    cmu = load_cmu()
    sent = ["the", "cats", "ran"]
    toks = [Token(w, cmu[w], "attested") for w in sent]
    r = forward_utterance(toks)
    assert r is not None and len(r.words) == 3
    assert r.utterance.level == "utterance" and r.utterance.symbols == sent
    for row in r.attention:                       # Tier 4: between-word, normalized
        assert abs(sum(row) - 1.0) < 1e-9
    assert len(r.carry_trajectory) == 3 and len(r.carry_trajectory[0]) == DIM
    assert 0.0 <= r.recognition <= 1.0


def test_forward_utterance_oov_is_skipped_and_lowers_recognition():
    cmu = load_cmu()
    known = [Token(w, cmu[w], "attested") for w in ["the", "cat"]]
    with_oov = known + [Token("qzzx", None, "oov")]
    r1, r2 = forward_utterance(known), forward_utterance(with_oov)
    assert len(r2.words) == 2                      # oov has no phonemes -> skipped
    assert r2.recognition < r1.recognition         # 2/3 < 2/2


def test_forward_utterance_salience_weights_carry_by_predictiveness():
    """Tier 6 wired in: shape sets each word's carry SALIENCE = its mean arc
    predictiveness (earned op). Predictiveness set directly so it is deterministic."""
    from elfix.routing.shape_routing import ShapeRouter
    cmu = load_cmu()
    router = ShapeRouter([Trajectory.of(w) for w in list(cmu.values())[:6000]])
    arcs_the = router.route(Trajectory.of(cmu["the"]))
    router.predictiveness = {c: 0.2 for c in arcs_the}    # a low-predictiveness word
    tok = Token("the", cmu["the"], "attested")
    assert abs(forward_utterance([tok], router=router).saliences[0] - 0.2) < 1e-9
    assert forward_utterance([tok]).saliences == [1.0]    # no router -> uniform salience


def test_recognition_drives_temperature():
    corpus = list(load_cmu().values())
    q = auto_quanta([Trajectory.of(w) for w in corpus[:8000]])
    inv = discover(corpus[:8000], quanta=q)
    rec = forward(RUNNING, inv, q)
    assert rec.recognition > 0.0 and rec.temperature < 2.0     # known -> commit
    nov = forward(RUNNING)                                      # no store
    assert nov.recognition == 0.0 and nov.temperature == 2.0    # novel -> stay open
