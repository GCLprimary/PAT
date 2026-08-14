"""The Tier 3 gate as a test: it must RUN and produce comparable F1s.
We assert geometry is computed and non-degenerate; we do NOT hard-assert PASS,
because the gate is an experiment, not an invariant (honest discipline)."""
import sys, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("m1", ROOT / "scripts" / "milestone1.py")
m1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m1)
from elfix.data_io import load_cmu, build_morpheme_gold
from elfix.emergent.emergent_unit import (
    geometry_boundaries, geometry_boundaries_emergent, discover, auto_quanta)
from elfix.trajectory.trajectory import Trajectory

def test_gate_runs_and_scores():
    cmu = load_cmu(); gold = build_morpheme_gold(cmu)
    assert len(gold) > 100
    p, r, f, gran = m1.score(gold, geometry_boundaries)
    assert 0.0 <= f <= 1.0 and gran > 1.0


def test_emergent_is_a_refinement_of_contour():
    """Tier 3 wiring invariant: emergent boundaries are a SUBSET of contour ones
    (discover() may WITHHOLD a seam, never invent one), and 'both-sides' gating
    is stricter than 'either'. A refinement, not a new boundary source."""
    corpus = list(load_cmu().values())
    q = auto_quanta([Trajectory.of(w) for w in corpus[:8000]])
    inv = discover(corpus[:8000], quanta=q)
    assert len(inv) > 0
    for ph in corpus[:5000]:
        c = set(geometry_boundaries(ph))
        e = set(geometry_boundaries_emergent(ph, inv, q))
        eb = set(geometry_boundaries_emergent(ph, inv, q, both_sides=True))
        assert e <= c, (ph, e - c)          # emergent ⊆ contour
        assert eb <= e                       # both-sides ⊆ either-side


def test_emergent_empty_inventory_equals_contour():
    """Degenerate case (Law-honest): with nothing discovered, the emergent path
    is exactly the contour path — no hidden behaviour."""
    for ph in list(load_cmu().values())[:3000]:
        assert geometry_boundaries_emergent(ph, {}, (0.2, 0.2)) == geometry_boundaries(ph)
