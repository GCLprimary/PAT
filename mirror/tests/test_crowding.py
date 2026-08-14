"""S-3 acceptance: rung crowding at the grid-47 placement ceiling.

Probe 22B: crowding is a non-issue below the ceiling. This test fills
the placement zone to PlacementFull with dense-block episodes, asserts
the measured shape-dependent capacity band (39-44 at grid 47), and
requires cross-modal recall >= 90% both directions at whatever N
placement allows.
"""
from amem import constants as AK
from amem.api import Memory
from amem.encoder import Encoder, PlacementFull
from amem.hooks import EpisodeHooks

from mirror import Rung


def test_fill_to_placement_full(embedder, geometry, tmp_path):
    words = [w for w in geometry.vocab[300:2000]
             if w in embedder.corpus and w.isalpha() and len(w) > 3]
    rung = Rung(embedder, geometry)

    enc = Encoder(grid=47, zone_min=2, zone_max=37,
                  min_sep=AK.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=str(tmp_path / "store"))
    hooks = EpisodeHooks(mem, encoder=enc)

    mids = {}
    for w in words:
        try:
            mids[w] = hooks.write_episode(rung.episode(w),
                                          payload_meta={"word": w})
        except PlacementFull:
            break
    n = len(mids)
    print(f"\nplacement ceiling reached at N = {n} episodes")
    assert 39 <= n <= 44, \
        f"capacity {n} outside the measured shape-dependent band 39-44"

    for label, kw in (("meaning-only -> form", dict(form=False)),
                      ("form-only -> meaning", dict(meaning=False))):
        ok = sum(int(hooks.recall_context(rung.episode(w, **kw)).identity
                     == mids[w]) for w in mids)
        rate = ok / n
        print(f"{label}: {ok}/{n} = {rate:.0%}  (chance {1 / n:.0%})")
        assert rate >= 0.90, f"{label} at the ceiling: {rate:.0%} < 90%"
