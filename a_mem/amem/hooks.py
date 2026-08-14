"""The integration hook pair (D-5): write_episode / recall_context.

Runtime-agnostic: any agent that can hand over an embedding per episode
can use a_mem. The hybrid recall route (D-1) is
    embedding -> nearest neighbor in embedding space -> episode id
    -> anchor recall on the stage (the probe-8 route).
Placement happens at write time only (probe-15 law); the separation
policy (D-3) auto-relocates encoder placements below the 0.45 overlap
danger line and stores pinned placements with a recorded warning.
"""
import numpy as np

from . import constants as K
from .encoder import Encoder, NumpyEmbeddingIndex, PlacementFull


class EpisodeHooks:
    """Binds a Memory to an embedding index and a placement encoder."""

    def __init__(self, memory, encoder=None, index=None):
        self.memory = memory
        self.encoder = encoder if encoder is not None else Encoder()
        self.index = index if index is not None else NumpyEmbeddingIndex()
        # rebuild the index from persisted episode metadata
        for mid in memory.library.mids():
            emb = memory.library.get(mid).meta.get("embedding")
            if emb is not None:
                self.index.add(mid, np.asarray(emb, dtype=float))

    # ── write path ───────────────────────────────────────────────────
    def _placements(self):
        out = []
        for mid in self.memory.library.mids():
            p = self.memory.library.get(mid).meta.get("placement")
            if p is not None:
                out.append((int(p[0]), int(p[1])))
        return out

    def _write_at(self, embedding, shape, cx, cy, payload_meta, pinned):
        cells = [(cx + dx, cy + dy) for dx, dy in shape]
        meta = {"embedding": [float(v) for v in np.asarray(embedding).ravel()],
                "placement": [cx, cy],
                "pinned": pinned}
        if payload_meta:
            meta.update(payload_meta)
        return self.memory.write(cells, meta=meta)

    def write_episode(self, embedding, payload_meta=None, placement=None):
        """Store one episode. Returns its memory id.

        placement=None: the encoder chooses a position maximizing
        separation; if the resulting write-time overlap is still >= the
        danger line, it relocates through further candidates (D-3), and
        raises PlacementFull when the zone cannot take another episode.
        placement=(cx, cy): caller-pinned — stored as-is; an overlap at
        or past the danger line is recorded as a warning, not refused.
        """
        if placement is not None:
            cx, cy = int(placement[0]), int(placement[1])
            shape = self.encoder.shape_for(embedding)
            mid = self._write_at(embedding, shape, cx, cy, payload_meta,
                                 pinned=True)
            entry = self.memory.library.get(mid)
            if entry.meta["overlap_report"]["flagged"]:
                entry.meta["separation_warning"] = True
                if self.memory.autosave:
                    self.memory.library.save()
            self.index.add(mid, embedding)
            return mid

        shape = self.encoder.shape_for(embedding)
        candidates = self.encoder.place(self._placements(), shape=shape)
        best = None                      # (overlap, cx, cy) least-bad so far
        for cx, cy in candidates[:K.PLACE_RELOCATE_TRIES]:
            mid = self._write_at(embedding, shape, cx, cy, payload_meta,
                                 pinned=False)
            report = self.memory.library.get(mid).meta["overlap_report"]
            if not report["flagged"]:
                self.index.add(mid, embedding)
                return mid
            # a flagged write must be withdrawn BEFORE the next candidate,
            # or its imprint would contaminate the next overlap report
            if best is None or report["max_overlap"] < best[0]:
                best = (report["max_overlap"], cx, cy)
            self.memory.forget(mid)
        # no candidate cleared the danger line: keep the least-overlapping
        # placement and record the warning (documented Phase 3 behavior)
        _, cx, cy = best
        mid = self._write_at(embedding, shape, cx, cy, payload_meta,
                             pinned=False)
        entry = self.memory.library.get(mid)
        entry.meta["separation_warning"] = True
        if self.memory.autosave:
            self.memory.library.save()
        self.index.add(mid, embedding)
        return mid

    # ── recall path (never derives placement — probe-15 law) ─────────
    def recall_context(self, embedding):
        """Recover the episode nearest to this embedding: NN match ->
        episode id -> anchor recall on the stage."""
        mid, match = self.index.nearest(embedding)
        rec = self.memory.recall(mid=mid)
        rec.scores = dict(rec.scores)
        rec.scores["embedding_match"] = match
        return rec
