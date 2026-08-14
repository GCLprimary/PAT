"""Probe 29: THE WORKSHOP FOUNDATION. Words populate a medium; can the
field line out its own geodesics?
Task: held-out sentences, cue = (first, last) content word; recover the
TRUE middle content words.
Media:  M1 meaning-kNN graph (dense cos, top-8 edges)
        M2 attestation graph (sentence-window co-occurrence counts)
Mechanisms: DIFFUSE (activation spread from both endpoints, field-like)
            GEODESIC (nodes on the shortest path, -log edge weight)
Baselines: MIDPOINT (dense-space midpoint nearest neighbors), RANDOM.
Metric: recall@10 of true middles, macro-averaged over sentences.
"""
import sys, os, warnings, heapq, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/review6/mirror")
from mirror.meaning import MeaningGeometry

g = MeaningGeometry()
sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus.txt") if len(l.split()) >= 8]
rng = np.random.default_rng(5)
idx = rng.permutation(len(sents))
cut = int(len(sents) * 0.95)
train = [sents[i] for i in idx[:cut]]
held = [sents[i] for i in idx[cut:]]

cnt = Counter()
for s in train: cnt.update(s)
STOP = set(w for w, _ in cnt.most_common(120))
VOC = [w for w, _ in cnt.most_common(2200) if w not in STOP and w in g][:2000]
VI = {w: i for i, w in enumerate(VOC)}
N = len(VOC)
print(f"medium vocab: {N} content words")

# M1: meaning-kNN
X = np.stack([g.vec(w) for w in VOC])
S = X @ X.T
np.fill_diagonal(S, -1)
K = 8
A1 = np.zeros((N, N))
for i in range(N):
    nb = np.argpartition(S[i], -K)[-K:]
    A1[i, nb] = np.clip(S[i, nb], 0, None)
A1 = np.maximum(A1, A1.T)

# M2: attestation (sentence-window co-occurrence, window 4, count>=2)
co = defaultdict(Counter)
for s in train:
    ws = [w for w in s if w in VI]
    for a in range(len(ws)):
        for b in range(a + 1, min(a + 5, len(ws))):
            if ws[a] != ws[b]:
                co[ws[a]][ws[b]] += 1
A2 = np.zeros((N, N))
for wa, c in co.items():
    for wb, v in c.items():
        if v >= 2:
            A2[VI[wa], VI[wb]] = A2[VI[wb], VI[wa]] = np.log1p(v)

def normalize_adj(A):
    d = A.sum(1, keepdims=True); d[d == 0] = 1
    return A / d

def diffuse(A, a_idx, b_idx, steps=4, beta=0.7):
    An = normalize_adj(A)
    act = np.zeros(N); act[a_idx] = act[b_idx] = 1.0
    src = act.copy()
    for _ in range(steps):
        act = beta * (An.T @ act) + src
    act[a_idx] = act[b_idx] = -1
    return np.argsort(act)[::-1][:10]

def geodesic(A, a_idx, b_idx):
    W = np.where(A > 0, -np.log(A / (A.max() + 1e-9) + 1e-9), np.inf)
    dist = np.full(N, np.inf); dist[a_idx] = 0
    prev = np.full(N, -1); done = np.zeros(N, bool)
    h = [(0.0, a_idx)]
    while h:
        d, u = heapq.heappop(h)
        if done[u]: continue
        done[u] = True
        if u == b_idx: break
        row = W[u]
        for v in np.where(np.isfinite(row))[0]:
            nd = d + row[v]
            if nd < dist[v]:
                dist[v] = nd; prev[v] = u
                heapq.heappush(h, (nd, v))
    if not np.isfinite(dist[b_idx]): return []
    path = []; u = b_idx
    while u != -1 and u != a_idx:
        path.append(u); u = prev[u]
    inner = [p for p in path if p != b_idx]
    # pad with diffusion top-ups to 10 for fair recall@10
    extra = [i for i in diffuse(A, a_idx, b_idx) if i not in inner]
    return (inner + extra)[:10]

tests = []
for s in held:
    ws = [w for w in s if w in VI]
    ws = list(dict.fromkeys(ws))
    if len(ws) >= 5:
        tests.append((ws[0], ws[-1], set(ws[1:-1])))
    if len(tests) >= 150: break
print(f"test sentences: {len(tests)} (endpoints -> recover middles)")

def recall_at10(得, mids): pass
def evaluate(name, fn):
    rs = []
    for a, b, mids in tests:
        top = fn(a, b)
        hit = len(mids & set(top))
        rs.append(hit / min(len(mids), 10))
    print(f"  {name:22s} recall@10 = {np.mean(rs):.3f}")
    return float(np.mean(rs))

def f_m1_diff(a, b): return {VOC[i] for i in diffuse(A1, VI[a], VI[b])}
def f_m2_diff(a, b): return {VOC[i] for i in diffuse(A2, VI[a], VI[b])}
def f_m1_geo(a, b): return {VOC[i] for i in geodesic(A1, VI[a], VI[b])}
def f_m2_geo(a, b): return {VOC[i] for i in geodesic(A2, VI[a], VI[b])}
def f_mid(a, b):
    m = (g.vec(a) + g.vec(b)); m /= np.linalg.norm(m)
    sims = X @ m
    sims[VI[a]] = sims[VI[b]] = -1
    return {VOC[i] for i in np.argsort(sims)[::-1][:10]}
def f_rand(a, b): return {VOC[i] for i in rng.choice(N, 10, replace=False)}

print("\nrecall@10 of true middle content words:")
evaluate("RANDOM", f_rand)
evaluate("MIDPOINT (dense NN)", f_mid)
evaluate("M1 meaning · diffuse", f_m1_diff)
evaluate("M1 meaning · geodesic", f_m1_geo)
evaluate("M2 attested · diffuse", f_m2_diff)
evaluate("M2 attested · geodesic", f_m2_geo)
