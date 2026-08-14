"""The creature's organs — composed, not owned.

Everything here is an import of a probe-validated organ from a_mem or
mirror; the shell adds no new physics. The heavy organs (the journey's
stack proposer) load lazily on first use.
"""
from collections import Counter
from functools import cached_property

import numpy as np

from mirror import (CenteredSpace, Embedder, Journey, MeaningGeometry,
                    Proposer, Transform, mine_pairs)
from mirror.config import DATA_DIR
from mirror.generate import MIN_SENT


class Organs:
    """One shared organ bundle; construct once per process."""

    def __init__(self):
        self.embedder = Embedder()
        self.transform = Transform(self.embedder).fit(
            mine_pairs(self.embedder.corpus))
        self.geometry = MeaningGeometry()
        cnt = Counter()
        with open(DATA_DIR / "corpus.txt", encoding="utf-8") as f:
            for line in f:
                cnt.update(line.split())
        self.corpus_counts = cnt
        self.stop = set(w for w, _ in cnt.most_common(120))
        self.space = CenteredSpace(self.geometry, stop=self.stop,
                                   weights=cnt)

    def shape_vec(self, word):
        return self.embedder.shape_vec(self.embedder.corpus[word])

    def bound_vec(self, base, suffix):
        """SEAM proposal for base + suffix (None if unlearnable)."""
        if suffix not in self.transform.modal_phon:
            return None
        return self.transform.bind(self.embedder.corpus[base], suffix)

    @cached_property
    def _journey_parts(self):
        """The volume side, loaded lazily (the dual-corpus law)."""
        with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
            sents = [line.split() for line in f
                     if len(line.split()) >= MIN_SENT]
        proposer = Proposer(sents)
        return proposer, Journey(proposer, self.geometry, self.space), sents

    @property
    def proposer(self):
        return self._journey_parts[0]

    @property
    def journey(self):
        return self._journey_parts[1]

    def attested_prompt_for(self, word):
        """The first attested 3-token opening of a corpus sentence that
        contains `word` — the road a walk can start from. None if no
        sentence offers one."""
        _, journey, sents = self._journey_parts
        for s in sents:
            if word in s and len(s) >= 3:
                p = tuple(s[:3])
                if journey.prompt_attested(p):
                    return p
        return None


_ORGANS = None


def get_organs():
    global _ORGANS
    if _ORGANS is None:
        _ORGANS = Organs()
    return _ORGANS
