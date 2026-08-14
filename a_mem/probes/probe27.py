"""Probe 27: GENERATE-WITH-REFUSAL v2 (the redesign probe 24 earned).
Three planks, all from probe 24's diagnosis:
  1. Refuse from PROPOSER STATE at the prompt rung: an unattested prompt
     (no trigram context AND broken internal bigrams) is refused before
     a word is emitted.
  2. Reflect WHOLE CONTINUATIONS: beam over trigram continuations (depth 6,
     beam 8); score each whole beam by topical coherence to the prompt.
  3. Anti-rut: a continuation reusing any bigram twice is discarded
     (the flood check); best survivor must clear theta, else refuse.
Acceptance: salad-refusal minus in-domain-refusal >= 50 points, and
emitted continuations' coherence > v1's (+0.250).
"""
import sys, os, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/review6/mirror")
from mirror.meaning import MeaningGeometry

sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus.txt") if len(l.split()) >= 6]
rng = np.random.default_rng(5)
idx = rng.permutation(len(sents)); cut = int(len(sents) * 0.95)
train = [sents[i] for i in idx[:cut]]; held = [sents[i] for i in idx[cut:]]
uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
for s in train:
    uni.update(s)
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1

g = MeaningGeometry()
STOP = set(w for w, _ in uni.most_common(120))
def topic_vec(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if not vs: return None
    v = np.mean(vs, axis=0); n = np.linalg.norm(v)
    return v / n if n > 0 else None

def prompt_attested(p):
    tri_hit = (p[-2], p[-1]) in tri and sum(tri[(p[-2], p[-1])].values()) >= 2
    bigs = all(p[i + 1] in bi.get(p[i], {}) for i in range(len(p) - 1))
    return tri_hit or bigs

def beams(prompt, depth=6, width=8):
    outs = [(list(prompt), set())]
    for _ in range(depth):
        nxt = []
        for path, used in outs:
            ctx = (path[-2], path[-1])
            cands = tri.get(ctx, None)
            pool = cands.most_common(3) if cands else \
                   (bi[path[-1]].most_common(2) if path[-1] in bi else [])
            for w, c in pool:
                bg = (path[-1], w)
                if bg in used: continue          # anti-rut: no bigram twice
                nxt.append((path + [w], used | {bg}))
        outs = nxt[:width * 3]
        outs = outs[:width]
        if not outs: break
    return [p[len(prompt):] for p, _ in outs]

def score(cont, tv):
    ws = [w for w in cont if w in g and w not in STOP]
    if tv is None or not ws: return -1.0
    return float(np.mean([g.vec(w) @ tv for w in ws]))

THETA = 0.15
def gen2(prompt):
    if not prompt_attested(prompt): return None, "REFUSE_PROMPT"
    tv = topic_vec(prompt)
    bs = beams(prompt)
    if not bs: return None, "REFUSE_NO_BEAM"
    scored = sorted(((score(c, tv), c) for c in bs), reverse=True)
    s, best = scored[0]
    if s < THETA: return None, "REFUSE_AUDIT"
    return best, "OK"

prompts_id = [tuple(s[:3]) for s in held[:100]]
V = [w for w, c in uni.most_common(3000)[300:]]
prompts_ood = [tuple(rng.choice(V, 3, replace=False)) for _ in range(100)]

r_id = r_ood = 0
coh = []
for p in prompts_id:
    out, st = gen2(p)
    r_id += int(out is None)
    if out: coh.append(score(out, topic_vec(p)))
for p in prompts_ood:
    out, st = gen2(p)
    r_ood += int(out is None)
print("v2 SELECTIVITY:")
print(f"  in-domain refused:  {r_id}%")
print(f"  word-salad refused: {r_ood}%")
print(f"  gap: {r_ood - r_id} points (acceptance >= 50)")
print(f"  emitted coherence: {np.mean(coh):+.3f}  (v1 was +0.250)")
print("\nshowpieces:")
for p in prompts_id[:3]:
    out, st = gen2(p)
    print(f"  {' '.join(p)} | {' '.join(out) if out else '['+st+']'}")
for p in prompts_ood[:3]:
    out, st = gen2(p)
    print(f"  SALAD {' '.join(p)} | {' '.join(out) if out else '['+st+']'}")
