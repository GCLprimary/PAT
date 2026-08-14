"""X-6: the literature row (probe 47) — WS-353 and SimLex-999,
measured honestly at 5.2M words.

Dense meaning space: window-4 PPMI over the pinned corpus_big, top
12,000 vocabulary plus every in-corpus benchmark word, truncated SVD
(k = 300), the frequency-weighted center removed (the house centering
law), unit rows, Spearman rho with tie-averaged ranks, reported AT
COVERAGE (pairs whose both words the corpus knows).

These are SENTINELS, not gates: count-SVD models at small corpora land
roughly 0.4-0.6 on WS353 and 0.2-0.35 on SimLex in the literature;
large word2vec ~0.65-0.7 / ~0.4. Our row is the honest small-corpus
point, and the 10M-coherent-corpus frontier inherits these bands as
its targets. Drift means the MEANING ORGAN changed character — the
sentinel message says so by name.
"""
import csv
from collections import Counter
from pathlib import Path

import numpy as np

from .config import DATA_DIR

VOCAB_N = 12_000
WINDOW = 4
K = 300
SVD_SEED = 7


def load_pairs(path):
    """(word1, word2, score) rows from a vecto-style CSV
    (index,word1,word2,similarity with a header line)."""
    out = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)                       # header
        for row in reader:
            if len(row) < 4:
                continue
            try:
                score = float(row[3])
            except ValueError:
                continue                    # malformed row: skip it
            out.append((row[1].lower(), row[2].lower(), score))
    return out


def spearman(xs, ys):
    def rank(v):
        v = np.asarray(v)
        order = np.argsort(v)
        r = np.empty(len(v))
        r[order] = np.arange(len(v))
        out = r.astype(float)
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1:
                out[m] = out[m].mean()
        return out
    rx, ry = rank(xs), rank(ys)
    rx -= rx.mean()
    ry -= ry.mean()
    return float((rx @ ry) / (np.linalg.norm(rx) * np.linalg.norm(ry)))


def _load_corpus(corpus_path):
    corpus_path = (DATA_DIR / "corpus_big.txt" if corpus_path is None
                   else Path(corpus_path))
    sents = []
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            sents.append(line.split())
    return sents


def _dense_space(sents, vocab_n, extra_words):
    """The house recipe: window-4 positive PMI, truncated SVD k=300
    (seeded start vector), frequency-weighted centering, unit rows."""
    from scipy import sparse
    from scipy.sparse.linalg import svds

    cnt = Counter()
    for s in sents:
        cnt.update(s)
    vocab = [w for w, _ in cnt.most_common(vocab_n)]
    vs = set(vocab)
    vocab += [w for w in sorted(extra_words)
              if w in cnt and w not in vs]
    ix = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)

    rows, cols = [], []
    for s in sents:
        idxs = [ix.get(w, -1) for w in s]
        for i, a in enumerate(idxs):
            if a < 0:
                continue
            for j in range(max(0, i - WINDOW),
                           min(len(idxs), i + WINDOW + 1)):
                if j == i:
                    continue
                b = idxs[j]
                if b >= 0:
                    rows.append(a)
                    cols.append(b)
    C = sparse.coo_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(V, V)).tocsr()
    rs = np.asarray(C.sum(1)).ravel()
    cs = np.asarray(C.sum(0)).ravel()
    total = C.sum()
    C = C.tocoo()
    pmi = np.log((C.data * total) / (rs[C.row] * cs[C.col]))
    pmi[pmi < 0] = 0.0
    P = sparse.coo_matrix((pmi, (C.row, C.col)), shape=(V, V)).tocsr()

    rng = np.random.default_rng(SVD_SEED)
    v0 = rng.standard_normal(min(P.shape))
    U, S, _ = svds(P, k=K, v0=v0)
    X = U * S
    freq = np.array([cnt[w] for w in vocab], dtype=np.float64)
    center = (X * (freq[:, None] / freq.sum())).sum(0, keepdims=True)
    X = X - center
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    return X, ix, cnt


def _score(benches, X, ix, key=None):
    key = key or (lambda w: w)
    out = {}
    for name, ps in benches.items():
        gold, pred = [], []
        for a, b, g in ps:
            aa, bb = key(a), key(b)
            if aa in ix and bb in ix:
                gold.append(g)
                pred.append(float(X[ix[aa]] @ X[ix[bb]]))
        out[name] = (len(ps), len(gold), spearman(pred, gold))
    return out


