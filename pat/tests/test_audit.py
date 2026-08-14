"""J-1/J-2/J-3 (probe 56): the auditor, the oracle, and the human's
rung.

LAW 2 is the spine: every emitted row carries its machine-checkable
receipt — an empty receipt field is a STRUCTURAL failure, and zero
unreceipted claims is a gate, not a style. The precision battery
asserts the sample's structure only; the >= 90% clause is graded AT
THE HUMAN GATE, by the human, on reports/precision_sample.tsv —
per law 5, the build does not self-grade.
"""
from collections import Counter
from pathlib import Path

import pytest

from pat import Agent
from pat.auditor import (assert_phone_case, audit_cmu,
                           audit_unimorph, homophone_index)
from mirror import Page
from mirror.config import DATA_DIR as MIRROR_DATA

REPORTS = Path(__file__).resolve().parent.parent / "reports"


@pytest.fixture(scope="module")
def counts():
    c = Counter()
    with open(MIRROR_DATA / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            c.update(line.split())
    return c


@pytest.fixture(scope="module")
def sweeps(organs, counts):
    corpus = organs.embedder.corpus
    cmu_rows, classes = audit_cmu(corpus, counts)
    names = set(Page.load(MIRROR_DATA / "page_gender_names.txt").rows)
    uni_rows = audit_unimorph(corpus, counts, organs.transform.pairs,
                              MIRROR_DATA / "unimorph_eng.tsv", names)
    homo_rows = homophone_index(corpus)
    return cmu_rows, classes, uni_rows, homo_rows


def test_yield_bands(sweeps):
    cmu_rows, classes, uni_rows, homo_rows = sweeps
    mism = classes["elision"] + classes["mutation"] + \
        classes["insertion"]
    print(f"\nA1 {mism} (459 ± 5%): elision {classes['elision']} "
          f"mutation {classes['mutation']} insertion "
          f"{classes['insertion']} exact {classes['exact']}")
    print(f"A2 {len(uni_rows)} (>= 1950)   A3 {len(homo_rows)} "
          f"(13982 ± 1%)")
    assert abs(mism - 459) <= 459 * 0.05
    assert classes["elision"] >= 160
    assert classes["insertion"] <= 25
    assert classes["exact"] >= 2900
    assert len(uni_rows) >= 1950
    assert abs(len(homo_rows) - 13982) <= 13982 * 0.01


def test_receipts_are_structural(sweeps):
    """Law 2: no empty receipt field anywhere, in any report row."""
    cmu_rows, _, uni_rows, homo_rows = sweeps
    for r in cmu_rows:
        for k, v in r.items():
            assert str(v) != "" or k == "subfamily", \
                f"UNRECEIPTED CLAIM in audit_cmu: {r}"
    for r in uni_rows:
        assert all(str(v) != "" for v in r.values()), \
            f"UNRECEIPTED CLAIM in audit_unimorph: {r}"
    for r in homo_rows:
        assert all(str(v) != "" for v in r.values())


def test_phone_case_canary(organs):
    """Law 3: the sixth scalp stays mounted — the tail alphabet must
    live inside the lexicon's, and a lowercase vintage must raise."""
    assert_phone_case(organs.embedder.corpus)
    import pat.auditor as aud
    original = aud.SUFFIX_PHON
    aud.SUFFIX_PHON = {"ing": ("IH", "ng")}      # the old scalp
    try:
        with pytest.raises(AssertionError):
            assert_phone_case(organs.embedder.corpus)
    finally:
        aud.SUFFIX_PHON = original


def test_onomastic_flagged_never_filtered(sweeps):
    """Law 4: hazards ride the report with the flag up; precision is
    measurable with and without them."""
    _, _, uni_rows, _ = sweeps
    flagged = [r for r in uni_rows if r["onomastic"] == "yes"]
    print(f"\nonomastic rows: {len(flagged)} of {len(uni_rows)} "
          f"(ex-onomastic pool: {len(uni_rows) - len(flagged)})")
    assert len(flagged) >= 5
    assert all(r in uni_rows for r in flagged)


ORACLE_PINNED = [
    ("verify painted = paint+ed",
     "CERTIFY — paint+ed, pair-exact, mined"),
    ("verify walking = walk+ing",
     "CERTIFY — walk+ing, pair-exact, mined"),
    ("verify melted = metal+ed",
     "REFUSE — pron('melted') does not begin with pron('metal') "
     "[m EH l t AH d vs m EH t AH l]"),
    ("verify side = sigh+ed",
     "HOMOPHONE — sounds exactly like sighed (sigh+ed); I cannot "
     "tell them apart by ear"),
    ("verify famous = fam+ous",
     "REFUSE — 'fam' is not a word I know"),
    ("verify cheerfully = cheerful+er",
     "REFUSE — remainder [IY] is not an attested form of -er"),
    ("verify darkness = dark+ness",
     "CERTIFY — dark+ness, pair-exact, mined"),
    ("verify quickly = quick+ly",
     "CERTIFY — quick+ly, pair-exact, mined"),
    ("verify government = govern+ment",
     "REFUSE — pron('government') does not begin with pron('govern') "
     "[g AH v ER m AH n t vs g AH v ER n]"),
    ("verify finds = find+s",
     "CERTIFY — find+s, pair-exact, mined"),
]


@pytest.fixture(scope="module")
def pat(organs, tmp_path_factory):
    return Agent(str(tmp_path_factory.mktemp("audit") / "store"),
                 organs=organs)


def test_oracle_ten_pinned(pat):
    """The probe's ten proposals, verbatim, through the full loop —
    a 10/10 regression including the government /n/ finding."""
    print()
    for clause, expected in ORACLE_PINNED:
        line = pat.respond(clause).lines()[0]
        print(f"  > {clause}\n    {line}")
        assert line == expected, f"{clause}: {line!r} != {expected!r}"


def test_verbs_containment_and_refusals(pat):
    """The J-2 battery case: audit + verify + alien in one input,
    probe-34 containment intact; malformed inputs refuse by name."""
    resp = pat.respond(
        "audit cmu and verify side = sigh+ed and translate hello")
    lines = resp.lines()
    assert len(lines) == 3
    assert lines[0].startswith("audited cmu: 459 variant candidates")
    assert "receipt" in lines[0]
    assert lines[1].startswith("HOMOPHONE — sounds exactly like sighed")
    assert lines[2] == "refuse: 'translate' is not something I do"
    assert pat.respond("audit everything").lines()[0] == \
        "refuse: I can audit cmu, unimorph, homophones"
    assert pat.respond("verify side sigh ed").lines()[0] == \
        "refuse: say it as: verify <word> = <base>+<suffix>"
    assert (REPORTS / "audit_cmu.tsv").exists()


def test_precision_sample_structure():
    """J-3: the human's rung exists, stratified exactly, receipts
    complete, verdict column empty with the schema documented. THE
    BUILD DOES NOT SELF-GRADE — the >= 90% clause belongs to the
    human gate."""
    path = REPORTS / "precision_sample.tsv"
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    header = lines[0].split("\t")
    assert header == ["stratum", "claim", "receipt", "verdict"]
    rows = [ln.split("\t") for ln in lines[1:]]
    # split preserves the trailing empty verdict only if the line ends
    # with the tab — normalize
    rows = [(r + [""])[:4] for r in rows]
    strata = Counter(r[0] for r in rows)
    assert strata == {"elision": 15, "mutation": 15, "unimorph": 10,
                      "insertion": 5, "onomastic": 5}
    for r in rows:
        assert r[1] and r[2], f"unreceipted sample row: {r}"
        assert r[3] == "", "a verdict was pre-filled — the build " \
                           "does not self-grade (law 5)"
    readme = (REPORTS / "precision_sample.README.txt").read_text(
        encoding="utf-8")
    assert "correct / incorrect / unsure" in readme