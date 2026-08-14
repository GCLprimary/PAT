"""W-4 + S-1/S-2: the count geometry — counts -> PPMI -> SVD densifier.

Probe-22 recipe (frozen for acceptance): window-4 co-occurrence over the
original sentence positions, with the top-120 frequency words excluded AS
CONTEXTS at count time (content-only contexts) and asymmetric marginals
(row x context-column) for the expected count. PPMI keeps zeros zero —
absence is not negative evidence (the ternary-zero law).

S-1, the probe-22 headline: compression before corpus. Truncated economy
SVD (top-k = 300) on the PPMI matrix, rows re-normalized, becomes the
default meaning space — it tripled suffix-offset agreement on the SAME
1M corpus while a 5x corpus moved it barely at all. dense=False keeps
the sparse PPMI space available; the ternary-zero law lives at the
sparse stage (the dense space is derived linear algebra).

S-2: corpus sources are a registry — each source built and normalized
separately under the ElfIX data contract; combining is EXPLICIT
(coherence before volume; no silent stacking).

Law-scope note: floats are legitimate here — traceability, not
integer-ness, is the invariant outside the lattice. Counting is exact
integer arithmetic; log2 and SVD are readouts of counts.
"""
import re
from collections import Counter
from pathlib import Path

import numpy as np

from .config import DATA_DIR, corpus_build_target, corpus_path

_KEEP = re.compile(r"[^a-z']")

SOURCES = ("brown", "gutenberg", "reuters")


def _norm_token(tok):
    return _KEEP.sub("", tok.lower()).strip("'")


def _nltk_sents(source, categories=None):
    import nltk
    corpus_id = {"brown": "brown", "gutenberg": "gutenberg",
                 "reuters": "reuters"}[source]
    try:
        nltk.data.find(f"corpora/{corpus_id}")
    except LookupError:
        nltk.download(corpus_id, quiet=True)
    if source in ("gutenberg", "reuters"):
        # plaintext corpus readers tokenize sentences with punkt
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt_tab", quiet=True)
    module = getattr(__import__("nltk.corpus", fromlist=[corpus_id]),
                     corpus_id)
    if source == "brown" and categories:
        return module.sents(categories=categories)
    return module.sents()


def _write_contract(sents, out, min_len):
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for sent in sents:
            pieces = []
            for t in sent:
                pieces.extend(re.split(r"[-/]", t))
            toks = [_norm_token(t) for t in pieces]
            toks = [t for t in toks if t]
            if len(toks) < min_len:
                continue
            f.write(" ".join(toks) + "\n")
            n += 1
    return n


def build_corpus(source="brown", out_path=None, categories=None, min_len=3):
    """Build ONE source's running text under the ElfIX data contract
    (make_corpus.py conventions). Returns (path, sentence_count)."""
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}; registry: {SOURCES}")
    if out_path is None:
        out_path = (corpus_build_target() if source == "brown"
                    else DATA_DIR / f"corpus_{source}.txt")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = _write_contract(_nltk_sents(source, categories), out_path, min_len)
    return out_path, n


def combine_sources(sources, out_path=None):
    """EXPLICIT combination — the registry never stacks silently.
    Each source is built (or reused) separately, then concatenated."""
    paths = []
    for s in sources:
        p = ensure_source(s)
        paths.append(p)
    if out_path is None:
        out_path = DATA_DIR / ("corpus_" + "+".join(sources) + ".txt")
    out_path = Path(out_path)
    with open(out_path, "w", encoding="utf-8") as out:
        for p in paths:
            with open(p, encoding="utf-8") as f:
                out.write(f.read())
    return out_path


def ensure_source(source):
    if source == "brown":
        return ensure_corpus()
    p = DATA_DIR / f"corpus_{source}.txt"
    if not p.exists():
        p, _ = build_corpus(source)
    return p


def ensure_corpus():
    """Resolve the default (Brown) corpus, building it if absent."""
    path = corpus_path()
    if path is not None:
        return path
    path, _ = build_corpus("brown")
    return path


