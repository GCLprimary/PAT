"""Tests for Tier 6 shape routing (elfix/routing/shape_routing.py).
The earned-not-magic property (classes recur >= min_count, no top-k), readable
classes (Law 6), and novelty agreement with Tier 7 (non-recurring arc -> -1)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.data_io import load_cmu
from elfix.trajectory.trajectory import Trajectory
from elfix.routing.shape_routing import ShapeRouter

CORPUS = list(load_cmu().values())[:8000]
TRAJS = [Trajectory.of(w) for w in CORPUS]


def test_routing_classes_are_earned_by_recurrence():
    """Law 1: every class recurs >= min_count — no magic top-k cutoff."""
    r = ShapeRouter(TRAJS, min_count=3)
    assert len(r.classes) > 0
    assert all(r.counts[d] >= 3 for d in r.classes)


def test_route_ids_are_valid_and_novel_is_minus_one():
    r = ShapeRouter(TRAJS, min_count=3)
    ids = r.route(Trajectory.of(["k", "AE", "t", "s"]))
    assert all(i == -1 or 0 <= i < len(r.classes) for i in ids)
    # a router that has seen almost nothing: every shape is NOVEL (-1), like
    # Tier 7's "no basis, stay open".
    tiny = ShapeRouter([Trajectory.of(["AA", "b"])], min_count=3)
    assert tiny.classes == []
    assert all(i == -1 for i in tiny.route(Trajectory.of(["k", "AE", "t", "s"])))


def test_class_descriptions_are_readable():
    r = ShapeRouter(TRAJS)
    assert isinstance(r.class_shape(0), str) and "recurs" in r.class_shape(0)
    assert isinstance(r.class_position(0), str)
    assert r.class_shape(-1) == "novel" and r.class_position(10 ** 9) == "novel"


def test_learn_ops_discovers_accumulate_vs_boundary():
    """Tier-6 op semantics earned from behaviour: a class that always predicts its
    continuation ACCUMULATES; one followed by a spread is a BOUNDARY. The split is
    discovered (2-means), not declared."""
    r = ShapeRouter(TRAJS, min_count=3)
    A, C = 0, 1
    streams = [[A, 7]] * 200                       # A -> 7 always (entropy 0)
    for x in range(10, 30):
        streams += [[C, x]] * 12                    # C -> 20 different (high entropy)
    r.learn_ops(streams, min_obs=20)
    assert r.class_op(A) == "accumulate"
    assert r.class_op(C) == "boundary"
    assert r.predictiveness[A] > r.predictiveness[C]
    assert r.class_op(99999) == "unknown"           # unseen / pre-learn -> unknown
