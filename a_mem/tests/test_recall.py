"""Probe 8 / S2: end-to-end autonomous recall — noisy signature ->
classify -> deploy half-anchors -> rebuild. Baseline margin +0.645
(known-identity ceiling +0.730); assert >= +0.55.

Also covers the same loop through the public Memory API.
"""
import numpy as np

from amem import Memory, cosine
from amem import constants as K
from conftest import (THREE_PATTERNS, confusion_margin, half_cells, imprint,
                      rebuild)


def test_autonomous_recall_margin(three_lib):
    names = list(three_lib)
    rng = np.random.default_rng(7)
    builds = {}
    for name in names:
        noisy_sig, _ = imprint(three_lib[name]["cells"], seed=77)
        pick = max(names, key=lambda n: cosine(noisy_sig, three_lib[n]["sig"]))
        assert pick == name  # selector must not miss at k = 3
        cue = half_cells(three_lib[pick]["anchors"], rng)
        builds[name] = rebuild(cue).w.copy()
    origs = {n: three_lib[n]["orig"] for n in names}
    m, _ = confusion_margin(builds, origs, names)
    assert m >= 0.55, f"autonomous recall margin {m:+.3f} < +0.55"


def test_recall_via_api_signature_route():
    mem = Memory(seed=11, path=None)
    mids = {name: mem.write(cells) for name, cells in THREE_PATTERNS.items()}
    for name, cells in THREE_PATTERNS.items():
        noisy_sig, _ = imprint(cells, seed=77)
        rec = mem.recall(signature=noisy_sig)
        assert rec.identity == mids[name]
        assert rec.dwell == K.REBUILD_BEATS
        # confidence is a noisy internal signal (r ~ +0.40 vs purity), so
        # assert only its validity range; completion is the quality gate
        # (probe 5 baseline ~0.5-0.74 at half-anchor cues)
        assert 0.0 < rec.confidence <= 1.0
        imp = mem.library.get(mids[name]).imprint
        completion = float(rec.reconstruction[imp].mean())
        assert completion >= 0.4, f"{name} completion {completion:.2f} < 0.4"
        # the reconstruction must resemble its own imprint more than others
        own = cosine(rec.reconstruction.astype(float),
                     mem.library.get(mids[name]).imprint.astype(float))
        for other, omid in mids.items():
            if other != name:
                cross = cosine(rec.reconstruction.astype(float),
                               mem.library.get(omid).imprint.astype(float))
                assert own > cross


def test_recall_via_api_cue_route():
    mem = Memory(seed=13, path=None)
    mids = {name: mem.write(cells) for name, cells in THREE_PATTERNS.items()}
    rng = np.random.default_rng(19)
    for name in THREE_PATTERNS:
        anchors = mem.library.get(mids[name]).anchors
        cue = half_cells(anchors, rng)
        rec = mem.recall(cue=cue)
        assert rec.identity == mids[name]
        assert 0.0 < rec.confidence <= 1.0
        imp = mem.library.get(mids[name]).imprint
        completion = float(rec.reconstruction[imp].mean())
        assert completion >= 0.4, f"{name} completion {completion:.2f} < 0.4"


def test_recall_argument_validation():
    mem = Memory(seed=1, path=None)
    try:
        mem.recall()
        raise AssertionError("expected ValueError for no arguments")
    except ValueError:
        pass
    mid = mem.write(THREE_PATTERNS["NW"])
    try:
        mem.recall(cue=[(1, 1)], signature=np.zeros(9))
        raise AssertionError("expected ValueError for both arguments")
    except ValueError:
        pass


def test_decode_boundary_exists_and_is_pure_selection():
    """W-4 / R-1: signature recall goes through the decode boundary; the
    only shipped selector is pure identity selection (nearest cosine) and
    selection itself never touches the stage."""
    from amem.decode import CosineSelector, Selector

    mem = Memory(seed=21, path=None)
    assert isinstance(mem.selector, CosineSelector)
    assert isinstance(mem.selector, Selector)   # satisfies the protocol

    mids = {n: mem.write(c) for n, c in THREE_PATTERNS.items()}
    a_before = mem.stage.a.copy()
    w_before = mem.stage.w.copy()
    entry = mem.library.get(mids["SE"])
    pick, score, scores = mem.selector.select(entry.sig_rad, mem.library)
    assert pick == mids["SE"] and score > 0
    # pure read: no field state was harmed in the making of this selection
    assert np.array_equal(mem.stage.a, a_before)
    assert np.array_equal(mem.stage.w, w_before)

    # the recall path honors a swapped-in selector (the boundary is real)
    class Rigged:
        def select(self, signature, library):
            mid = mids["NW"]
            return mid, 1.0, {mid: 1.0}

    mem.selector = Rigged()
    rec = mem.recall(signature=entry.sig_rad)   # SE's code, rigged to NW
    assert rec.identity == mids["NW"]