class MeaningGeometry:
    """PPMI count geometry with the SVD-300 dense space as default."""

    def __init__(self, corpus_file=None, vocab_n=4000, window=4,
                 content_cut=120, dense=True, k=300, cache=True):
        self.window = window
        self.content_cut = content_cut
        self.dense = dense
        self.k = k
        path = ensure_corpus() if corpus_file is None else Path(corpus_file)
        self._corpus_file = Path(path)
        with open(path, encoding="utf-8") as f:
            sents = [line.split() for line in f]

        uni = Counter()
        for s in sents:
            uni.update(s)
        self.vocab = [w for w, _ in uni.most_common(vocab_n)]
        self.vi = {w: i for i, w in enumerate(self.vocab)}
        n = len(self.vocab)

        # probe-22 counting: exact integers, window over ORIGINAL
        # positions, stop words never counted AS CONTEXTS (column side)
        counts = np.zeros((n, n), dtype=np.int32)
        a_all, b_all = [], []
        for s in sents:
            kept = [(i, self.vi[w]) for i, w in enumerate(s) if w in self.vi]
            if len(kept) < 2:
                continue
            pos = np.fromiter((p for p, _ in kept), dtype=np.int64)
            ids = np.fromiter((w for _, w in kept), dtype=np.int64)
            for kk in range(1, len(kept)):
                gap = pos[kk:] - pos[:-kk]
                mask = gap <= window
                if not mask.any():
                    break
                a_all.append(ids[:-kk][mask])
                b_all.append(ids[kk:][mask])
        a = np.concatenate(a_all)
        b = np.concatenate(b_all)
        cut = self.content_cut
        keep_b = b >= cut          # context must be a content word
        np.add.at(counts, (a[keep_b], b[keep_b]), 1)
        keep_a = a >= cut
        np.add.at(counts, (b[keep_a], a[keep_a]), 1)

        self.counts = counts
        self.rowsum = counts.sum(axis=1, dtype=np.float64)
        self.ctxsum = counts.sum(axis=0, dtype=np.float64)
        self.total = float(counts.sum(dtype=np.float64))
        self._sparse_cache = {}
        self.dense_vecs = None
        if dense:
            self._build_dense(cache)

    # ── sparse stage (the counts; ternary zero lives here) ───────────
    def sparse_vec(self, word):
        if word not in self.vi:
            raise KeyError(f"{word!r} not in the meaning vocabulary")
        if word in self._sparse_cache:
            return self._sparse_cache[word]
        i = self.vi[word]
        c = self.counts[i].astype(np.float64)
        expected = self.rowsum[i] * self.ctxsum / self.total
        v = np.zeros(len(self.vocab))
        live = (c > 0) & (expected > 0) & (c > expected)
        v[live] = np.log2(c[live] / expected[live])
        m = np.linalg.norm(v)
        if m > 0:
            v /= m
        self._sparse_cache[word] = v
        return v

    # ── dense stage (S-1: compression before corpus) ─────────────────
    def _cache_file(self):
        stem = self._corpus_file.stem
        size = self._corpus_file.stat().st_size
        return DATA_DIR / f"svd_{stem}_{size}_n{len(self.vocab)}_k{self.k}.npz"

    def _build_dense(self, cache=True):
        cache_file = self._cache_file()
        if cache and cache_file.exists():
            blob = np.load(cache_file, allow_pickle=False)
            if list(blob["vocab"]) == self.vocab:
                self.dense_vecs = blob["vecs"]
                return
        p = np.zeros((len(self.vocab), len(self.vocab)), dtype=np.float32)
        for w in self.vocab:
            p[self.vi[w]] = self.sparse_vec(w)
        u, s, _ = np.linalg.svd(p, full_matrices=False)
        w = u[:, :self.k] * s[:self.k]
        norms = np.linalg.norm(w, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.dense_vecs = (w / norms).astype(np.float32)
        self._sparse_cache.clear()      # free the row cache used to build p
        if cache:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache_file, vecs=self.dense_vecs,
                                vocab=np.array(self.vocab))

    # ── the public space ─────────────────────────────────────────────
    def __contains__(self, word):
        return word in self.vi

    @property
    def dim(self):
        return self.k if (self.dense and self.dense_vecs is not None) \
            else len(self.vocab)

    def vec(self, word):
        if self.dense and self.dense_vecs is not None:
            if word not in self.vi:
                raise KeyError(f"{word!r} not in the meaning vocabulary")
            return self.dense_vecs[self.vi[word]].astype(np.float64)
        return self.sparse_vec(word)

    def neighbors(self, word, k=4, among=2000):
        v = self.vec(word)
        sims = []
        for other in self.vocab[:among]:
            if other != word:
                sims.append((float(v @ self.vec(other)), other))
        sims.sort(reverse=True)
        return sims[:k]


