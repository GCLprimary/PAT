"""Tests for self-forming appendix units (elfix/emergent/appendix.py) —
the ADDITIVE Tier-3 cue. Key properties: voicing-neutral allomorph merging (the
geometric novelty), a superset of the contour, promotion by SHAPE recurrence not
dictionary lookup (non-leaky), and a real recall lift over the contour."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.data_io import load_cmu, build_morpheme_gold
from elfix.emergent.emergent_unit import geometry_boundaries
from elfix.emergent.appendix import (phon_shape, discover_appendices,
                                       appendix_boundary,
                                       geometry_boundaries_additive)


def test_phon_shape_merges_allomorphs_by_voicing():
    """The geometric move BPE cannot make: -s/-z and -t/-d share one shape."""
    assert phon_shape("s") == phon_shape("z")        # coronal fricative
    assert phon_shape("t") == phon_shape("d")        # coronal stop
    assert phon_shape("s") != phon_shape("t")
    assert phon_shape("IY") == ("V",)


def test_additive_is_a_superset_of_contour():
    """Additive can only ADD boundaries the contour missed, never remove one."""
    corpus = list(load_cmu().values())
    inv = discover_appendices(corpus)
    for ph in corpus[:5000]:
        assert set(geometry_boundaries(ph)) <= set(geometry_boundaries_additive(ph, inv))


def test_promotion_is_shape_recurrence_not_dictionary():
    """Non-leaky: a final shape recurring across many DISTINCT nonsense stems is
    promoted with NO stem-dictionary lookup (the morpheme gold's own criterion).
    20 invented words, none real, all ending in a coronal stop."""
    stems = [[c, v] for v in ("IY", "AA") for c in
             ("p", "b", "k", "g", "f", "v", "m", "n", "l", "r")]
    corpus = [s + ["t"] for s in stems]               # 20 distinct nonsense stems
    inv = discover_appendices(corpus)
    assert inv, "a recurring final shape should promote with no dictionary"
    assert appendix_boundary(["p", "IY", "t"], inv) is not None


def test_additive_lifts_recall_over_contour():
    """The headline: appendix units raise morpheme recall well past the contour's
    ~52% ceiling (we expect ~0.48 -> ~0.97)."""
    cmu = load_cmu()
    corpus, gold = list(cmu.values()), build_morpheme_gold(cmu)
    inv = discover_appendices(corpus)

    def recall(predict):
        tp = fn = 0
        for _, ph, b in gold:
            p = set(predict(ph))
            tp += b in p
            fn += b not in p
        return tp / (tp + fn)

    assert recall(lambda ph: geometry_boundaries_additive(ph, inv)) > \
        recall(geometry_boundaries) + 0.1
