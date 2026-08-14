"""W-5: the form|meaning rung (probe 21) — cross-modal episodes.

An episode is the concatenation of two unit-normalized blocks,
[shape | meaning], re-normalized as a whole and written through a_mem's
EpisodeHooks onto a grid-47 lattice. A cross-modal cue is the same
episode with one block zeroed: meaning-only cue retrieves the form
episode and vice versa (probe 21: 100% both directions, chance 4%).
"""
import numpy as np
from amem import constants as AK
from amem.api import Memory
from amem.encoder import Encoder
from amem.hooks import EpisodeHooks

RUNG_GRID = 47
RUNG_ZONE = (2, 37)


class Rung:
    def __init__(self, embedder, geometry):
        self.embedder = embedder
        self.geometry = geometry
        self.ds = embedder.dim
        self.dm = geometry.dim

    def episode(self, word, form=True, meaning=True):
        """[shape | meaning] episode vector; zero a block to cue cross-
        modally."""
        fs = (self.embedder.shape_vec(self.embedder.corpus[word])
              if form else np.zeros(self.ds))
        ms = self.geometry.vec(word) if meaning else np.zeros(self.dm)
        v = np.concatenate([fs, ms])
        m = np.linalg.norm(v)
        return v / m if m > 0 else v

    def write_bank(self, words, grid=RUNG_GRID, seed=5, path=None,
                   encoder_seed=0):
        """Write one episode per word; returns (memory, hooks, mids)."""
        enc = Encoder(grid=grid, zone_min=RUNG_ZONE[0], zone_max=RUNG_ZONE[1],
                      min_sep=AK.PLACE_MIN_SEP, seed=encoder_seed)
        mem = Memory(grid=grid, seed=seed, path=path)
        hooks = EpisodeHooks(mem, encoder=enc)
        mids = {w: hooks.write_episode(self.episode(w), payload_meta={"word": w})
                for w in words}
        return mem, hooks, mids
