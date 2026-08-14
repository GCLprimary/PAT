"""Probe 49: THE CIRCULATION + THE MEANING-DRIFT CENSUS.
A CIRCULATION — chapter episodes written to REAL a_mem (anchor shape
  vector as the pattern, ledger digest as meta); retrieval cued by
  MEMBER vectors (never the anchor itself); capacity curve at
  N = 50/150/300; refusal on below-threshold recalls; confabs counted
  (wrong-chapter recalls above threshold).
B MEANING DRIFT — form-chapters checked against the dense meaning
  space: member's dense vec vs own anchor vs best other anchor;
  margin < 0 => the member's meaning has left the family -> the
  DRIFT CENSUS, a new receipt chapters should carry.
"""
import warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
from amem.api import Memory

fam = defaultdict(dict)
for base, sfx, w, rem in pairs:
    fam[base][sfx] = w
fams = [(b, d) for b, d in fam.items() if len(d) >= 3]

D = len(vec(corpus["the"], "shape"))
print(f"shape dim {D}; families available {len(fams)}")

def cells_of(v, grid, k=24):
    idx = np.argsort(v)[::-1][:k]
    return [(int(d) // grid, int(d) % grid) for d in idx]

print("\\nA · CIRCULATION (real a_mem, member-cued chapter recall)")
for N in (50, 150, 300):
    sel = fams[:N]
    mem = Memory(seed=3, path=f"/tmp/amem_cx_{N}")
    g = int(mem.grid)
    anchor_of = {}
    for b, d in sel:
        m_ = mem.write(cells_of(vec(corpus[b], "shape"), g), meta={"anchor": b})
        anchor_of[m_] = b
    ok = confab = refuse = tot = 0
    for b, d in sel:
        for w in list(d.values())[:2]:
            r = mem.recall(cue=cells_of(vec(corpus[w], "shape"), g))
            tot += 1
            got = anchor_of.get(getattr(r, "identity", None)) if r else None
            if got is None: refuse += 1
            elif got == b: ok += 1
            elif tuple(corpus[got]) == tuple(corpus[b]): ok += 1
            else: confab += 1
    print(f"  N={N:3d}: member-cued recall {ok}/{tot} = {ok/tot*100:.1f}%   "
          f"refusals {refuse}   WRONG-CHAPTER {confab}")

print("\\nB · MEANING DRIFT (form-chapters vs the dense space)")
toks_all = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt")]
cnt = Counter()
for s in toks_all: cnt.update(s)
vocab = [w for w, _ in cnt.most_common(10000)]
need = {w for b, d in fams[:300] for w in [b] + list(d.values())}
vocab += [w for w in need if w in cnt and w not in set(vocab)]
ix = {w: i for i, w in enumerate(vocab)}
V = len(vocab)
from scipy import sparse
rows, cols = [], []
W = 4
for s in toks_all:
    idxs = [ix.get(w, -1) for w in s]
    for i, a in enumerate(idxs):
        if a < 0: continue
        for j in range(max(0, i - W), min(len(idxs), i + W + 1)):
            if j != i and idxs[j] >= 0:
                rows.append(a); cols.append(idxs[j])
C = sparse.coo_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                      shape=(V, V)).tocsr()
rs = np.asarray(C.sum(1)).ravel(); cs = np.asarray(C.sum(0)).ravel(); total = C.sum()
C = C.tocoo()
pmi = np.log((C.data * total) / (rs[C.row] * cs[C.col])); pmi[pmi < 0] = 0
P = sparse.coo_matrix((pmi, (C.row, C.col)), shape=(V, V)).tocsr()
from scipy.sparse.linalg import svds
U, S, _ = svds(P, k=300)
X = U * S
freq = np.array([cnt[w] for w in vocab], float)
X = X - (X * (freq[:, None] / freq.sum())).sum(0, keepdims=True)
X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

MIN = 20
use = [(b, d) for b, d in fams[:300] if b in ix and cnt[b] >= MIN and sum(w in ix and cnt[w] >= MIN for w in d.values()) >= 2]
A = np.stack([X[ix[b]] for b, _ in use])
own = []; drift = []
for fi, (b, d) in enumerate(use):
    for w in d.values():
        if w not in ix or cnt[w] < MIN: continue
        s = A @ X[ix[w]]
        o = s[fi]; s2 = s.copy(); s2[fi] = -2
        margin = float(o - s2.max())
        own.append(margin)
        if margin < 0:
            drift.append((w, b, use[int(np.argmax(s2))][0], margin))
own = np.array(own)
print(f"  members checked: {len(own)} across {len(use)} chapters")
print(f"  meaning coheres with own chapter (margin > 0): {np.mean(own > 0)*100:.1f}%")
print(f"  margin mean {own.mean():+.3f}   p10 {np.quantile(own, 0.10):+.3f}")
print(f"  DRIFT CENSUS: {len(drift)} members whose meaning left the family")
for w, b, other, m in sorted(drift, key=lambda x: x[3])[:6]:
    print(f"    {w!r}: born of {b!r}, now nearer {other!r}  (margin {m:+.3f})")
