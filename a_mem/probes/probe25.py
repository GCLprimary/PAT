"""Probe 25: PREFIX BREADTH (the S-4 gate's evidence).
Mine prefix pairs (derived pron ENDS with base pron); learn modal prefix
forms from a train split; SEAM vs SUM prefix-side; loop gains L3
(prefix-bound proposals) tested with known and withheld bases.
"""
import sys, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features

corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2: corpus[p[0]] = tuple(p[1:])

def shape(ph):
    f = features(ph)
    if str(getattr(f, "kind", "?")) == "vowel": return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
SH = sorted({shape(p) for pr in corpus.values() for p in pr}); SHI = {s: i for i, s in enumerate(SH)}
NB = len(SH)
def vec(seq):
    v = np.zeros(NB * NB + NB)
    ss = [shape(p) for p in seq]
    for t in ss: v[NB * NB + SHI[t]] += 1
    for a, b in zip(ss, ss[1:]): v[SHI[a] * NB + SHI[b]] += 1
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

PREFIXES = ["un", "re", "dis", "mis", "pre", "over", "out"]
pairs = []
for w in corpus:
    for pre in PREFIXES:
        if w.startswith(pre) and len(w) > len(pre) + 2:
            base = w[len(pre):]
            if base in corpus:
                B, W = corpus[base], corpus[w]
                if len(W) > len(B) and W[-len(B):] == B:
                    pairs.append((base, pre, w, W[:len(W) - len(B)]))
rng = np.random.default_rng(7)
rng.shuffle(pairs)
by_pre = defaultdict(list)
for pr in pairs: by_pre[pr[1]].append(pr)
train, test = [], []
for pre, lst in by_pre.items():
    k = int(len(lst) * 0.6)
    train += lst[:k]; test += lst[k:]
print(f"mined {len(pairs)} prefix pairs; per-prefix: " +
      ", ".join(f"{p}:{len(by_pre[p])}" for p in PREFIXES if by_pre[p]))
rem_counts = {p: Counter(tuple(r[3]) for r in train if r[1] == p) for p in PREFIXES}
modal = {p: list(c.most_common(1)[0][0]) for p, c in rem_counts.items() if c}
print("prefix allomorph counts (train):", {p: len(c) for p, c in rem_counts.items() if c})

def pred(base_pron, pre, rule):
    if rule == "SEAM": return vec(modal[pre] + list(base_pron))
    v = vec(modal[pre]) + vec(base_pron)
    return v / np.linalg.norm(v)

for rule in ("SUM", "SEAM"):
    cs = [float(pred(corpus[b], p, rule) @ vec(corpus[w])) for b, p, w, _ in test[:400]]
    print(f"{rule}: held-out mean cos {np.mean(cs):.3f}")

# loop L3
known = sorted({b for b, _, _, _ in test})[:40]
with_t = [(b, p, w) for b, p, w, _ in test if b in known][:20]
withheld_bases = sorted({b for b, _, _, _ in test} - set(known))[:40]
wo_t = [(b, p, w) for b, p, w, _ in test if b in withheld_bases][:20]
base_vecs = {b: vec(corpus[b]) for b in known}
bound = {(b, p): pred(corpus[b], p, "SEAM") for b in known for p in modal}
THETA = 0.98
def analyze(w_pron):
    obs = vec(w_pron)
    s1 = {b: float(obs @ v) for b, v in base_vecs.items()}
    b1 = max(s1, key=s1.get)
    if s1[b1] >= THETA: return ("BARE", b1, None)
    s3 = {k: float(obs @ v) for k, v in bound.items()}
    k3 = max(s3, key=s3.get)
    if s3[k3] >= THETA: return ("PRE", k3[0], k3[1])
    return ("REFUSE", None, None)
okk = sum(int(analyze(corpus[w])[:3] == ("PRE", b, p)) for b, p, w in with_t)
refu = sum(int(analyze(corpus[w])[0] == "REFUSE") for b, p, w in wo_t)
confab = len(wo_t) - refu
print(f"loop L3: known {okk}/{len(with_t)} correct   withheld {refu}/{len(wo_t)} refused, {confab} confabulated")
