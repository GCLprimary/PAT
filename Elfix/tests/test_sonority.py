"""Tests for earned (phonotactic) sonority (elfix/sonority.py).
Law 1: the spacing traces to a corpus count. Law 3: the ranking is a re-derivable
view of the corpus, asserted here — never hand-tuned."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from elfix.data_io import load_cmu
from elfix.sonority import (derive_sonority, sonority_phonotactic,
                              PHONOTACTIC_SONORITY)
from elfix.substrate.features import sonority
from elfix.emergent.emergent_unit import geometry_boundaries


def _order(d):
    return [m for m in sorted(d, key=d.get) if m != "vowel"]


def test_frozen_table_has_the_documented_shape():
    """The constant the model uses is well-formed: obstruents below sonorants,
    sonorants ranked nasal < lateral < approximant, vowels on top."""
    s = PHONOTACTIC_SONORITY
    assert max(s["stop"], s["fricative"], s["affricate"]) < s["nasal"]
    assert s["nasal"] < s["lateral"] < s["approximant"] < s["vowel"]


def test_phonotactic_sonority_is_re_derivable_from_corpus():
    """Law 3: re-derive from the corpus and assert the earned structure. The
    robust, large-effect invariants hold on any reasonable corpus; the exact
    frozen ranking + values are checked against the full corpus when present."""
    corpus = list(load_cmu().values())
    d = derive_sonority(corpus)
    assert d["nasal"] < d["lateral"] <= d["approximant"]
    assert max(d["stop"], d["fricative"], d["affricate"]) < d["nasal"]
    if len(corpus) > 50_000:                      # the full CMU corpus is present
        assert _order(d) == _order(PHONOTACTIC_SONORITY)
        assert all(abs(d[m] - PHONOTACTIC_SONORITY[m]) < 0.05 for m in d)


def test_dual_scale_keeps_phonetic_and_phonotactic_apart():
    """The two sonority measures are genuinely different facts and must NOT be
    collapsed: /s/ is sonorant-ish phonetically (continuant) but an outermost
    appendix phonotactically. The morpheme cue needs the former, syllables the
    latter."""
    assert sonority("s") > sonority("t")                       # phonetic: s above
    assert sonority_phonotactic("s") < sonority_phonotactic("t")   # earned: s below


def test_morpheme_path_unaffected_by_dual_scale():
    """geometry_boundaries (the morpheme path) still uses phonetic sonority, so
    the coda-reversal plural cue survives: cats -> boundary before the -s."""
    assert geometry_boundaries(["k", "AE", "t", "s"]) == [3]
