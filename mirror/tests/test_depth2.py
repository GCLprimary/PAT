"""D-1/D-2 (probe 54): the depth-2 resolver, the assignment law, and
the gates.

LAW 1: JUDGES ARE ASSIGNED PER-PARADIGM BY MEASURED PRECISION — the
contest is re-run here and must reproduce the pinned winners (forced
accuracy, judged-accuracy floor 85). c_command is the pinned negative:
the strict-frame judge keeps it (64.9 @ 87) because depth-2's judged
slice runs under the floor there — c_command's antecedent IS the
strict-frame subject; it was never depth-2's customer.

LAW 2: THE VERB INVENTORY IS AN ARTIFACT — checksummed, from mined
pairs + the irregulars page, never a hand list. upset and sounds (the
session's noun-verb ambiguity casualties) are verbish BY ARTIFACT:
sounds through sound's mined -ed/-ing family, upset through its page-7
row. The mining shadow's residue is recorded: imagine/notice
(e-deletion) sit outside the mined side and outside the page — their
absence is the shadow, named, not patched.

THE FOUR SESSION CANARIES ride test_canaries; the F3 margin note:
the clause-boundary mislabel family is confirmed; REDUCED RELATIVES
specifically are unobserved in BLiMP's paradigms — recorded here so
the frontier knows what this organ has never met.
"""
import hashlib
import json
from pathlib import Path

import pytest

from mirror import LawBook, Page, TrigramScorer, aggregate, run_all
from mirror.agreement import build_number_lexicon
from mirror.blimp import (BLIMP_DIR, DEPTH2_ASSIGNED, SVA2_ASSIGNED,
                          depth2_judge, load_paradigm, reflexive_judge,
                          route, sva2_judge)
from mirror.config import DATA_DIR
from mirror.frames import Depth2Resolver, case_tokens, verb_inventory

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent / "fixtures" / "blimp"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi", "gender_names",
         "past_irregulars")


@pytest.fixture(scope="module")
def book(transform):
    sg, pl, _ = build_number_lexicon(transform.pairs)
    return LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in PAGES], sg, pl)


@pytest.fixture(scope="module")
def verbs(transform, book):
    v = verb_inventory(transform, book.page_named("past_irregulars"))
    pin = json.loads((FIX / "verb_inventory.json").read_text(
        encoding="utf-8"))
    got = hashlib.sha256(
        "\n".join(sorted(v)).encode("utf-8")).hexdigest()
    assert got == pin["sha256"], \
        "the verb artifact drifted from its pin (law 2)"
    assert len(v) == pin["count"]
    return v


@pytest.fixture(scope="module")
def scorer():
    return TrigramScorer()


def test_verb_artifact_settles_the_ambiguities(book, verbs, transform):
    res = Depth2Resolver(book, verbs)
    assert res.is_verbish("sounds"), "sounds lost its artifact verbhood"
    assert res.is_verbish("upset"), \
        "upset lost its page-7 verbhood (the walk-left canary's fuel)"
    # the mining shadow's residue, recorded (law 1 of Part XI):
    for shadowed in ("imagine", "notice"):
        assert shadowed not in verbs, \
            f"{shadowed} entered the artifact — did the miner learn " \
            f"e-deletion? investigate before celebrating"


def test_assignment_contest_reproduces_the_pin(book, verbs, scorer):
    """Law 1, re-measured: winners match assignment_table.json."""
    pin = json.loads((FIX / "assignment_table.json").read_text(
        encoding="utf-8"))
    strict = reflexive_judge(book)
    deep = depth2_judge(book, verbs)

    def measure(name, judge):
        ok = n = jn = jok = 0
        for g, b in load_paradigm(VENDOR / f"{name}.jsonl"):
            pick = judge(g, b)
            if pick is not None:
                jn += 1
                jok += int(pick == "g")
            else:
                pick = scorer.pick(g, b)
            ok += int(pick == "g")
            n += 1
        return ok / n * 100, jn, (jok / jn * 100 if jn else 0.0)

    print("\nASSIGNMENT TABLE (the HANDOFF prints this):")
    for name, row in pin.items():
        if "strict_frame" not in row:
            continue
        fs, jns, jas = measure(name, strict)
        fd, jnd, jad = measure(name, deep)
        elig_s = jas >= 85 and jns > 0
        elig_d = jad >= 85 and jnd > 0
        if elig_s and not elig_d:
            winner = "strict-frame"
        elif elig_d and not elig_s:
            winner = "depth-2"
        else:
            winner = "depth-2" if fd > fs else "strict-frame"
        print(f"  {name[:40]:40s} strict {fs:5.1f} ({jns:4d} @ "
              f"{jas:5.1f})  depth2 {fd:5.1f} ({jnd:4d} @ {jad:5.1f})"
              f"  -> {winner}")
        assert winner == row["winner"], \
            f"{name}: measured winner {winner} != pinned {row['winner']}"
    # the pinned negative, asserted by name
    assert pin["principle_A_c_command"]["winner"] == "strict-frame"
    assert pin["principle_A_c_command"]["depth_2"][2] < 85, \
        "depth-2 became eligible on c_command — re-run the contest"
    # routing carries the assignment
    for name in DEPTH2_ASSIGNED:
        assert route(name) == "depth2"
    for name in SVA2_ASSIGNED:
        assert route(name) == "sva2"
    assert route("principle_A_c_command") == "reflexive"
    assert route("irregular_plural_subject_verb_agreement_1") == "sv"


