"""W-1: the embedder — voicing-neutral shape-bigram geometry (probe 18 E2).

A phoneme's shape is its (manner, place) articulation with voicing erased;
every vowel collapses into the single ("V",) bucket. A word's vector is
the unit-normalized concatenation of shape-bigram counts and shape-unigram
counts. This is the geometry that beat the bag baseline while holding
relative-form recall at 10x chance (probe 18: self@0.90 92%, relative 78%).

Law-scope note: the spec words the vowel gate as "sonority >= 6", but the
ElfIX phonetic sonority scale tops out at 5.0 (vowels) — that literal test
never fires; in the probes every vowel fell into one bucket anyway via the
stringified (None, None) of its consonant features. mirror makes the
intended rule explicit (kind == "vowel"); the geometry is identical up to
a relabeling of one basis element, so every probe number carries over
exactly. Flagged in HANDOFF.md, not silently reconciled.
"""
import numpy as np

from .config import cmu_path, ensure_elfix_importable

ensure_elfix_importable()
from elfix.substrate.features import features, sonority  # noqa: E402

VOWEL_SONORITY_GATE = 6.0   # the spec's literal (dead) threshold — see docstring


def load_cmu(path=None):
    """word -> phoneme tuple, in the ElfIX preprocessed CMU contract."""
    path = cmu_path() if path is None else path
    corpus = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                corpus[parts[0]] = tuple(parts[1:])
    return corpus


def shape(ph):
    """Voicing-neutral articulatory shape of one phoneme.

    Vowels -> ("V",); unknown -> ("?",); consonants -> (manner, place).
    """
    f = features(ph)
    if f is None:
        return ("?",)
    if f.kind == "vowel" or (sonority(ph) or 0) >= VOWEL_SONORITY_GATE:
        return ("V",)
    return (str(f.manner), str(f.place))


class BigramSpace:
    """Generic bigram+unigram count geometry over a fixed token alphabet."""

    def __init__(self, alphabet):
        self.alphabet = sorted(alphabet)
        self.index = {t: i for i, t in enumerate(self.alphabet)}
        self.n = len(self.alphabet)
        self.dim = self.n * self.n + self.n

    def vec(self, tokens):
        v = np.zeros(self.dim)
        idx = self.index
        toks = list(tokens)
        for t in toks:
            v[self.n * self.n + idx[t]] += 1
        for a, b in zip(toks, toks[1:]):
            v[idx[a] * self.n + idx[b]] += 1
        m = np.linalg.norm(v)
        return v / m if m > 0 else v


class Embedder:
    """The two sibling geometries over one phone inventory.

    shape_vec is the W-1 deliverable (mirror's working space); phon_vec is
    the phoneme-identity sibling kept for the W-2 SEAM >= SUM comparison.
    """

    def __init__(self, corpus=None):
        self.corpus = load_cmu() if corpus is None else corpus
        phones = sorted({p for pr in self.corpus.values() for p in pr})
        self.phones = phones
        self.phon_space = BigramSpace(phones)
        self.shape_space = BigramSpace({shape(p) for p in phones})

    @property
    def dim(self):
        return self.shape_space.dim

    def shape_vec(self, phonemes):
        """Unit shape-bigram vector for a phoneme sequence (W-1)."""
        return self.shape_space.vec([shape(p) for p in phonemes])

    def phon_vec(self, phonemes):
        return self.phon_space.vec(list(phonemes))

    def vec(self, phonemes, space="shape"):
        if space == "shape":
            return self.shape_vec(phonemes)
        if space == "phon":
            return self.phon_vec(phonemes)
        raise ValueError(f"unknown space: {space!r}")
