"""W-4 + S-1 acceptance: the count geometry and the SVD densifier.

S-1 (probe 22, recipe frozen): dense suffix-offset agreement >= +0.05
for each of -ed/-ing/-s with |random floor| <= 0.01 (measured
.076/.066/.082); dense relatedness >= 18/20. The sparse stage keeps the
ternary-zero and content-only laws (structural asserts) and its offsets
are reported for the record (the probe-22 baseline the SVD tripled).

The 24 curated W-4 triples were fixed a priori in the accepted build and
are kept unchanged.
"""
import numpy as np
import pytest

from mirror import MeaningGeometry, relatedness, suffix_offsets

# (word, related, random) — fixed in the accepted build, unchanged
TRIPLES = [
    ("water", "surface", "chairman"), ("war", "civil", "butter"),
    ("music", "songs", "cattle"), ("money", "tax", "shoulder"),
    ("school", "students", "storm"), ("church", "god", "engine"),
    ("doctor", "medical", "cotton"), ("road", "street", "poetry"),
    ("child", "children", "senate"), ("night", "morning", "acid"),
    ("house", "home", "oxygen"), ("book", "books", "harbor"),
    ("city", "town", "grain"), ("government", "federal", "piano"),
    ("business", "company", "prayer"), ("court", "judge", "kitchen"),
    ("college", "university", "winter"), ("farm", "land", "editor"),
    ("science", "research", "dinner"), ("blood", "body", "railroad"),
    ("door", "room", "congress"), ("horse", "race", "cell"),
    ("summer", "spring", "jury"), ("food", "meat", "colonel"),
]


@pytest.fixture(scope="module")
def sparse_geometry():
    return MeaningGeometry(dense=False)


def test_s1_dense_acceptance(geometry):
    """The probe-22 headline, asserted: compression buys what corpus
    volume couldn't."""
    assert geometry.dim == 300
    hits, tot = relatedness(geometry, np.random.default_rng(7))
    print(f"\ndense relatedness: {hits}/{tot}")
    assert hits >= 18, f"dense relatedness {hits}/{tot} < 18/20"
    offs = suffix_offsets(geometry, np.random.default_rng(7))
    for sfx in ("ed", "ing", "s"):
        agree, floor = offs[sfx]
        print(f"  -{sfx}: {agree:+.3f} (random {floor:+.3f})")
        assert agree >= 0.05, f"-{sfx} offset agreement {agree:+.3f} < +0.05"
        assert abs(floor) <= 0.01, f"-{sfx} random floor {floor:+.3f} > 0.01"


def test_relatedness_triples(geometry):
    """W-4's curated-triple gate, now on the default (dense) space."""
    usable = [(w, r, x) for w, r, x in TRIPLES
              if w in geometry and r in geometry and x in geometry]
    assert len(usable) >= 20, f"only {len(usable)} usable triples (< 20)"
    wins = 0
    losses = []
    for w, r, x in usable:
        vw = geometry.vec(w)
        if float(vw @ geometry.vec(r)) > float(vw @ geometry.vec(x)):
            wins += 1
        else:
            losses.append((w, r, x))
    rate = wins / len(usable)
    print(f"\ncurated relatedness: {wins}/{len(usable)} = {rate:.0%}  "
          f"losses: {losses}")
    assert rate >= 0.90, f"relatedness {rate:.0%} < 90%"


def test_sparse_baseline_report(sparse_geometry):
    """Report-only: the sparse offsets the SVD tripled (probe-22
    baseline ~+0.022), for the record."""
    hits, tot = relatedness(sparse_geometry, np.random.default_rng(7))
    offs = suffix_offsets(sparse_geometry, np.random.default_rng(7))
    print(f"\nsparse relatedness: {hits}/{tot}  [report-only]")
    for sfx, (agree, floor) in offs.items():
        print(f"  -{sfx}: {agree:+.3f} (random {floor:+.3f})  [report-only]")


def test_ternary_zero_and_content_laws(sparse_geometry):
    """The laws live at the sparse (count) stage: unseen pairs stay
    exactly zero, and stop-word contexts are never counted at all
    (probe-22 count-time exclusion — structural)."""
    geo = sparse_geometry
    assert np.all(geo.counts[:, :geo.content_cut] == 0), \
        "stop-word context columns carry counts — count-time cut failed"
    w = "water"
    v = geo.sparse_vec(w)
    counts = geo.counts[geo.vi[w]]
    assert np.all(v[counts == 0] == 0.0), "an unseen pair got a nonzero value"
    assert np.all(v >= 0.0), "PPMI went negative — not a P-PMI anymore"
    assert np.isclose(np.linalg.norm(v), 1.0)


def test_dense_flag_keeps_sparse_available(geometry):
    """S-1: dense is default, sparse stays reachable on the same object."""
    v_dense = geometry.vec("water")
    v_sparse = geometry.sparse_vec("water")
    assert v_dense.shape == (300,)
    assert v_sparse.shape == (len(geometry.vocab),)
