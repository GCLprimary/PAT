"""Probe 49b: GATED CIRCULATION + THE COUNT FOLD.
A a_mem is a PROPOSER: rank r.scores, verify each candidate anchor with
  the sequence-exact stem gate; first gated pass wins, else refuse.
  Raw-similarity circulation measured 34.8% at N=300; the gate should
  restore ~48b levels.
B THE COUNT FOLD: the creature lemmatizes the corpus with its own
  addressing (member tokens counted as their anchors), the dense space
  is rebuilt over folded counts, and the sentinel rows are re-measured
  against 0.433 / 0.244 / 0.160.
"""
import csv, warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
from amem.api import Memory

fam = defaultdict(dict); attested = defaultdict(set)
for base, sfx, w, rem in pairs:
    fam[base][sfx] = w; attested[sfx].add(tuple(rem))
ALL_REMS = set()
for s_, rs in attested.items(): ALL_REMS |= rs
fams = [(b, d) for b, d in fam.items() if len(d) >= 3]

def cells_of(v, grid, k=24):
    idx = np.argsort(v)[::-1][:k]
    return [(int(d) // grid, int(d) % grid) for d in idx]

print("A \u00b7 GATED CIRCULATION (a_mem proposes, the exact gate verifies)")
N = 300
sel = fams[:N]
mem = Memory(seed=3, path="/tmp/amem_gc")
g = int(mem.grid)
anchor_of = {}
for b, d in sel:
    anchor_of[mem.write(cells_of(vec(corpus[b], "shape"), g), meta={"anchor": b})] = b
ok = confab = refuse = tot = 0
for b, d in sel:
    for w in list(d.values())[:2]:
        r = mem.recall(cue=cells_of(vec(corpus[w], "shape"), g))
        tot += 1
        got = None
        scores = getattr(r, "scores", None) if r else None
        if scores:
            wp = tuple(corpus[w])
            for mid in sorted(scores, key=scores.get, reverse=True)[:12]:
                a = anchor_of.get(mid)
                if a is None: continue
                ap = tuple(corpus[a])
                if wp == ap or (len(wp) > len(ap) and wp[:len(ap)] == ap
                                and wp[len(ap):] in ALL_REMS):
                    got = a; break
        if got is None: refuse += 1
        elif got == b or tuple(corpus[got]) == tuple(corpus[b]): ok += 1
        else: confab += 1
print(f"  N={N}: gated recall {ok}/{tot} = {ok/tot*100:.1f}%   "
      f"refusals {refuse}   WRONG-CHAPTER {confab}   (raw was 34.8%, wrong 391)")

print("\nB \u00b7 THE COUNT FOLD (creature-lemmatized dense space vs sentinels)")
anchors_pron = {tuple(corpus[b]): b for b in fam}
def to_anchor(w):
    if w in fam or w not in corpus: return w
    p = tuple(corpus[w])
    if p in anchors_pron: return anchors_pron[p]
    for k in (1, 2, 3):
        if len(p) - k >= 2 and p[-k:] in ALL_REMS:
            a = anchors_pron.get(p[:-k])
            if a: return a
    return w

toks_all = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt")]
amap = {}
def m(w):
    if w not in amap: amap[w] = to_anchor(w)
    return amap[w]
folded = [[m(w) for w in s] for s in toks_all]
cnt = Counter()
for s in folded: cnt.update(s)
print(f"  fold: {sum(1 for w,a in amap.items() if w != a)} surface types folded into anchors")

def load_pairs(path):
    out = []
    with open(path, encoding="utf-8") as f:
        r = csv.reader(f); next(r)
        for row in r:
            try: out.append((row[1].lower(), row[2].lower(), float(row[3])))
            except (ValueError, IndexError): pass
    return out
B = "/home/claude/wbench/word-similarity/monolingual/en/"
benches = {"WS353-sim": load_pairs(B + "wordsim353-sim.csv"),
           "WS353-rel": load_pairs(B + "wordsim353-rel.csv"),
           "SimLex-999": load_pairs(B + "simlex999.csv")}
bw = {m(w) for ps in benches.values() for a, b2, _ in ps for w in (a, b2)}
vocab = [w for w, _ in cnt.most_common(10000)]
vocab += [w for w in bw if w in cnt and w not in set(vocab)]
ix = {w: i for i, w in enumerate(vocab)}; V = len(vocab)
from scipy import sparse
rows, cols = [], []
for s in folded:
    idxs = [ix.get(w, -1) for w in s]
    for i, a in enumerate(idxs):
        if a < 0: continue
        for j in range(max(0, i - 4), min(len(idxs), i + 5)):
            if j != i and idxs[j] >= 0:
                rows.append(a); cols.append(idxs[j])
C = sparse.coo_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(V, V)).tocsr()
rs = np.asarray(C.sum(1)).ravel(); cs = np.asarray(C.sum(0)).ravel(); tt = C.sum()
C = C.tocoo()
pmi = np.log((C.data * tt) / (rs[C.row] * cs[C.col])); pmi[pmi < 0] = 0
P = sparse.coo_matrix((pmi, (C.row, C.col)), shape=(V, V)).tocsr()
from scipy.sparse.linalg import svds
U, S, _ = svds(P, k=300)
X = U * S
freq = np.array([cnt[w] for w in vocab], float)
X -= (X * (freq[:, None] / freq.sum())).sum(0, keepdims=True)
X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

def spearman(xs, ys):
    def rank(v):
        v = np.asarray(v); o = np.argsort(v); r = np.empty(len(v)); r[o] = np.arange(len(v))
        out = r.astype(float)
        for val in np.unique(v):
            k = v == val
            if k.sum() > 1: out[k] = out[k].mean()
        return out
    rx, ry = rank(xs), rank(ys); rx -= rx.mean(); ry -= ry.mean()
    return float((rx @ ry) / (np.linalg.norm(rx) * np.linalg.norm(ry)))

base_rows = {"WS353-sim": 0.433, "WS353-rel": 0.244, "SimLex-999": 0.160}
for name, ps in benches.items():
    gold, pred = [], []
    for a, b2, gsc in ps:
        aa, bb = m(a), m(b2)
        if aa in ix and bb in ix:
            gold.append(gsc); pred.append(float(X[ix[aa]] @ X[ix[bb]]))
    rho = spearman(pred, gold)
    d = rho - base_rows[name]
    print(f"  {name:11s} covered {len(gold):4d}   rho {rho:+.3f}   (unfolded {base_rows[name]:+.3f}, \u0394 {d:+.3f})")
