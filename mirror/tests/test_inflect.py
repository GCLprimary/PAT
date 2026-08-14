"""E-1 (probes 51/53): the inflection table — orthography, induced.

Law 1: the mining projection has a shadow (it cannot see moved/making/
stopped/carries), so this ruler's table is induced from ITS OWN
attested pairs — the vendored UniMorph train split — never from mined
pairs. Selective by signature; irregulars ride page 7, and UniMorph is
data, never a lesson source. The table exports readably (the model is
the page): a doubling row, an e-deletion row, and a y-replacement row
must be visible in it.
"""
import hashlib
import json

import pytest

from mirror import InflectionTable, LawBook, Page
from mirror.agreement import build_number_lexicon
from mirror.config import DATA_DIR


@pytest.fixture(scope="module")
def table():
    manifest = json.loads(
        (DATA_DIR / "fixtures" / "unimorph_manifest.json").read_text(
            encoding="utf-8"))
    h = hashlib.sha256()
    with open(DATA_DIR / "unimorph_eng.tsv", "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == manifest["unimorph_eng.tsv"], \
        "the vendored UniMorph file drifted from its manifest"
    return InflectionTable().fit()


def test_held_out_gates(table):
    floors = {"V;PST": 89.0, "V;PRS;3;SG": 96.0,
              "V;V.PTCP;PRS": 96.0, "N;PL": 97.0}
    tot_ok = tot_ans = tot_n = 0
    print()
    for tag, floor in floors.items():
        ok, wrong, refused, n = table.evaluate(tag)
        forced = ok / n * 100
        tot_ok += ok
        tot_ans += ok + wrong
        tot_n += n
        print(f"  {tag:14s} forced {forced:5.2f}%  refused {refused}  "
              f"rows {len(table.rules[tag])}")
        assert forced >= floor, f"{tag}: {forced:.2f} < {floor}"
    overall = tot_ok / tot_n * 100
    coverage = tot_ans / tot_n * 100
    print(f"  OVERALL forced {overall:.2f}%  coverage {coverage:.2f}%  "
          f"rows {table.n_rows()}")
    assert overall >= 95.5, f"overall forced {overall:.2f} < 95.5"
    assert coverage >= 99.0, f"coverage {coverage:.2f} < 99"


def test_page_seven_rides_first(table, transform):
    """Irregulars ride pages: with page 7 consulted first, held-out
    V;PST moves ~+0.3 (the common irregulars live in train — the
    page's real payoff is the two perfect BLiMP paradigms)."""
    page = Page.load(DATA_DIR / "page_past_irregulars.txt")
    past_map = {b: label.split(",")[0].strip()
                for b, label in page.rows.items()}
    ok0, _, _, n0 = table.evaluate("V;PST")
    ok1, _, _, n1 = table.evaluate("V;PST", overrides=past_map)
    print(f"\nV;PST table-only {ok0/n0*100:.1f}%  page-7-first "
          f"{ok1/n1*100:.1f}%")
    assert ok1 >= ok0, "page 7 HURT the held-out set — investigate"


def test_export_is_the_page(table):
    """~300+ readable rows; doubling, e-deletion, and y-replacement
    must all be visible in the export."""
    text = table.export()
    assert table.n_rows() >= 250
    assert "Ced" in text or "Cing" in text     # doubling
    assert "e_ing" in text or " d " in text    # e-deletion family
    assert "ied" in text or "ies" in text      # y-replacement
    sample = "\n".join(text.splitlines()[:12])
    print(f"\n{table.n_rows()} rows; head:\n{sample}")


def test_unimorph_is_never_a_lesson(table):
    """No page may be authored from UniMorph — the pages that exist
    carry transcription provenance in their headers, asserted here as
    a standing reminder rather than a mechanism (the mechanism is
    review; the reminder is this test's docstring)."""
    for name in ("page_past_irregulars", "page_irregular_plurals"):
        header = (DATA_DIR / f"{name}.txt").read_text(
            encoding="utf-8").split("\n\n")[0]
        assert "NOT mined" in header
