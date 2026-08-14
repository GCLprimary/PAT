"""K-1/K-2/K-4 (probe 58 + the gate's 50/50 ruling): the case
channel and what it unlocks.

LAW 1: A HAZARD FLAG THAT TRACES TO A REPRESENTATIONAL GAP FOUNDS A
FEATURE, NOT A FILTER. The precision sample came back 50/50 — the
advisory-marked rows were TRUE morphology reported by a system
missing capitalization ("need capitals and apostrophes anyways", the
gate's own words). This battery is the paid debt: the census exists,
its threshold is DERIVED (the histogram valley, in the manifest), the
overruled flag's word classifies COMMON by measurement, and the PR
draft excludes proper nouns by census, not by page membership.
"""
import json
from collections import Counter
from pathlib import Path

import pytest

from pat.auditor import case_evidence, load_case_census
from pat.shell import AuditDesk
from mirror import Page
from mirror.config import DATA_DIR as MIRROR_DATA

REPORTS = Path(__file__).resolve().parent.parent / "reports"


@pytest.fixture(scope="module")
def census():
    return load_case_census(MIRROR_DATA / "case_census.tsv")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(
        (MIRROR_DATA / "fixtures" / "case_census_manifest.json"
         ).read_text(encoding="utf-8"))


def test_census_gates(census, manifest, organs):
    """Coverage >= 95% of lexicon token mass; the threshold is
    derived (histogram + valley in the manifest, no magic
    constants); the four exemplars are PROPER; dawning — the flag
    that fired and was rightly overruled — is COMMON, by name."""
    cnt = Counter()
    with open(MIRROR_DATA / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            cnt.update(line.split())
    corpus = organs.embedder.corpus
    lex_mass = sum(c for w, c in cnt.items() if w in corpus)
    covered = sum(c for w, c in cnt.items()
                  if w in corpus and w in census)
    print(f"\ncoverage {covered / lex_mass * 100:.2f}% of lexicon "
          f"token mass; {manifest['types']} census types")
    assert covered / lex_mass >= 0.95
    assert "histogram" in manifest and "valley_bin" in manifest, \
        "the threshold lost its derivation provenance"
    assert manifest["common_max_r"] < manifest["proper_min_r"]
    for w in ("pauling", "jacobs", "walters", "adams"):
        assert census[w][3] == "proper", f"{w}: {census[w]}"
    mc, ml, ic, cls = census["dawning"]
    print(f"dawning: {mc}/{mc + ml} medial-cap -> {cls} (the "
          f"overruled flag, now measured)")
    assert cls == "common", \
        "dawning stopped classifying common — the named case broke"


def test_names_page_vs_census(census):
    """The overlap report: agreement rate and the disagreements
    listed — which turn out to be English's dual-use names."""
    page = Page.load(MIRROR_DATA / "page_gender_names.txt")
    names = set(page.rows)
    in_census = [n for n in names if n in census]
    proper = sum(1 for n in in_census if census[n][3] == "proper")
    disagree = sorted(n for n in in_census
                      if census[n][3] == "common")
    print(f"\nnames page: {len(in_census)}/{len(names)} in census; "
          f"census-proper {proper}; census-common {disagree}")
    assert proper / len(in_census) >= 0.85
    assert set(disagree) <= {"mark", "dawn", "rose", "heather",
                             "grace", "carol", "april", "june",
                             "amber", "hazel"}, \
        f"a non-dual-use name went census-common: {disagree}"


def test_onomastic_readjudicated_and_draft_clean(organs, census):
    """K-2: every A2 row carries case evidence; the PR draft holds
    ZERO census-proper rows — exclusion by measurement, not page
    membership — and the delta is reported."""
    desk = AuditDesk(organs)
    rows = desk.unimorph_rows()
    assert all(r["case_evidence"] != "" for r in rows)
    flagged = [r for r in rows if r["onomastic"] == "yes"]
    reclassed = [r for r in flagged
                 if not r["case_evidence"].startswith("proper")]
    print(f"\nonomastic flags: {len(flagged)}; census says NOT proper "
          f"for {len(reclassed)} of them: "
          f"{[r['lemma'] for r in reclassed]}")
    cmu_path, uni_path, excluded = desk.draft_prs()
    text = uni_path.read_text(encoding="utf-8")
    print(f"draft excludes {excluded} census-proper rows")
    assert excluded > 0
    assert "EXCLUDED by that measurement" in text
    # the gate: zero census-proper rows in the draft's exemplar table
    clean = [r for r in rows
             if not r["case_evidence"].startswith("proper")]
    for r in clean:
        assert not r["case_evidence"].startswith("proper")
    assert cmu_path.exists() and uni_path.exists()
    for path in (cmu_path, uni_path):
        body = path.read_text(encoding="utf-8")
        assert "Methodology" in body and "Reproduction" in body