"""M-3: the count fold (probe 49b) — fold the counts, not the vectors.

The creature lemmatizes the corpus with its own addressing (the
dict-exact fold: bases anchor themselves, members fold in under the
attested-remainder peel) and the dense space is rebuilt over folded
counts. The headline is WS353-REL: relatedness is starved by surface
fragmentation, and folding one family's counts into its anchor feeds
it (+0.08 over the unfolded reference). SimLex stays flat — similarity
was never fragmentation-limited, exactly as forecast. The unfolded
rows remain the reference column (test_meaning_rows); drift in either
column names the meaning organ.

The drift census (M-1's receipt): member-level dense vectors are
context-genre noise — coherence ~34% at count-floor 20 — which is
law 4's own justification: the anchor carries the meaning, and a
member whose margin goes negative gets a RECEIPT ('watering': born of
'water', now nearer 'boil'), never an action.
"""
from collections import defaultdict
from pathlib import Path

import pytest

from mirror.meaning_rows import (corpus_fold, drift_census,
                                 folded_meaning_rows)

VENDOR = Path(__file__).resolve().parent / "fixtures" / "meaning"
BENCH = {
    "WS353-sim": VENDOR / "wordsim353-sim.csv",
    "WS353-rel": VENDOR / "wordsim353-rel.csv",
    "SimLex-999": VENDOR / "simlex999.csv",
}
UNFOLDED = {"WS353-sim": 0.433, "WS353-rel": 0.244, "SimLex-999": 0.160}


@pytest.fixture(scope="module")
def fold(transform, embedder):
    return corpus_fold(transform, embedder.corpus)


def test_folded_sentinel_rows(fold):
    rows, n_folded = folded_meaning_rows(fold, BENCH)
    print(f"\nfold: {n_folded} surface types folded into anchors")
    for name, (n, cov, rho) in rows.items():
        print(f"  {name:11s} covered {cov:4d}   rho {rho:+.3f}   "
              f"(unfolded {UNFOLDED[name]:+.3f}, "
              f"delta {rho - UNFOLDED[name]:+.3f})")
    assert n_folded >= 15_000, f"the fold shrank ({n_folded} types)"
    assert rows["WS353-rel"][2] >= 0.30, \
        f"THE FOLD'S HEADLINE FAILED: WS353-rel " \
        f"{rows['WS353-rel'][2]:+.3f} < 0.30 — folded counts stopped " \
        f"feeding relatedness"
    assert rows["WS353-sim"][2] >= 0.43
    assert abs(rows["SimLex-999"][2] - 0.16) <= 0.03, \
        "SimLex left its band — it was forecast FLAT under the fold"


def test_drift_census(transform):
    """Receipts, not actions: size recorded, coherence recorded — the
    number that justifies law 4 (member vectors are context-genre
    noise; the anchor carries the meaning)."""
    byb = defaultdict(dict)
    for b, s, w, _ in transform.pairs:
        byb[b][s] = w
    fams = [(b, d) for b, d in byb.items() if len(d) >= 3][:300]
    n, coherence, drift = drift_census(fams)
    print(f"\ndrift census: {n} members checked, coherence "
          f"{coherence:.1f}%, {len(drift)} drift receipts")
    for d in sorted(drift, key=lambda x: x["margin"])[:4]:
        print(f"   {d['word']!r}: born of {d['anchor']!r}, now nearer "
              f"{d['nearer']!r} (margin {d['margin']:+.3f})")
    assert n >= 150
    assert coherence <= 60.0, \
        "member-level coherence rose past the law's premise — " \
        "re-examine law 4 before trusting centroids anywhere"
    assert drift, "an empty drift census at 34% coherence is impossible"
    for d in drift:
        assert d["margin"] < 0