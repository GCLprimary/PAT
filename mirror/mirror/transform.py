"""W-2: the transform — seam-aware binding (probe 19).

bind(base, suffix) predicts the derived form's vector by embedding the
CONCATENATED phoneme sequence base + modal-suffix-form — the SEAM rule:
the junction bigram (base coda x suffix onset) rides along. The SUM
baseline (superpose part vectors, no seam) measurably loses to it
(probe 19: SEAM 0.997 held-out cosine, +0.12 shape / +0.14 phon over SUM;
retrieval 39/39 vs 38/39).

Suffix canonical forms are LEARNED: the modal phoneme remainder over a
train split of mined (base, suffix, derived) pairs. The inventory
persists to JSON.
"""
import json
from collections import Counter, defaultdict

import numpy as np

SUFFIXES = ["ing", "s", "ed", "er", "ly", "ness"]
PREFIXES = ["un", "re", "dis", "mis", "pre", "over", "out"]


def mine_prefix_pairs(corpus, prefixes=None):
    """G-3 (probe 25): clean (base, prefix, derived, phoneme-remainder)
    pairs — derived is prefix + base orthographically AND the derived
    pronunciation ENDS with the base's pronunciation."""
    prefixes = PREFIXES if prefixes is None else prefixes
    pairs = []
    for w in corpus:
        for pre in prefixes:
            if w.startswith(pre) and len(w) > len(pre) + 2:
                base = w[len(pre):]
                if base in corpus:
                    b, d = corpus[base], corpus[w]
                    if len(d) > len(b) and d[-len(b):] == b:
                        pairs.append((base, pre, w, d[:len(d) - len(b)]))
    return pairs


def mine_pairs(corpus, suffixes=None):
    """Clean (base, suffix, derived, phoneme-remainder) pairs: derived is
    base + suffix orthographically AND the pronunciation extends the
    base's pronunciation as a prefix."""
    suffixes = SUFFIXES if suffixes is None else suffixes
    pairs = []
    for w in corpus:
        for sfx in suffixes:
            if w.endswith(sfx) and len(w) > len(sfx) + 2:
                base = w[:-len(sfx)]
                if base in corpus:
                    b, d = corpus[base], corpus[w]
                    if len(d) > len(b) and d[:len(b)] == b:
                        pairs.append((base, sfx, w, d[len(b):]))
    return pairs


class Transform:
    """Learned suffix inventory + the bind operation."""

    def __init__(self, embedder):
        self.embedder = embedder
        self.modal_phon = {}        # suffix -> modal phoneme remainder
        self.allomorphs = {}        # suffix -> distinct remainder count
        self.train = []
        self.test = []
        self.modal_prefix = {}      # prefix -> modal phoneme form
        self.prefix_allomorphs = {}
        self.prefix_pairs = []
        self.prefix_train = []
        self.prefix_test = []

    # ── learning ─────────────────────────────────────────────────────
    def fit(self, pairs, seed=7, train_frac=0.6, test_cap=40):
        """Probe-19 protocol: shuffle, per-suffix split, modal remainder
        from train, held-out test capped."""
        pairs = list(pairs)
        rng = np.random.default_rng(seed)
        rng.shuffle(pairs)
        # the shuffled order is part of the protocol: probe 20 samples its
        # known/withheld base sets from THIS ordering, not the mined one
        self.pairs = pairs
        by_sfx = defaultdict(list)
        for pr in pairs:
            by_sfx[pr[1]].append(pr)
        train, test = [], []
        for sfx, lst in by_sfx.items():
            k = int(len(lst) * train_frac)
            train += lst[:k]
            test += lst[k:]
        rng.shuffle(test)
        self.train, self.test = train, test[:test_cap]
        rem = {s: Counter(tuple(r[3]) for r in train if r[1] == s)
               for s in set(p[1] for p in train)}
        self.modal_phon = {s: list(c.most_common(1)[0][0])
                           for s, c in rem.items() if c}
        self.allomorphs = {s: len(c) for s, c in rem.items() if c}
        return self

    def fit_prefixes(self, pairs, seed=7, train_frac=0.6):
        """G-3: the same protocol, prefix side (probe 25)."""
        pairs = list(pairs)
        rng = np.random.default_rng(seed)
        rng.shuffle(pairs)
        self.prefix_pairs = pairs
        by_pre = defaultdict(list)
        for pr in pairs:
            by_pre[pr[1]].append(pr)
        train, test = [], []
        for pre, lst in by_pre.items():
            k = int(len(lst) * train_frac)
            train += lst[:k]
            test += lst[k:]
        self.prefix_train, self.prefix_test = train, test
        rem = {p: Counter(tuple(r[3]) for r in train if r[1] == p)
               for p in set(pr[1] for pr in train)}
        self.modal_prefix = {p: list(c.most_common(1)[0][0])
                             for p, c in rem.items() if c}
        self.prefix_allomorphs = {p: len(c) for p, c in rem.items() if c}
        return self

    @property
    def suffixes(self):
        return sorted(self.modal_phon)

    @property
    def prefixes(self):
        return sorted(self.modal_prefix)

    # ── the transform ────────────────────────────────────────────────
    def bind(self, base_pron, suffix, space="shape"):
        """SEAM: embed the concatenated sequence — junction included."""
        if suffix not in self.modal_phon:
            raise KeyError(f"unknown suffix category: {suffix!r}")
        return self.embedder.vec(list(base_pron) + self.modal_phon[suffix],
                                 space)

    def bind_sum(self, base_pron, suffix, space="shape"):
        """The no-seam baseline: superpose part vectors (for tests)."""
        vb = self.embedder.vec(base_pron, space)
        vs = self.embedder.vec(self.modal_phon[suffix], space)
        v = vb + vs
        return v / np.linalg.norm(v)

    def bind_prefix(self, base_pron, prefix, space="shape"):
        """SEAM, prefix side: modal prefix form + base, junction included."""
        if prefix not in self.modal_prefix:
            raise KeyError(f"unknown prefix category: {prefix!r}")
        return self.embedder.vec(self.modal_prefix[prefix] + list(base_pron),
                                 space)

    def bind_prefix_sum(self, base_pron, prefix, space="shape"):
        vb = self.embedder.vec(base_pron, space)
        vp = self.embedder.vec(self.modal_prefix[prefix], space)
        v = vb + vp
        return v / np.linalg.norm(v)

    # ── persistence ──────────────────────────────────────────────────
    def save(self, path):
        payload = {"modal_phon": self.modal_phon,
                   "allomorphs": self.allomorphs,
                   "modal_prefix": self.modal_prefix,
                   "prefix_allomorphs": self.prefix_allomorphs}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        self.modal_phon = {s: list(v) for s, v in payload["modal_phon"].items()}
        self.allomorphs = dict(payload["allomorphs"])
        self.modal_prefix = {p: list(v)
                             for p, v in payload.get("modal_prefix", {}).items()}
        self.prefix_allomorphs = dict(payload.get("prefix_allomorphs", {}))
        return self
