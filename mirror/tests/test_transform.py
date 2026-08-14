"""W-2 acceptance (probe 19): the SEAM rule.

Held-out cosine >= 0.98 in shape space; SEAM strictly beats SUM on cosine
in BOTH spaces (measured +0.14 phon, +0.12 shape); sibling-library
retrieval through grid-47 a_mem at the >= 38/39 rate with SEAM >= SUM.
"""
import numpy as np
from amem import constants as AK
from amem.api import Memory
from amem.encoder import Encoder
from amem.hooks import EpisodeHooks

from mirror import Transform


def test_mined_inventory(transform):
    assert len(transform.pairs) >= 18000        # ~20k from the CMU data
    assert len(transform.test) == 40
    assert set(transform.suffixes) == {"ing", "s", "ed", "er", "ly", "ness"}


def test_seam_beats_sum_on_cosine(embedder, transform):
    for space, floor_margin in (("phon", 0.10), ("shape", 0.08)):
        seam, sum_ = [], []
        for b, s, w, _ in transform.test:
            actual = embedder.vec(embedder.corpus[w], space)
            seam.append(float(transform.bind(embedder.corpus[b], s, space) @ actual))
            sum_.append(float(transform.bind_sum(embedder.corpus[b], s, space) @ actual))
        m_seam, m_sum = float(np.mean(seam)), float(np.mean(sum_))
        print(f"\n{space}: SEAM {m_seam:.3f}  SUM {m_sum:.3f}  margin {m_seam - m_sum:+.3f}")
        assert m_seam > m_sum, f"{space}: SEAM did not beat SUM"
        assert m_seam - m_sum >= floor_margin, \
            f"{space}: SEAM margin {m_seam - m_sum:+.3f} below floor"
        if space == "shape":
            assert m_seam >= 0.98, f"held-out SEAM cosine {m_seam:.3f} < 0.98"


def test_sibling_library_retrieval(embedder, transform, tmp_path):
    enc = Encoder(grid=47, zone_min=2, zone_max=37,
                  min_sep=AK.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=str(tmp_path / "store"))
    hook = EpisodeHooks(mem, encoder=enc)
    mids = {w: hook.write_episode(embedder.shape_vec(embedder.corpus[w]))
            for (_, _, w, _) in transform.test}

    results = {}
    for rule, fn in (("SEAM", transform.bind), ("SUM", transform.bind_sum)):
        ok = sum(int(hook.recall_context(
            fn(embedder.corpus[b], s, "shape")).identity == mids[w])
            for b, s, w, _ in transform.test)
        results[rule] = ok
    n = len(transform.test)
    print(f"\nretrieval: SEAM {results['SEAM']}/{n}  SUM {results['SUM']}/{n}")
    # the 38/39 measured rate, as a rate (test membership is corpus-sized)
    assert results["SEAM"] / n >= 38 / 39
    assert results["SEAM"] >= results["SUM"]


def test_suffix_inventory_persists(embedder, transform, tmp_path):
    path = str(tmp_path / "suffixes.json")
    transform.save(path)
    fresh = Transform(embedder).load(path)
    assert fresh.modal_phon == transform.modal_phon
    b, s, _, _ = transform.test[0]
    assert np.allclose(fresh.bind(embedder.corpus[b], s),
                       transform.bind(embedder.corpus[b], s))
