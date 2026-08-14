"""Probe 23b: inversion accounting (the maths the user asked us to check).
1) Round-trip RERUN with start INFERRED (degree imbalance; balanced words
   enumerate all valid starts) -- corrected unique/exact numbers.
2) Integer snap: decode from the NORMALIZED vector (lambda sweep to snap
   entries onto the integer lattice) -- recovery rate.
3) SEAM-connectivity theorem: SUM-bound count graphs must be disconnected
   (no Eulerian path -> structural refusal); SEAM-bound must walk.
"""
import sys, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features

corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2:
        corpus[p[0]] = tuple(p[1:])

def shape(ph):
    f = features(ph)
    if str(getattr(f, "kind", "?")) == "vowel": return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))

def graph_of(ss):
    return Counter(zip(ss, ss[1:])), Counter(ss)

def infer_starts(edges, nodes):
    outd, ind = Counter(), Counter()
    for (a, b), c in edges.items():
        outd[a] += c; ind[b] += c
    plus = [n for n in nodes if outd[n] - ind[n] == 1]
    minus = [n for n in nodes if ind[n] - outd[n] == 1]
    bal_ok = all(abs(outd[n] - ind[n]) <= 1 for n in nodes)
    if not bal_ok or len(plus) > 1 or len(minus) > 1:
        return None            # not Eulerian-decodable: REFUSE
    if len(plus) == 1:
        return plus            # path case: unique start
    return [n for n in nodes if outd[n] > 0] or list(nodes)  # circuit: any active node

def walks_from(edges, start, n_edges, cap=64):
    out = []
    def rec(node, used, path):
        if len(out) >= cap: return
        if used == n_edges:
            out.append(tuple(path)); return
        for (a, b), c in sorted(edges.items()):
            if a == node and c > 0:
                edges[(a, b)] -= 1; path.append(b)
                rec(b, used + 1, path)
                path.pop(); edges[(a, b)] += 1
    rec(start, 0, [start])
    return out

def decode(edges, nodes, cap=64):
    starts = infer_starts(edges, nodes)
    if starts is None: return None
    n_edges = sum(edges.values())
    if n_edges == 0:
        return [tuple([n]) for n in nodes.elements()][:1]
    all_walks = []
    for s in starts:
        all_walks += walks_from(dict_to_counter(edges), s, n_edges, cap - len(all_walks))
        if len(all_walks) >= cap: break
    # connectivity check: a walk uses all edges; if none found, disconnected
    return all_walks

def dict_to_counter(c): return Counter(dict(c))

rng = np.random.default_rng(5)
words = [w for w in corpus if 2 <= len(corpus[w]) <= 12]
sample = [words[i] for i in rng.choice(len(words), 500, replace=False)]

print("1 · ROUND-TRIP, start INFERRED (corrected numbers)")
recon = uniq = exact = refuse = 0
for w in sample:
    ss = [shape(p) for p in corpus[w]]
    edges, nodes = graph_of(ss)
    walks = decode(dict_to_counter(edges), nodes)
    if walks is None or not walks:
        refuse += 1; continue
    recon += int(tuple(ss) in walks)
    uniq += int(len(walks) == 1)
    exact += int(walks[0] == tuple(ss))
print(f"   reconstructable {recon/5:.0f}%   unique {uniq/5:.0f}%   exact(lex tie-break) {exact/5:.0f}%   refused {refuse/5:.0f}%")

print("\n2 · INTEGER SNAP from the normalized vector")
SH = sorted({shape(p) for pr in corpus.values() for p in pr}); SHI = {s: i for i, s in enumerate(SH)}
NB = len(SH)
def count_vec(ss):
    v = np.zeros(NB * NB + NB)
    for t in ss: v[NB * NB + SHI[t]] += 1
    for a, b in zip(ss, ss[1:]): v[SHI[a] * NB + SHI[b]] += 1
    return v
snapped = 0
for w in sample[:200]:
    ss = [shape(p) for p in corpus[w]]
    c = count_vec(ss)
    u = c / np.linalg.norm(c)                      # what the embedder ships
    nz = u[u > 1e-9]
    lam = 1.0 / nz.min()                           # candidate scale from smallest entry
    ok = False
    for k in range(1, 6):                          # smallest entry could be count 1..5
        cand = u * lam * k
        r = np.round(cand)
        if np.abs(cand - r).max() < 1e-6 and np.allclose(r, c):
            ok = True; break
    snapped += int(ok)
print(f"   exact count recovery from unit vector: {snapped/2:.0f}%  (lambda sweep, k<=5)")

print("\n3 · SEAM-CONNECTIVITY THEOREM (200 mined pairs)")
pairs = []
for w in corpus:
    for sfx in ("ing", "ness", "ful"):
        if w.endswith(sfx) and len(w) > len(sfx) + 2:
            base = w[:-len(sfx)]
            if base in corpus:
                B, W = corpus[w][:0] or corpus[base], corpus[w]
                if len(W) > len(B) and W[:len(B)] == B:
                    pairs.append((base, w))
    if len(pairs) >= 200: break
seam_walk = sum_walk = 0
for base, w in pairs[:200]:
    ss_full = [shape(p) for p in corpus[w]]
    ss_base = [shape(p) for p in corpus[base]]
    ss_suf = [shape(p) for p in corpus[w][len(corpus[base]):]]
    e_seam, n_seam = graph_of(ss_full)
    e_sum = Counter(); n_sum = Counter()
    for part in (ss_base, ss_suf):
        e, n = graph_of(part)
        e_sum += e; n_sum += n
    ws = decode(dict_to_counter(e_seam), n_seam)
    wm = decode(dict_to_counter(e_sum), n_sum)
    seam_walk += int(bool(ws))
    sum_walk += int(bool(wm))
print(f"   SEAM-bound decodable: {seam_walk}/200   SUM-bound decodable: {sum_walk}/200")
print(f"   (SUM failures = disconnected or unbalanced graphs -> structural refusal)")
