"""X-3 acceptance (probe 46): pages must pass the counts.

The auditor walks the pinned corpus and measures a rule's consonance
before any page wearing it may ship. The founding precedent, asserted:
MODAL->bare is a LAW (98.4%), PERF->ed strong (88.4%, banded), and the
textbook class BE->ing is REFUTED (20.2% — 'be' takes a disjunction:
progressive/passive/predication). The LawBook enforces the verdict: a
page whose audited rule sits below the floor is refused at load, by
name and number. Attestation examines the teacher too.
"""
import pytest

from mirror import (AUDIT_FLOOR, LawBook, Page, audit_rule,
                    build_form_lexicon, BE_AUX, MODAL_AUX, PERF_AUX)
from mirror.agreement import build_number_lexicon
from mirror.config import DATA_DIR


@pytest.fixture(scope="module")
def forms(transform):
    return build_form_lexicon(transform.pairs)


@pytest.fixture(scope="module")
def sents():
    with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
        return [l.split() for l in f][:60000]


def test_modal_is_a_law(sents, forms):
    pct, n = audit_rule(sents, MODAL_AUX, "bare", forms)
    print(f"\nMODAL->bare: {pct:.1f}% (n={n})")
    assert n >= 1000
    assert pct >= 97.0, f"MODAL->bare consonance {pct:.1f}% < 97"


def test_perf_is_strong_banded(sents, forms):
    pct, n = audit_rule(sents, PERF_AUX, "ed", forms)
    print(f"\nPERF->ed: {pct:.1f}% (n={n})")
    assert n >= 1000
    assert 85.0 <= pct <= 89.0, \
        f"PERF->ed left its band: {pct:.1f}% not in 87 ± 2"


def test_be_canary_the_refutation(sents, forms, transform):
    """The fixture IS the refutation: a hypothetical BE->ing page
    audits under 30% and the LawBook refuses to load it, naming the
    number. The textbook was wrong; the counts said so."""
    pct, n = audit_rule(sents, BE_AUX, "ing", forms)
    print(f"\nBE->ing: {pct:.1f}% (n={n}) — REFUTED")
    assert n >= 1000
    assert pct < 30.0, \
        f"BE->ing audited at {pct:.1f}% — the refutation weakened?"

    sg, pl, _ = build_number_lexicon(transform.pairs)
    bad_page = Page("be_progressive", {"is": "be_aux", "are": "be_aux"},
                    rule="be-takes-ing", audit=pct)
    with pytest.raises(ValueError) as err:
        LawBook([bad_page], sg, pl)
    msg = str(err.value)
    print(f"refusal: {msg}")
    assert "REFUSED" in msg and f"{pct:.1f}" in msg \
        and f"{AUDIT_FLOOR:.0f}" in msg


def test_audited_good_page_loads(sents, forms, transform):
    """The floor refuses refuted rules, not audited-good ones."""
    pct, _ = audit_rule(sents, MODAL_AUX, "bare", forms)
    sg, pl, _ = build_number_lexicon(transform.pairs)
    page = Page("modal_bare", {"will": "modal"}, rule="modal-takes-bare",
                audit=pct)
    book = LawBook([page], sg, pl)
    assert book.page_named("modal_bare") is not None
