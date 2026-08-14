"""L-3 acceptance (probes 42-43): the BLiMP batteries.

Judgment stays selective: every forced number is reported beside its
judged coverage and judged accuracy. The vendored 14 agreement
paradigms carry the gates; the full-67 run carries the overall gate,
the no-leak law (judges must not touch paradigms outside their lane),
and the baseline row. The seduction control (distractor paradigms at
trigram-only <= 50%) proves the attractors are real — if it drifts,
the fixture's distractors aren't distracting anyone.
"""
import hashlib
import json
from pathlib import Path

import pytest

from mirror import LawBook, Page, TrigramScorer, run_all
from mirror.agreement import build_number_lexicon
from mirror.blimp import BLIMP_DIR, route, run, table
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent / "fixtures" / "blimp"


@pytest.fixture(scope="module")
def lawbook(transform):
    """The FULL library (Part IX state): the Part VIII gates and
    no-harm asserts below now also prove three new pages harmless to
    the dn/sv lanes."""
    sg, pl, _ = build_number_lexicon(transform.pairs)
    pages = ("demonstratives", "irregular_plurals", "reflexives",
             "quantifiers_existential", "npi")
    return LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in pages], sg, pl)


@pytest.fixture(scope="module")
def scorer():
    return TrigramScorer()          # checksum-asserted construction


@pytest.fixture(scope="module")
def reference():
    return json.loads((FIX / "blimp_reference.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def vendored(scorer, lawbook):
    schooled = run_all(scorer, lawbook, blimp_dir=VENDOR)
    trigram = run_all(scorer, None, blimp_dir=VENDOR)
    return schooled, trigram


def test_paradigm_gates(vendored):
    """The spec's five gates, with judged accuracy where demanded."""
    schooled, trigram = vendored
    print("\n" + table(schooled, baseline=trigram))
    gates = {
        "determiner_noun_agreement_1": (86, None),
        "determiner_noun_agreement_irregular_1": (88, 98),
        "determiner_noun_agreement_irregular_2": (93, 98),
        "determiner_noun_agreement_with_adj_irregular_1": (75, None),
        "irregular_plural_subject_verb_agreement_1": (65, None),
    }
    for name, (floor, judged_floor) in gates.items():
        forced, jn, jacc = schooled[name]
        assert forced >= floor, f"{name}: {forced:.1f} < {floor}"
        if judged_floor is not None:
            assert jacc >= judged_floor, \
                f"{name}: judged accuracy {jacc:.1f} < {judged_floor}"


def test_no_harm_and_reference_regression(vendored, reference):
    """Regular dn paradigms stay within 1.5 points of the pinned
    reference (and of the probe's quoted value where it quoted one)."""
    schooled, _ = vendored
    ref = reference["schooled"]
    regular_dn = [n for n in schooled if n.startswith("determiner_noun")
                  and "irregular" not in n]
    assert len(regular_dn) == 4
    for name in regular_dn:
        got = schooled[name][0]
        pinned = ref[name][0]
        assert abs(got - pinned) <= 1.5, \
            f"{name}: {got:.1f} moved {abs(got - pinned):.1f} from " \
            f"its pinned {pinned:.1f}"
    assert abs(schooled["determiner_noun_agreement_1"][0] - 88.6) <= 1.5


def test_seduction_control(vendored):
    """Distractor paradigms at trigram-only <= 50% — the control that
    proves the attractors are real."""
    _, trigram = vendored
    for name in ("distractor_agreement_relational_noun",
                 "distractor_agreement_relative_clause"):
        acc = trigram[name][0]
        print(f"\n{name}: trigram-only {acc:.1f}%")
        assert acc <= 50.0, \
            f"FLAG: {name} at {acc:.1f}% trigram-only — the fixture's " \
            f"distractors aren't distracting anyone"


def test_coverage_gap_flag(vendored):
    """irregular_SVA_2 is recorded AT the trigram baseline with a named
    flag: its subjects carry no determiner, so sv_judge v1 never fires.
    The frame lane owns this paradigm; asserting a gain here would be
    pretending."""
    schooled, trigram = vendored
    name = "irregular_plural_subject_verb_agreement_2"
    forced, jn, _ = schooled[name]
    print(f"\nCOVERAGE GAP (named, not asserted): {name} forced "
          f"{forced:.1f} == trigram {trigram[name][0]:.1f}, judged {jn} "
          f"— subjects without determiners are the frame lane's job")
    assert jn == 0
    assert forced == trigram[name][0]


@pytest.mark.skipif(not BLIMP_DIR.exists(),
                    reason="data/blimp missing — run scripts/fetch_blimp.py "
                           "(the 67-paradigm battery needs the fetched set)")
def test_overall_67(scorer, lawbook, reference):
    """Manifest-verified full run: overall >= 59.5 forced (probe 60.5);
    the trigram baseline row is recorded, not gated; judges must not
    leak outside their lane (every non-agreement paradigm's forced
    accuracy equals trigram-only)."""
    manifest = json.loads((FIX / "blimp_manifest.json").read_text(
        encoding="utf-8"))
    assert len(manifest) == 67
    for name, expected in manifest.items():
        got = hashlib.sha256((BLIMP_DIR / name).read_bytes()).hexdigest()
        assert got == expected, f"{name} drifted from the manifest"

    schooled = run_all(scorer, lawbook)
    trigram = run_all(scorer, None)
    overall = sum(v[0] for v in schooled.values()) / len(schooled)
    tri_overall = sum(v[0] for v in trigram.values()) / len(trigram)
    print(f"\nOVERALL (67, forced): {overall:.2f}   "
          f"trigram-only baseline row: {tri_overall:.2f} "
          f"(probe band 56.8 ± 0.7 — recorded, not gated)")
    assert overall >= 59.5, f"overall {overall:.2f} < 59.5"
    leaked = [n for n in schooled if route(n) is None
              and schooled[n][0] != trigram[n][0]]
    assert not leaked, f"judges leaked outside their lane: {leaked}"
    for n in schooled:
        if route(n) is None:
            assert schooled[n][1] == 0, f"{n} reports judged pairs"
