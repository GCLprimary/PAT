"""L-1 acceptance (probes 42-43): pages, the LawBook, and the ledger.

Pages are law-class artifacts: pinned files, checksummed, loaded with
their conflict ledger in hand (lessons never load silently). Pages
override induced CLASSIFICATIONS and never attested PAIRS; the
lesson-corrects-induction canary asserts the ledger names people, men,
and children — each one a word the -s miner classed singular because a
derived pair exists (men+s -> mens: derivation evidence misread as
number evidence, corrected by one taught line).
"""
import hashlib
import json

import pytest

from mirror import LawBook, Page
from mirror.agreement import build_number_lexicon, number_of
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def induced(transform):
    sg, pl, _ = build_number_lexicon(transform.pairs)
    return sg, pl


@pytest.fixture(scope="module")
def pages():
    return [Page.load(DATA_DIR / "page_demonstratives.txt"),
            Page.load(DATA_DIR / "page_irregular_plurals.txt")]


@pytest.fixture(scope="module")
def lawbook(pages, induced):
    return LawBook(pages, *induced)


def test_page_checksums_pinned(pages):
    pinned = json.loads((FIX / "page_checksums.json").read_text(
        encoding="utf-8"))
    for name, expected in pinned.items():
        got = hashlib.sha256(
            (DATA_DIR / name).read_bytes()).hexdigest()
        assert got == expected, \
            f"{name} drifted from its pin — a lesson is an artifact"
    assert pages[0].n_lines == 4 and len(pages[0]) == 4
    assert pages[1].n_lines == 52 and len(pages[1]) == 104


def test_conflict_ledger_corrects_induction(lawbook, induced):
    """Law 2: the ledger is nonempty on the page known to correct the
    lexicon, contains >= 3 entries, and names people/men/children —
    each verified against the induced classification here."""
    sg, pl = induced
    conflicts = lawbook.conflicts()
    words = {w for w, _, _ in conflicts}
    print(f"\nconflict ledger ({len(conflicts)}):")
    for c in conflicts:
        print("  ", c)
    assert len(conflicts) >= 3, "the conflict ledger went quiet"
    assert {"people", "men", "children"} <= words, \
        f"the canary names are missing from {words}"
    page2 = [c for c in lawbook.conflict_ledger
             if c[3] == "irregular_plurals"]
    assert page2, \
        "page #2 loaded with an empty ledger — a page known to " \
        "correct the lexicon corrected nothing (law 2 failure)"
    for word, page_says, induced_says, _ in lawbook.conflict_ledger:
        got = number_of(word, sg, pl)
        assert f"induced:{got}" == induced_says, \
            f"ledger entry for '{word}' misquotes the induced lexicon"
        assert page_says != induced_says


def test_page_first_then_fallthrough(lawbook, induced):
    """On-page words are ruled by the page; off-page words fall through
    to `agreement.number_of` UNCHANGED (wraps, does not modify)."""
    sg, pl = induced
    assert lawbook.number_of("men") == "pl"
    assert lawbook.number_of("this") == "sg"
    assert lawbook.number_of("those") == "pl"
    assert lawbook.provenance_of("men") == "lesson:irregular_plurals"
    on_page = set(lawbook._page_num)
    checked = 0
    for word in list(sorted(sg))[:200] + list(sorted(pl))[:200]:
        if word in on_page:
            continue
        assert lawbook.number_of(word) == number_of(word, sg, pl)
        checked += 1
    assert lawbook.number_of("qqqzz") is None
    assert lawbook.provenance_of("qqqzz") is None
    print(f"\n{checked} off-page words fall through unchanged")


def test_export_readable(lawbook):
    text = lawbook.export()
    assert "demonstratives" in text and "irregular_plurals" in text
    assert "OVERRIDES" in text
    assert "conflict ledger:" in text
    print("\n" + "\n".join(text.splitlines()[-6:]))
