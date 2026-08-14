"""W-2 acceptance: the hybrid encoder + id-keyed recall (D-1, D-3, D-5).

The probe-15 law: recall NEVER re-derives placement. Matching happens in
embedding space; placement is write-time-only separation optimization.
"""
import numpy as np

from amem import Encoder, EpisodeHooks, Memory, PlacementFull
from amem import constants as K

EMB_D = 32


def build_hooks(seed=9, n_episodes=8):
    mem = Memory(seed=seed, path=None)
    hooks = EpisodeHooks(mem)
    rng = np.random.default_rng(3)
    embs = [rng.normal(size=EMB_D) for _ in range(n_episodes)]
    embs = [e / np.linalg.norm(e) for e in embs]
    mids = [hooks.write_episode(e, payload_meta={"episode": i})
            for i, e in enumerate(embs)]
    return mem, hooks, embs, mids


def test_end_to_end_noisy_recall():
    """8 episodes; noisy re-encounters at sigma in {0.05, 0.10, 0.20}.
    Embedding-space matching makes sigma <= 0.10 near-trivial — that is
    the point (probe 15: placement re-derivation managed only 42%)."""
    mem, hooks, embs, mids = build_hooks()
    for sigma, floor in ((0.05, 0.95), (0.10, 0.95), (0.20, 0.80)):
        ok = tot = 0
        for i, emb in enumerate(embs):
            for s in (77, 101):
                noisy = emb + np.random.default_rng(s + i).normal(size=EMB_D) * sigma
                rec = hooks.recall_context(noisy)
                ok += int(rec.identity == mids[i])
                tot += 1
        acc = ok / tot
        assert acc >= floor, f"sigma={sigma}: accuracy {acc:.2f} < {floor}"


def test_recall_never_derives_placement():
    """The spy: placement derivations happen at write time only."""
    mem, hooks, embs, mids = build_hooks()
    calls_after_writes = hooks.encoder.place_calls
    assert calls_after_writes == len(mids)   # one derivation per write
    for emb in embs:
        noisy = emb + np.random.default_rng(1).normal(size=EMB_D) * 0.1
        hooks.recall_context(noisy)
    assert hooks.encoder.place_calls == calls_after_writes, \
        "the recall path derived a placement (probe-15 law violated)"


def test_write_time_separation_report():
    """All pairwise imprint overlaps below the danger line, or the entry
    carries a recorded warning (D-3)."""
    mem, hooks, embs, mids = build_hooks()
    ids, overlap = mem.library.pairwise_overlap()
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if overlap[i, j] >= K.OVERLAP_DANGER:
                warned = (mem.library.get(ids[i]).meta.get("separation_warning")
                          or mem.library.get(ids[j]).meta.get("separation_warning"))
                assert warned, (f"{ids[i]}~{ids[j]} overlap "
                                f"{overlap[i, j]:.2f} with no recorded warning")


def test_pinned_placement_stores_with_warning():
    """D-3: when the caller pins a colliding placement, a_mem stores it
    and records the warning — duty of care, not refusal."""
    mem = Memory(seed=13, path=None)
    hooks = EpisodeHooks(mem)
    rng = np.random.default_rng(5)
    e1, e2 = rng.normal(size=EMB_D), rng.normal(size=EMB_D)
    m1 = hooks.write_episode(e1, placement=(5, 5))
    m2 = hooks.write_episode(e2, placement=(7, 7))    # deliberate collision
    entry2 = mem.library.get(m2)
    assert entry2.meta["pinned"]
    if entry2.meta["overlap_report"]["flagged"]:
        assert entry2.meta.get("separation_warning"), \
            "flagged pinned write must carry a recorded warning"
    assert m1 in mem.library and m2 in mem.library    # both stored


def test_placement_full_at_packing_limit():
    """The zone packs ~9 at Chebyshev-5 (probe 15); the 10th raises."""
    enc = Encoder()
    placed = []
    for i in range(9):
        cands = enc.place(placed, shape=K.SEED_CONSTELLATION)
        placed.append(cands[0])
    seps = [max(abs(a[0] - b[0]), abs(a[1] - b[1]))
            for i, a in enumerate(placed) for b in placed[i + 1:]]
    assert min(seps) >= K.PLACE_MIN_SEP
    try:
        enc.place(placed, shape=K.SEED_CONSTELLATION)
        raise AssertionError("expected PlacementFull at the packing limit")
    except PlacementFull:
        pass


def test_index_rebuilds_from_persisted_store(tmp_path):
    """The hook pair survives a process restart: embeddings persist in
    entry metadata and the index rebuilds from the library."""
    store = str(tmp_path / "store")
    mem = Memory(seed=9, path=store)
    hooks = EpisodeHooks(mem)
    rng = np.random.default_rng(3)
    embs = [rng.normal(size=EMB_D) for _ in range(3)]
    mids = [hooks.write_episode(e) for e in embs]

    mem2 = Memory(seed=99, path=store)
    hooks2 = EpisodeHooks(mem2)
    assert len(hooks2.index) == 3
    for emb, mid in zip(embs, mids):
        rec = hooks2.recall_context(emb + 0.05 * rng.normal(size=EMB_D))
        assert rec.identity == mid
