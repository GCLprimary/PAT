"""E-4/E-5 (probe 53): pages 6-7, the diff-judges, the routing law,
and the selective aggregate.

LAW 3: THE SPECIFIC JUDGE OUTRANKS THE GENERAL LANE. anaphor_gender
sat inside the reflexive lane and was silently absorbed — 0 judged —
until the direct diff-judges were routed FIRST. The order lives in
route(); the gender paradigm reporting > 0 judged is the assertion
that keeps it.

The aggregate is the entry card's number, printed every run: judged
coverage and judged accuracy over all 67 beside the forced overall
(recorded band 24.2% @ ~93.8%; the L3 forecast targets 35-45% @ >= 95
as the library grows). existential_there_quantifiers_2 is CERTIFIED:
quantifier-inversion structure — abstention is correct, no cheap page
exists; the frame lane owns it.
"""
import json
from pathlib import Path

import pytest

from mirror import (LawBook, Page, TrigramScorer, aggregate,
                    load_paradigm, run_all)
from mirror.agreement import build_number_lexicon
from mirror.blimp import BLIMP_DIR, route, table
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent / "fixtures" / "blimp"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi", "gender_names",
         "past_irregulars")


@pytest.fixture(scope="module")
def library(transform):
    sg, pl, _ = build_number_lexicon(transform.pairs)
    return LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in PAGES], sg, pl)


@pytest.fixture(scope="module")
def scorer():
    return TrigramScorer()


@pytest.fixture(scope="module")
def vendored(scorer, library):
    schooled = run_all(scorer, library, blimp_dir=VENDOR)
    trigram = run_all(scorer, None, blimp_dir=VENDOR)
    return schooled, trigram


def test_routing_law(vendored):
    """The specific judge outranks the general lane — encoded and
    asserted: the gender paradigm is judged (> 0), not absorbed."""
    assert route("anaphor_gender_agreement") == "gender"
    assert route("irregular_past_participle_verbs") == "ppart"
    assert route("irregular_past_participle_adjectives") == "ppart"
    # anaphor_number: reassigned to depth-2 by Part XII's law 1
    assert route("anaphor_number_agreement") == "depth2"
    schooled, _ = vendored
    assert schooled["anaphor_gender_agreement"][1] > 0, \
        "anaphor_gender reports 0 judged — the reflexive lane " \
        "swallowed it again (law 3)"


def test_page_six_seven_gates(vendored):
    schooled, trigram = vendored
    forced, jn, jacc = schooled["anaphor_gender_agreement"]
    print(f"\nanaphor_gender: {trigram['anaphor_gender_agreement'][0]:.1f}"
          f" -> {forced:.1f} ({jn} judged @ {jacc:.1f}%)")
    assert forced >= 77.0 and jacc == 100.0
    for name, judged_floor in (
            ("irregular_past_participle_verbs", 850),
            ("irregular_past_participle_adjectives", 1000)):
        forced, jn, jacc = schooled[name]
        print(f"{name}: {trigram[name][0]:.1f} -> {forced:.1f} "
              f"({jn} judged @ {jacc:.1f}%)")
        assert forced == 100.0, f"{name} fell from perfect: {forced}"
        assert jn >= judged_floor and jacc == 100.0


@pytest.mark.skipif(not BLIMP_DIR.exists(),
                    reason="data/blimp missing — run scripts/fetch_blimp.py")
def test_entry_card_overall_and_aggregate(scorer, library):
    """Overall >= 65.5 forced at seven pages; the library curve; the
    selective aggregate recorded (band, not a gate); no-harm against
    the pinned reference."""
    ref = json.loads((FIX / "entry_reference.json").read_text(
        encoding="utf-8"))
    schooled = run_all(scorer, library)
    agg = aggregate(schooled)
    curve = ref["curve"]
    print(f"\nLIBRARY CURVE  {curve['pages_0']} -> {curve['pages_2']} "
          f"-> {curve['pages_5']} -> {agg['forced_overall']:.2f}")
    print(f"SELECTIVE (the entry-card row): {agg['judged']}/"
          f"{agg['total']} = {agg['coverage_pct']:.1f}% @ "
          f"{agg['judged_acc_pct']:.2f}% (band 24.2 @ ~93.8; L3 "
          f"forecast 35-45 @ >= 95)")
    assert agg["forced_overall"] >= 65.5
    # domain_2 and anaphor_number: reassigned to the depth-2 lane by
    # Part XII's law 1; this vintage run (no verb artifact) leaves them
    # to the trigram — their gates live in test_depth2
    reassigned = {"principle_A_domain_2", "anaphor_number_agreement"}
    for name, (pinned, _, _) in ref["schooled"].items():
        if name in reassigned:
            continue
        got = schooled[name][0]
        assert abs(got - pinned) <= 1.5, \
            f"{name}: {got:.1f} drifted from the entry pin {pinned:.1f}"


def test_quantifiers_2_certified(vendored):
    """CERTIFIED abstention: the bad sentences invert the quantifier
    structure ('All convertibles weren't there existing') — outside
    every page's rule; no cheap page exists. The frame lane owns it.
    Asserted at 0 judged, with two sample pairs printed."""
    schooled, trigram = vendored
    name = "existential_there_quantifiers_2"
    forced, jn, _ = schooled[name]
    pairs = load_paradigm(VENDOR / f"{name}.jsonl")[:2]
    print(f"\n{name}: {forced:.1f} == trigram "
          f"{trigram[name][0]:.1f}, judged {jn}")
    for g, b in pairs:
        print(f"  GOOD: {g}\n  BAD:  {b}")
    assert jn == 0
    assert forced == trigram[name][0]