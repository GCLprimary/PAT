"""K-3 (probe 58): the apostrophe organ — page-taught contractions,
mined clitic, censused ambiguities.

LAW 4: THE CLITIC OBEYS THE THIRDS — the four induced rows are
asserted by name (voiced->z, voiceless->s, sibilant->IH-z,
affricate->AH-z; the affricate epenthesis canary's third
confirmation). The tiny contraction classes are page-taught, never
mined; the possessive-vs-is ambiguity and the plural s' are censused
to the frames lane, never guessed. Registration is opt-in: the
shipped six-suffix gate must remain untouched (no-harm is a gate,
verified structurally here and by the full suites).
"""
from collections import Counter

import pytest

from mirror import Page, PhonGate
from mirror.clitic import (apostrophe_census, clitic_table,
                           frames_lane_census, mine_clitic_pairs,
                           register_clitic, CLITIC)
from mirror.config import DATA_DIR


@pytest.fixture(scope="module")
def counts():
    c = Counter()
    with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            c.update(line.split())
    return c


@pytest.fixture(scope="module")
def clitic_pairs(embedder, counts):
    return mine_clitic_pairs(embedder.corpus, counts)


def test_yield_and_the_four_rows(embedder, clitic_pairs):
    print(f"\nclitic pairs: {len(clitic_pairs)} (gate >= 480)")
    assert len(clitic_pairs) >= 480
    modal, support = clitic_table(embedder.corpus, clitic_pairs)
    print(f"the four rows: " + "  ".join(
        f"{cls}->{' '.join(modal[cls])}" for cls in
        ("voiced", "voiceless", "sibilant", "affricate")))
    assert modal["voiced"] == ("z",)
    assert modal["voiceless"] == ("s",)
    assert modal["sibilant"] == ("IH", "z")
    assert modal["affricate"] == ("AH", "z"), \
        "the affricate epenthesis canary broke on its third confirmation"


def test_contraction_page_taught_never_mined(embedder):
    page = Page.load(DATA_DIR / "page_contractions.txt")
    assert page.rule == "contraction-expansion"
    assert page.rows["can't"] == "can+not"
    assert page.rows["won't"] == "will+not"     # not wo+not
    assert page.rows["'d"] == "would or had"    # honest ambiguity
    assert len(page) >= 20
    header = (DATA_DIR / "page_contractions.txt").read_text(
        encoding="utf-8").split("\n\n")[0]
    assert "never mined" in header or "NOT mined" in header


def test_registration_is_opt_in_and_analyzes(embedder, transform,
                                             clitic_pairs):
    """analyze john's under a registered gate -> john + 's, receipt
    carried; the SHIPPED gate stays six-suffix."""
    gate = PhonGate.from_transform(transform)
    register_clitic(gate, embedder.corpus, clitic_pairs)
    obs = list(embedder.corpus["john's"])
    res = gate.check_bound(obs, embedder.corpus["john"], CLITIC)
    assert res.ok
    assert gate.verdict("john's", "BOUND", "john", CLITIC) == "OK"
    assert gate.surface_of("john", CLITIC) == "john's"
    shipped = PhonGate.from_transform(transform)
    assert CLITIC not in shipped.attested, \
        "the clitic leaked into the SHIPPED gate — no-harm broken"
    assert len(shipped.attested) == 6


def test_censuses_recorded_not_guessed(embedder, counts):
    classes = apostrophe_census(embedder.corpus)
    total = sum(classes.values())
    print(f"\napostrophe census ({total} types): {dict(classes)}")
    assert total >= 8000
    assert classes[CLITIC] >= 6000
    assert classes["n't"] == 20                # page-taught, never mined
    lane = frames_lane_census(embedder.corpus, counts)
    print(f"frames-lane census (flagged, never guessed): {lane}")
    assert lane["plural_possessive_s_prime_types"] > 0
    assert lane["possessive_vs_is_token_mass"] > 0