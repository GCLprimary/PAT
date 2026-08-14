"""S-2 acceptance: the corpus registry and the stacking sentinel.

Coherence before volume: sources are built separately under the
contract, combined only explicitly, and the probe-22 finding — a stacked
multi-genre corpus underperforms Brown+SVD on at least one metric — is
kept as a regression sentinel. If stacking ever HELPS under this recipe,
that is a finding to flag, not silently adopt: this test fails loudly.
"""
import numpy as np
import pytest

from mirror import (MeaningGeometry, SOURCES, coherence_report,
                    combine_sources, ensure_source, relatedness,
                    suffix_offsets)
from mirror.config import DATA_DIR


def test_registry_builds_sources_separately():
    for s in SOURCES:
        p = ensure_source(s)
        assert p.exists()
    # brown stays the default corpus; the combined file exists only when
    # explicitly requested
    with pytest.raises(ValueError):
        from mirror.meaning import build_corpus
        build_corpus("wikipedia")


def test_stacking_sentinel():
    """Probe-22 regression sentinel: combined must underperform the
    Brown+SVD default on >= 1 metric."""
    rep = coherence_report()
    print("\ncoherence report:")
    for k in list(SOURCES) + ["combined"]:
        hits, tot = rep[k]["relatedness"]
        offs = "  ".join(f"-{s} {a:+.3f}"
                         for s, (a, _) in rep[k]["offsets"].items())
        print(f"  {k:10s} relatedness {hits}/{tot}   {offs}")
    print(f"  adopt_combined (relatedness rule): {rep['adopt_combined']}")

    brown = rep["brown"]
    combined = rep["combined"]
    worse = []
    if combined["relatedness"][0] < brown["relatedness"][0]:
        worse.append("relatedness")
    for sfx in ("ed", "ing", "s"):
        if combined["offsets"][sfx][0] < brown["offsets"][sfx][0]:
            worse.append(f"-{sfx} offset")
    print(f"  combined worse than brown on: {worse}")
    assert worse, (
        "FINDING TO FLAG: stacking no longer underperforms Brown+SVD "
        "on any metric under the frozen recipe — do not silently adopt; "
        "re-probe coherence policy")