def meaning_rows(bench_files, corpus_path=None):
    """bench_files: {name: csv path} -> {name: (n_pairs, covered, rho)}.
    The probe-47 recipe, verbatim (unfolded — the reference column)."""
    sents = _load_corpus(corpus_path)
    benches = {name: load_pairs(path)
               for name, path in bench_files.items()}
    bench_words = {w for ps in benches.values() for a, b, _ in ps
                   for w in (a, b)}
    X, ix, _ = _dense_space(sents, VOCAB_N, bench_words)
    return _score(benches, X, ix)


# ── M-3 (probe 49b): the count fold — law 4 of the metabolism ────────
FOLD_VOCAB_N = 10_000            # probe-49b literal (unfolded uses 12k)


def corpus_fold(transform, corpus):
    """The creature's lemmatizer as a fold callable (probe 49b): mined
    bases anchor themselves; any other in-lexicon token folds to an
    anchor when its pron is an anchor's pron (homophone collapse, the
    probe's last-wins dict) or peels to one under an attested
    remainder. Everything else stays itself."""
    bases = set()
    anchors_pron = {}
    all_rems = set()
    for base, sfx, w, rem in transform.pairs:
        bases.add(base)
        all_rems.add(tuple(rem))
    for b in bases:
        anchors_pron[tuple(corpus[b])] = b      # probe-49b: last wins
    maxr = max(len(r) for r in all_rems)

    def fold(w):
        if w in bases or w not in corpus:
            return w
        p = tuple(corpus[w])
        hit = anchors_pron.get(p)
        if hit is not None:
            return hit
        for k in range(1, maxr + 1):
            if len(p) - k >= 2 and p[-k:] in all_rems:
                a = anchors_pron.get(p[:-k])
                if a is not None:
                    return a
        return w

    return fold


def folded_meaning_rows(fold, bench_files, corpus_path=None):
    """LAW 4: FOLD THE COUNTS, NOT THE VECTORS. `fold` maps a surface
    token to its anchor (the creature's own addressing — the dict-exact
    engine's lemmatizer). The dense space is rebuilt over folded
    counts; benchmark queries go through the same fold. Returns
    ({name: (n, covered, rho)}, n_types_folded)."""
    sents = _load_corpus(corpus_path)
    amap = {}

    def m(w):
        if w not in amap:
            amap[w] = fold(w)
        return amap[w]

    folded = [[m(w) for w in s] for s in sents]
    benches = {name: load_pairs(path)
               for name, path in bench_files.items()}
    bench_anchors = {m(w) for ps in benches.values() for a, b, _ in ps
                     for w in (a, b)}
    X, ix, _ = _dense_space(folded, FOLD_VOCAB_N, bench_anchors)
    n_folded = sum(1 for w, a in amap.items() if w != a)
    return _score(benches, X, ix, key=m), n_folded


def drift_census(families, corpus_path=None, vocab_n=FOLD_VOCAB_N,
                 min_count=20):
    """M-1's receipt, computed here (probe 49): members whose dense
    vector sits nearer another family's anchor than its own
    (margin < 0). families: [(anchor, {sfx: word})]. Returns
    (n_checked, coherence_pct, drift) where drift entries are
    {word, anchor, nearer, margin} — receipts only, no action."""
    sents = _load_corpus(corpus_path)
    cnt = Counter()
    for s in sents:
        cnt.update(s)
    need = {w for b, d in families for w in [b] + list(d.values())}
    X, ix, cnt = _dense_space(sents, vocab_n, need)
    use = [(b, d) for b, d in families
           if b in ix and cnt[b] >= min_count
           and sum(w in ix and cnt[w] >= min_count
                   for w in d.values()) >= 2]
    A = np.stack([X[ix[b]] for b, _ in use])
    margins = []
    drift = []
    for fi, (b, d) in enumerate(use):
        for w in d.values():
            if w not in ix or cnt[w] < min_count:
                continue
            s = A @ X[ix[w]]
            own = s[fi]
            s2 = s.copy()
            s2[fi] = -2
            margin = float(own - s2.max())
            margins.append(margin)
            if margin < 0:
                drift.append({"word": w, "anchor": b,
                              "nearer": use[int(np.argmax(s2))][0],
                              "margin": round(margin, 4)})
    margins = np.array(margins)
    coherence = float(np.mean(margins > 0) * 100)
    return len(margins), coherence, drift
