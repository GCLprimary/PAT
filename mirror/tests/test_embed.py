"""W-1 acceptance (probe 18): the shape-bigram embedder through grid-47
a_mem. Self-recall under fixed-angle noise, relative-form recall at 10x
chance, near-form discrimination. Crowding reported, not asserted."""
import numpy as np
from amem import constants as AK
from amem.api import Memory
from amem.encoder import Encoder
from amem.hooks import EpisodeHooks

from conftest import angle_noise

WORDS = ["lock", "play", "help", "read", "load", "fold", "trust", "open",
         "will", "lead", "build", "heat", "law", "work", "agree", "think",
         "group", "bend", "fill", "end", "cat", "dog", "house", "water",
         "light"]
RELATIVES = {"lock": "unlocking", "play": "replaying", "read": "misreading",
             "load": "reloading", "help": "unhelpful", "think": "unthinking",
             "build": "rebuilding", "work": "reworking", "open": "reopening",
             "lead": "misleading"}
DISCRIM = [("lock", "law"), ("play", "lead"), ("cat", "bend")]


def test_embedder_through_amem(embedder, tmp_path):
    words = [w for w in WORDS if w in embedder.corpus]
    relatives = {b: r for b, r in RELATIVES.items()
                 if b in embedder.corpus and r in embedder.corpus}
    # one relative form is absent from the CMU file; the probe's own
    # filter dropped it too (its measured 78% was 7/9)
    assert len(words) == 25 and len(relatives) >= 9

    vecs = {w: embedder.shape_vec(embedder.corpus[w]) for w in words}
    m = np.array([vecs[w] for w in words])
    gram = m @ m.T
    np.fill_diagonal(gram, -1)
    crowd = float(gram.max(axis=1).mean())
    print(f"\ncrowding (mean nn-cosine): {crowd:.3f}  [reported, not asserted]")

    enc = Encoder(grid=47, zone_min=2, zone_max=37,
                  min_sep=AK.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=str(tmp_path / "store"))
    hook = EpisodeHooks(mem, encoder=enc)
    mids = {w: hook.write_episode(vecs[w]) for w in words}

    # probe-18 rng discipline: the 0.95 draws precede the 0.90 draws
    rng = np.random.default_rng(9)
    acc = {}
    for c in (0.95, 0.90):
        ok = tot = 0
        for w in words:
            for _ in range(2):
                rec = hook.recall_context(angle_noise(vecs[w], c, rng))
                ok += int(rec.identity == mids[w])
                tot += 1
        acc[c] = ok / tot
    print(f"noisy self-recall @0.95: {acc[0.95]:.0%}  @0.90: {acc[0.90]:.0%}")
    assert acc[0.90] >= 0.85, f"self@0.90 {acc[0.90]:.0%} < 85%"

    ok = 0
    for b, r in relatives.items():
        rec = hook.recall_context(embedder.shape_vec(embedder.corpus[r]))
        ok += int(rec.identity == mids[b])
    rel = ok / len(relatives)
    print(f"relative-form recall: {rel:.0%}  (chance {1 / len(words):.0%})")
    assert rel >= 0.60, f"relative-form recall {rel:.0%} < 60%"

    for a, b in DISCRIM:
        rec = hook.recall_context(vecs[a])
        assert rec.identity == mids[a], \
            f"near-form confusion: {a} retrieved {rec.identity}, not its own"
