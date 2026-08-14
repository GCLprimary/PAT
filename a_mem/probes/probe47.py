"""Probe 47: THE LITERATURE ROW — WS-353 (sim/rel) + SimLex-999.
Dense meaning space: window-4 PPMI + SVD-300 over the pinned
corpus_big (5.2M words), frequency-weighted center removed (the house
centering law). Spearman rho at coverage, per benchmark. Anchors from
the literature for context: count-SVD models at small corpora land
roughly rho 0.4-0.6 on WS353 and 0.2-0.35 on SimLex; large word2vec
~0.65-0.7 / ~0.4. Our row is the honest small-corpus point.
"""
import csv, warnings
import numpy as np
warnings.filterwarnings("ignore")

toks_all = []
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"):
    toks_all.append(l.split())
from collections import Counter, defaultdict
cnt = Counter()
for s in toks_all: cnt.update(s)

def load_pairs(path, delim=","):
    out = []
    with open(path, encoding="utf-8") as f:
        r = csv.reader(f)
        head = [h.lower() for h in next(r)]
        # find the two word columns and the first numeric score column
        for row in r:
            if len(row) < 3: continue
            try: sc = float(row[2])
            except ValueError:
                try: sc = float(row[3])
                except (ValueError, IndexError): continue
            a, b = row[0], row[1]
            if not a[0].isalpha(): a, b = row[1], row[2]
            out.append((a.lower(), b.lower(), sc))
    return out

B = "/home/claude/wbench/word-similarity/monolingual/en/"
benches = {
    "WS353-sim": load_pairs(B + "wordsim353-sim.csv"),
    "WS353-rel": load_pairs(B + "wordsim353-rel.csv"),
    "SimLex-999": load_pairs(B + "simlex999.csv"),
}
bench_words = set()
for ps in benches.values():
    for a, b, _ in ps: bench_words.add(a); bench_words.add(b)

VOCAB_N = 12000
vocab = [w for w, _ in cnt.most_common(VOCAB_N)]
vs = set(vocab)
extra = [w for w in bench_words if w in cnt and w not in vs]
vocab += extra; vs |= set(extra)
ix = {w: i for i, w in enumerate(vocab)}
V = len(vocab)
print(f"vocab {V} (top {VOCAB_N} + {len(extra)} benchmark words in corpus)")

W = 4
from scipy import sparse
rows, cols = [], []
for s in toks_all:
    idxs = [ix.get(w, -1) for w in s]
    for i, a in enumerate(idxs):
        if a < 0: continue
        for j in range(max(0, i - W), min(len(idxs), i + W + 1)):
            if j == i: continue
            b = idxs[j]
            if b >= 0: rows.append(a); cols.append(b)
C = sparse.coo_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                      shape=(V, V)).tocsr()
rs = np.asarray(C.sum(1)).ravel(); cs = np.asarray(C.sum(0)).ravel()
total = C.sum()
C = C.tocoo()
pmi = np.log((C.data * total) / (rs[C.row] * cs[C.col]))
pmi[pmi < 0] = 0.0
P = sparse.coo_matrix((pmi, (C.row, C.col)), shape=(V, V)).tocsr()
from scipy.sparse.linalg import svds
U, S, Vt = svds(P, k=300)
X = U * S
X = X - X.mean(0, keepdims=True) * 0          # placeholder; weighted next
freq = np.array([cnt[w] for w in vocab], dtype=np.float64)
center = (X * (freq[:, None] / freq.sum())).sum(0, keepdims=True)
X = X - center
X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

def spearman(xs, ys):
    def rank(v):
        order = np.argsort(v); r = np.empty(len(v)); r[order] = np.arange(len(v))
        # average ties
        v = np.asarray(v); out = r.astype(float)
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1: out[m] = out[m].mean()
        return out
    rx, ry = rank(np.asarray(xs)), rank(np.asarray(ys))
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx @ ry) / (np.linalg.norm(rx) * np.linalg.norm(ry)))

print("\nbenchmark     pairs  covered   Spearman rho")
for name, ps in benches.items():
    gold, pred = [], []
    for a, b, g in ps:
        if a in ix and b in ix:
            gold.append(g); pred.append(float(X[ix[a]] @ X[ix[b]]))
    rho = spearman(pred, gold)
    print(f"  {name:11s} {len(ps):5d}   {len(gold):4d}     {rho:+.3f}")
