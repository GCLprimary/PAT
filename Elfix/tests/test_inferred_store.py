"""Tests for Stage 4, the inferred-pronunciation store (elfix/lexicon/inferred_store).
These pin the LAW guarantees — separation, no-shadow, no-compounding, ternary
evidence with absence != zero, and malleable->confirmed promotion."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.lexicon.inferred_store import InferredStore


def test_never_shadows_attested():
    s = InferredStore({"cat": ["k", "AE", "t"]})
    assert s.propose("cat", ["x"], "c", "at", "d1") == "attested"   # refused
    assert s.lookup("cat") == (["k", "AE", "t"], "attested")
    assert s.evidence("cat") == 1


def test_ternary_evidence_distinguishes_absence_from_zero():
    s = InferredStore({"cat": ["k", "AE", "t"]})
    assert s.evidence("cat") == 1            # attested  +1
    assert s.evidence("zzz") is None         # absent    None  (Law 2: != 0)
    s.propose("cats", ["k", "AE", "t", "s"], "cat", "s", "d1")
    assert s.evidence("cats") == 0           # inferred  0


def test_conflicting_pron_is_evidenced_against():
    s = InferredStore({})
    s.propose("w", ["a"], "x", "s", "d1")
    assert s.propose("w", ["b"], "y", "s", "d2") == "rejected"   # contradiction
    assert s.evidence("w") == -1
    assert s.lookup("w") == (None, "absent") or s.lookup("w")[1] == "absent"


def test_corroboration_promotes_malleable_to_confirmed():
    s = InferredStore({})
    s.propose("w", ["a"], "x", "s", "d1")
    assert s.lookup("w")[1] == "inferred:malleable"
    s.propose("w", ["a"], "y", "es", "d2")                       # 2nd agreeing source
    assert s.lookup("w")[1] == "inferred:confirmed"


def test_confirmed_view_excludes_malleable():
    s = InferredStore({"cat": ["k", "AE", "t"]})
    s.propose("cats", ["k", "AE", "t", "s"], "cat", "s", "d1")   # malleable
    v = s.confirmed_view()
    assert "cat" in v and "cats" not in v                        # malleable not growable
    s.propose("cats", ["k", "AE", "t", "s"], "cat", "es", "d2")  # corroborate
    assert "cats" in s.confirmed_view()


def test_grow_does_not_compound_inferred():
    """The error-cascade trap: 'running' is inferred from the attested 'run', but
    'runnings' must NOT then be built from the inferred 'running' (attested-only
    generation). It stays absent."""
    s = InferredStore({"run": ["r", "AH", "n"]})
    s.grow(["running"])
    assert s.lookup("running")[1].startswith("inferred")
    s.grow(["runnings"])
    assert s.evidence("runnings") is None        # not built from an inferred stem
