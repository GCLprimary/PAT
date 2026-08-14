"""Probe 24: GENERATE-WITH-REFUSAL (the reversed mirror).
Proposer: trigram->bigram backoff counts (Brown, 95% train / 5% held out).
Audit:   a candidate stands if count-support >= 2 AND (stopword OR
         cos(dense_meaning(cand), topic_vec) >= theta_m), where topic_vec =
         mean dense vector of the prompt/emitted content words.
Refuse:  when no candidate stands (the generator declines to speak).

P1 selectivity: refusal rate on 100 in-domain prompts (held-out sentence
   openings) vs 100 word-salad prompts, theta_m in {0 (raw-ish), .05, .10}.
P2 cost/benefit: next-word top-1/top-5 on held-out positions, audit on/off;
   topical coherence of 10-token generations, audit on/off.
P3 showpieces.
"""
import sys, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/review6/mirror")
import os
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
from mirror.meaning import MeaningGeometry

sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus.txt") if len(l.split()) >= 6]
rng = np.random.default_rng(5)
idx = rng.permutation(len(sents))
cut = int(len(sents) * 0.95)
train = [sents[i] for i in idx[:cut]]
held = [sents[i] for i in idx[cut:]]

uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
for s in train:
    uni.update(s)
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1

g = MeaningGeometry()   # dense Brown, cached
STOP = set(w for w, _ in uni.most_common(120))
def topic_vec(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if not vs: return None
    v = np.mean(vs, axis=0); n = np.linalg.norm(v)
    return v / n if n > 0 else None

def candidates(ctx):
    if len(ctx) >= 2 and (ctx[-2], ctx[-1]) in tri:
        return tri[(ctx[-2], ctx[-1])].most_common(20)
    if ctx and ctx[-1] in bi:
        return bi[ctx[-1]].most_common(20)
    return []

def step(ctx, theta_m, audit=True):
    tv = topic_vec(ctx[-8:]) if audit else None
    for cand, cnt in candidates(ctx):
        if cnt < 2: continue
        if not audit or theta_m <= 0: return cand
        if cand in STOP: return cand
        if cand in g and tv is not None and float(g.vec(cand) @ tv) >= theta_m:
            return cand
        if cand not in g and tv is None: return cand
    return None   # REFUSE

def gen(prompt, theta_m, audit=True, n=10):
    ctx = list(prompt); out = []
    for _ in range(n):
        w = step(ctx, theta_m, audit)
        if w is None: return out, True
        out.append(w); ctx.append(w)
    return out, False

print("P1 · SELECTIVITY — refusal rate (refused before 10 tokens)")
prompts_id = [tuple(s[:3]) for s in held[:100]]
V = [w for w, c in uni.most_common(3000)[300:]]
prompts_ood = [tuple(rng.choice(V, 3, replace=False)) for _ in range(100)]
print("theta_m   in-domain   word-salad")
for th in (0.0, 0.05, 0.10):
    r_id = sum(int(gen(p, th)[1]) for p in prompts_id)
    r_ood = sum(int(gen(p, th)[1]) for p in prompts_ood)
    print(f"{th:.2f}      {r_id:3d}%        {r_ood:3d}%")

print("\nP2 · COST/BENEFIT")
pos = []
for s in held:
    if len(s) >= 5: pos.append((tuple(s[:3]), s[3]))
    if len(pos) >= 300: break
for audit, th in (("off", 0.0), ("on", 0.05)):
    t1 = t5 = 0
    for ctx, gold in pos:
        cands = [c for c, n in candidates(list(ctx))[:5]]
        first = step(list(ctx), th, audit == "on")
        t1 += int(first == gold)
        t5 += int(gold in cands)
    print(f"  audit {audit}: next-word top-1 {t1/3:.0f}%  (top-5 pool {t5/3:.0f}%)")
coh = {}
for audit, th in (("off", 0.0), ("on", 0.05)):
    cs = []
    for p in prompts_id[:60]:
        out, _ = gen(p, th, audit == "on")
        tv = topic_vec(p)
        for w in out:
            if w in g and w not in STOP and tv is not None:
                cs.append(float(g.vec(w) @ tv))
    coh[audit] = np.mean(cs) if cs else float("nan")
print(f"  topical coherence of generated content words: off {coh['off']:+.3f}  on {coh['on']:+.3f}")

print("\nP3 · SHOWPIECES (theta_m=0.05)")
for p in prompts_id[:3]:
    out, ref = gen(p, 0.05)
    print(f"  {' '.join(p)} | {' '.join(out)}{' [REFUSED]' if ref else ''}")
for p in prompts_ood[:3]:
    out, ref = gen(p, 0.05)
    print(f"  SALAD {' '.join(p)} | {' '.join(out)}{' [REFUSED]' if ref else ''}")