def test_depth2_gates(book, verbs, scorer):
    schooled = run_all(scorer, book, blimp_dir=VENDOR, verbs=verbs)
    gates = {
        "principle_A_domain_1": (98, 100),
        "principle_A_domain_2": (61, 73),
        "principle_A_domain_3": (85, 93),
        "irregular_plural_subject_verb_agreement_2": (89, 96),
        "anaphor_number_agreement": (66.8, 85),
        "principle_A_c_command": (63, 85),
    }
    print()
    for name, (floor, jfloor) in gates.items():
        forced, jn, jacc = schooled[name]
        print(f"  {name[:44]:44s} {forced:5.1f}  ({jn:4d} @ "
              f"{jacc:5.1f}%)")
        assert forced >= floor, f"{name}: {forced:.1f} < {floor}"
        if jn:
            assert jacc >= jfloor, f"{name}: judged {jacc:.1f} < {jfloor}"
    # SVA_1 no-harm under the sva2 split (stays with sv)
    assert schooled["irregular_plural_subject_verb_agreement_1"][0] \
        >= 68.6


@pytest.mark.skipif(not BLIMP_DIR.exists(),
                    reason="data/blimp missing — run scripts/fetch_blimp.py")
def test_overall_and_no_harm(book, verbs, scorer):
    ref = json.loads((FIX / "depth2_reference.json").read_text(
        encoding="utf-8"))
    entry = json.loads((FIX / "entry_reference.json").read_text(
        encoding="utf-8"))["schooled"]
    schooled = run_all(scorer, book, verbs=verbs)
    agg = aggregate(schooled)
    print(f"\nFORCED overall: {agg['forced_overall']:.2f}  "
          f"(gate >= 66.4; Part XI 65.93)")
    print(f"SELECTIVE: {agg['coverage_pct']:.1f}% @ "
          f"{agg['judged_acc_pct']:.2f}%  (was 24.2 @ 93.79)")
    assert agg["forced_overall"] >= 66.4
    reassigned = DEPTH2_ASSIGNED | SVA2_ASSIGNED
    for name, (pinned, _, _) in ref["schooled"].items():
        assert abs(schooled[name][0] - pinned) <= 1.5, \
            f"{name} drifted from the Part XII pin"
    for name, (pinned, _, _) in entry.items():
        if name in reassigned:
            continue                 # law 1 superseded their assignment
        assert abs(schooled[name][0] - pinned) <= 1.5, \
            f"{name}: harm against the Part XI pin"


def test_canaries(book, verbs):
    """The session's four broken rulers, pinned as tests. The F3
    margin note rides the docstring: clause-boundary mislabels are a
    confirmed family; reduced relatives are UNOBSERVED in BLiMP —
    recorded, so nobody mistakes absence of failure for coverage."""
    res = Depth2Resolver(book, verbs)
    ws = case_tokens("A lot of patients were hurting themselves")
    assert res.resolve(ws, ws.index("themselves")) == (None, "pl"), \
        "partitive heads stopped resolving plural"
    ws2 = case_tokens("The lady that upset Karla praised herself")
    phi = res.resolve(ws2, ws2.index("herself"))
    assert phi is not None and phi[1] == "sg", \
        "the relative-headed subject was lost behind its relativizer"
    assert res.is_verbish("upset") and res.is_verbish("sounds")
    v = res.violation(case_tokens(
        "The lady that upset Karla praised herself"))
    assert v == 0
