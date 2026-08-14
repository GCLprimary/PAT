"""Tests for the earned Maximal-Onset syllable gold (elfix/syllable.py).
Law 3 (one source of truth): the legal-onset set is a re-derivable VIEW of the
dictionary, asserted here, never hand-listed."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from elfix.syllable import legal_onsets, mop_boundaries, build_syllable_gold
from elfix.substrate.features import features

# small constructed corpus (full-corpus onset diversity not needed for invariants)
CORP = [["s", "t", "r", "IY", "t"], ["k", "AE", "t"],
        ["EH", "k", "s", "t", "r", "AH"], ["t", "IY"],
        ["b", "AH", "t", "ER"], ["d", "AO", "g"]]


def _initial_cluster(word):
    cl = []
    for s in word:
        f = features(s)
        if f is None or f.kind == "vowel":
            break
        cl.append(s)
    return tuple(cl)


def test_onsets_are_a_view_of_attested_initials():
    """Re-derive the onset set independently and assert equality (Law 3)."""
    ons = legal_onsets(CORP)
    inits = {_initial_cluster(w) for w in CORP if _initial_cluster(w)}
    assert (ons - {()}) == inits          # every legal onset is some word's onset
    assert () in ons                      # the empty (vowel-initial) onset is legal


def test_mop_places_one_boundary_per_vowel_gap():
    """Structural invariant of Maximal Onset: a multisyllabic word gets exactly
    (#nuclei - 1) interior boundaries, all interior and sorted-unique."""
    cmu = {f"w{i}": w for i, w in enumerate(CORP)}
    gold = build_syllable_gold(cmu)
    assert gold, "expected some multisyllabic gold from the corpus"
    for _, ph, bs in gold:
        nvowel = sum(1 for s in ph if (f := features(s)) and f.kind == "vowel")
        assert len(bs) == nvowel - 1
        assert bs == sorted(set(bs))
        assert all(0 < b < len(ph) for b in bs)


def test_maximal_onset_prefers_longest_legal_onset():
    """extra -> ek.stra: the medial 'k s t r' gives 'str' to the next onset."""
    ons = legal_onsets(CORP)
    assert mop_boundaries(["EH", "k", "s", "t", "r", "AH"], ons) == [2]


def test_syllable_boundary_uses_maximal_onset_not_coda():
    """The geometry's two conventions differ by exactly +1 on the intervocalic
    consonant: robot -> ru.bot (syllable, trough->onset) vs ro b|ot style coda."""
    from elfix.emergent.emergent_unit import (syllable_boundaries,
                                                 geometry_boundaries)
    w = ["r", "OW", "b", "AA", "t"]            # 'robot'
    assert syllable_boundaries(w) == [2]        # r OW | b AA t  (b -> onset)
    assert geometry_boundaries(w) == [3]        # r OW b | AA t  (b -> coda, min+1)
