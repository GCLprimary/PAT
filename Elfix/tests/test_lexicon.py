"""Tests for lexicon growth Stage 1 (ortho_affix) + Stage 2 (compose_pron).
The earned allomorphy is the load-bearing claim, so most tests pin the voicing/
sibilant/coronal-stop conditioning directly (the same rule appendix.py earned)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.data_io import load_cmu
from elfix.lexicon.ortho_affix import discover_suffixes, decompose, INFLECTIONAL
from elfix.lexicon.compose_pron import compose


def test_core_inflectional_suffixes_are_earned():
    """Law 1: the CORE inflectional suffixes fall out of productivity (orthographic
    productivity is single-letter-skewed, so they emerge at frac~0.1). 'est' is
    genuinely rare and included by scope, not earned — an honest exception."""
    earned = discover_suffixes(load_cmu().keys())
    assert all(s in earned for s in ("s", "es", "ed", "ing", "er"))


def test_decompose_finds_known_stems_with_spelling_restoration():
    known = {"cat", "run", "make", "bus", "study", "play"}.__contains__
    assert decompose("cats", known) == [("cat", "s")]
    assert decompose("running", known) == [("run", "ing")]      # un-double
    assert decompose("making", known) == [("make", "ing")]      # e-insert
    assert decompose("studies", known) == [("study", "es")]     # i -> y
    assert decompose("played", known) == [("play", "ed")]
    assert decompose("xyz", known) == []                        # nothing known


def test_compose_voicing_allomorphy():
    """-s/-z and -t/-d chosen by the stem-final phoneme (the earned rule)."""
    assert compose(["k", "AE", "t"], "s") == ["k", "AE", "t", "s"]        # voiceless
    assert compose(["d", "AO", "g"], "s") == ["d", "AO", "g", "z"]        # voiced
    assert compose(["b", "AH", "s"], "s") == ["b", "AH", "s", "IH", "z"]  # sibilant
    assert compose(["w", "AO", "k"], "ed") == ["w", "AO", "k", "t"]       # voiceless
    assert compose(["p", "l", "EY"], "ed") == ["p", "l", "EY", "d"]       # voiced (V)
    assert compose(["w", "AO", "n", "t"], "ed") == ["w", "AO", "n", "t", "IH", "d"]


def test_compose_invariant_suffixes_and_no_rule():
    assert compose(["r", "AH", "n"], "ing") == ["r", "AH", "n", "IH", "NG"]
    assert compose(["f", "AE", "s", "t"], "er") == ["f", "AE", "s", "t", "ER"]
    assert compose(["x"], "ness") is None        # derivational: no v1 rule -> None