# ── the probe-22 instruments (used by tests and the coherence report) ─
PROBE22_TRIPLES = [
    ("water", "surface"), ("war", "civil"), ("music", "songs"),
    ("money", "tax"), ("school", "students"), ("night", "morning"),
    ("doctor", "hospital"), ("church", "god"), ("river", "water"),
    ("fire", "heat"), ("court", "judge"), ("food", "eat"),
    ("book", "read"), ("game", "play"), ("heart", "blood"),
    ("road", "car"), ("winter", "snow"), ("voice", "heard"),
    ("door", "open"), ("child", "mother"),
]


def relatedness(geometry, rng, triples=None):
    """Probe-22 relatedness: (hits, total) over the triple instrument."""
    triples = PROBE22_TRIPLES if triples is None else triples
    hits = tot = 0
    for w, rel in triples:
        if w in geometry and rel in geometry:
            rnd = geometry.vocab[rng.integers(500, len(geometry.vocab))]
            if rnd in (w, rel):
                continue
            vw = geometry.vec(w)
            hits += int(float(vw @ geometry.vec(rel)) >
                        float(vw @ geometry.vec(rnd)))
            tot += 1
    return hits, tot


def suffix_offsets(geometry, rng, suffixes=("ed", "ing", "s"), n_offsets=12):
    """Probe-22 offsets: {sfx: (agreement, random_floor)}."""
    out = {}
    for sfx in suffixes:
        offs = []
        for b in geometry.vocab:
            d = b + sfx
            if d in geometry and b in geometry and len(b) > 3:
                o = geometry.vec(d) - geometry.vec(b)
                m = np.linalg.norm(o)
                if m > 0:
                    offs.append(o / m)
            if len(offs) >= n_offsets:
                break
        if len(offs) < 6:
            continue
        sims = [float(offs[i] @ offs[j])
                for i in range(len(offs)) for j in range(i + 1, len(offs))]
        rand = []
        for _ in range(20):
            x, y = rng.choice(len(geometry.vocab), 2, replace=False)
            r = geometry.vec(geometry.vocab[x]) - geometry.vec(geometry.vocab[y])
            m = np.linalg.norm(r)
            if m > 0:
                rand.append(r / m)
        rsims = [float(rand[i] @ rand[j])
                 for i in range(len(rand)) for j in range(i + 1, len(rand))]
        out[sfx] = (float(np.mean(sims)), float(np.mean(rsims)))
    return out


def coherence_report(sources=SOURCES, vocab_n=4000, k=300, seed=7):
    """S-2: combined vs best-single, per the probe-22 instrument.

    Combined is adopted only where its relatedness is >= best-single
    minus 1 triple; otherwise per-source models stand."""
    results = {}
    for s in sources:
        geo = MeaningGeometry(corpus_file=ensure_source(s),
                              vocab_n=vocab_n, k=k)
        hits, tot = relatedness(geo, np.random.default_rng(seed))
        results[s] = {"relatedness": (hits, tot),
                      "offsets": suffix_offsets(geo, np.random.default_rng(seed))}
    combined_path = combine_sources(list(sources))
    combo = MeaningGeometry(corpus_file=combined_path, vocab_n=vocab_n, k=k)
    hits, tot = relatedness(combo, np.random.default_rng(seed))
    results["combined"] = {"relatedness": (hits, tot),
                           "offsets": suffix_offsets(combo, np.random.default_rng(seed))}
    best_single = max((results[s]["relatedness"][0] for s in sources))
    results["adopt_combined"] = hits >= best_single - 1
    results["best_single"] = best_single
    return results
