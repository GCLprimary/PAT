"""X-5 acceptance (probe 45): the library curve and its gates.

Five pages, five lanes, one curve: 56.8 (no pages) -> 60.5 (two) ->
64.8 (five). Judges abstain outside their rule (law 4) — the NPI scope
paradigms, quantifiers_2, and the principle_A paradigms beyond the
strict frame's reach report ZERO judged pairs, asserted;
principle_A_domain_2 is FLAGGED, not asserted (clause-local binding —
the frame-depth-2 campaign owns it). Adding pages must not harm what
Part VIII already held (± 1.5 on every dn/sv-lane paradigm).
"""
import json
from pathlib import Path

import pytest

from mirror import LawBook, Page, TrigramScorer, run_all
from mirror.agreement import build_number_lexicon
from mirror.blimp import BLIMP_DIR, route, table
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent / "fixtures" / "blimp"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi")


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


def test_new_paradigm_gates(vendored):
    schooled, trigram = vendored
    print("\n" + table(schooled, baseline=trigram))
    gates = {
        "npi_present_1": (97, 99),
        "npi_present_2": (97, 99),
        "matrix_question_npi_licensor_present": (96, 99),
        "only_npi_licensor_present": (98, 99),
        "principle_A_c_command": (60, 85),
        # anaphor_number_agreement: REASSIGNED to the depth-2 lane by
        # Part XII's law 1 (assignment by measured precision); its gate
        # (>= 66.8) lives in test_depth2 now
        "existential_there_quantifiers_1": (89, 98),
    }
    for name, (floor, jfloor) in gates.items():
        forced, jn, jacc = schooled[name]
        assert forced >= floor, f"{name}: {forced:.1f} < {floor}"
        if jfloor is not None:
            assert jacc >= jfloor, \
                f"{name}: judged accuracy {jacc:.1f} < {jfloor}"


def test_abstention_asserted(vendored):
    """Law 4, leak-proof by construction: where the rule gives no
    verdict, the judge gives none — zero judged pairs."""
    schooled, trigram = vendored
    must_abstain = (
        "only_npi_scope", "sentential_negation_npi_scope",
        "existential_there_quantifiers_2",
        "principle_A_case_1", "principle_A_case_2",
        "principle_A_domain_1", "principle_A_domain_3",
        "principle_A_reconstruction", "anaphor_gender_agreement",
    )
    for name in must_abstain:
        forced, jn, _ = schooled[name]
        assert jn == 0, f"{name}: judged {jn} pairs — a judge left " \
                        f"its rule"
        assert forced == trigram[name][0]


def test_domain_2_flag_retired_by_depth2(vendored, library):
    """THE FLAG, RETIRED: Part IX recorded principle_A_domain_2 paying
    for the strict-frame judge's clause-blindness (41.9, judged slice
    below chance). Part XII's law 1 reassigned it to the depth-2 lane,
    where it gates at >= 61 @ >= 73 (test_depth2). In THIS vintage run
    (no verb artifact) the lane abstains entirely — the harm is gone,
    the conquest lives elsewhere, and this test keeps the history."""
    schooled, trigram = vendored
    forced, jn, jacc = schooled["principle_A_domain_2"]
    print(f"\nprinciple_A_domain_2 (vintage run): {forced:.1f}, "
          f"judged {jn} — reassigned; see test_depth2")
    assert jn == 0
    assert forced == trigram["principle_A_domain_2"][0]


def test_no_harm_part_viii(vendored):
    """Every Part VIII dn/sv-lane paradigm within ± 1.5 of its pin."""
    schooled, _ = vendored
    part8 = json.loads((FIX / "blimp_reference.json").read_text(
        encoding="utf-8"))["schooled"]
    checked = 0
    # "sva2" joins the lane list: SVA_2 was reassigned there by Part
    # XII's law 1, and in this vintage run (no verb artifact) the lane
    # abstains — its forced value still equals the Part VIII pin
    for name, (pinned, _, _) in part8.items():
        if route(name) not in ("dn", "sv", "sva2") \
                or name not in schooled:
            continue
        got = schooled[name][0]
        assert abs(got - pinned) <= 1.5, \
            f"{name}: {got:.1f} moved from its Part VIII pin {pinned:.1f}"
        checked += 1
    assert checked == 14
    print(f"\n{checked} Part VIII paradigms unharmed by three new pages")


@pytest.mark.skipif(not BLIMP_DIR.exists(),
                    reason="data/blimp missing — run scripts/fetch_blimp.py")
def test_library_curve(scorer, library):
    """The headline: overall (67, forced) >= 64.0; the curve printed."""
    ref = json.loads((FIX / "library_reference.json").read_text(
        encoding="utf-8"))
    schooled = run_all(scorer, library)
    overall = sum(v[0] for v in schooled.values()) / len(schooled)
    curve = ref["curve"]
    print(f"\nLIBRARY CURVE  pages=0: {curve['pages_0']}   "
          f"pages=2: {curve['pages_2']}   pages=5: {overall:.2f}")
    assert overall >= 64.0, f"overall {overall:.2f} < 64.0"
    # domain_2 and anaphor_number: REASSIGNED to the depth-2 lane by
    # Part XII's law 1 — this vintage run (no verb artifact) leaves
    # them to the trigram, so their Part IX pins no longer bind here;
    # their gates live in test_depth2
    reassigned = {"principle_A_domain_2", "anaphor_number_agreement"}
    for name, (pinned, jn, jacc) in ref["schooled"].items():
        if name in reassigned:
            continue
        got = schooled[name][0]
        assert abs(got - pinned) <= 1.5, \
            f"{name}: {got:.1f} drifted from the library pin {pinned:.1f}"
