"""Probe 28: GEODESICS -- do real sentences trace lower-action paths
through the dense meaning space than their own shuffles (order-only
control) and random word sequences?
Measured: action real 1.443 < shuffled 1.520 < random 1.766;
real beats own shuffle in 81% of sentences; turn-cos -0.480 vs -0.499.
"""
import sys, os, warnings, numpy as np
from collections import Counter
warnings.filterwarnings('ignore')
os.environ['MIRROR_ELFIX_PATH'] = '/home/claude/elfix/Elfix'
sys.path.insert(0, '/home/claude/review6/mirror')
from mirror.meaning import MeaningGeometry

g = MeaningGeometry()
sents = [l.split() for l in open('/home/claude/elfix/Elfix/data/corpus.txt') if len(l.split()) >= 8]
rng = np.random.default_rng(5)
cnt = Counter()
for s in sents: cnt.update(s)
STOP = set(w for w, _ in cnt.most_common(120))

def path_stats(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if len(vs) < 4: return None
    steps = [np.linalg.norm(vs[i+1] - vs[i]) for i in range(len(vs)-1)]
    turns = []
    for i in range(len(vs)-2):
        a = vs[i+1] - vs[i]; b = vs[i+2] - vs[i+1]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na > 0 and nb > 0: turns.append(float(a @ b / (na * nb)))
    return float(np.mean(np.square(steps))), (float(np.mean(turns)) if turns else np.nan)

V = [w for w, _ in cnt.most_common(4000)[300:] if w in g]
real_a, shuf_a, rand_a, real_t, shuf_t, rand_t = [], [], [], [], [], []
n = 0
for s in sents:
    if n >= 300: break
    r = path_stats(s)
    if r is None: continue
    sh = list(s); rng.shuffle(sh)
    r2 = path_stats(sh)
    rd = path_stats(list(rng.choice(V, len(s), replace=False)))
    if r2 is None or rd is None: continue
    real_a.append(r[0]); shuf_a.append(r2[0]); rand_a.append(rd[0])
    real_t.append(r[1]); shuf_t.append(r2[1]); rand_t.append(rd[1])
    n += 1
print(f'n={n}')
print(f'action: real {np.mean(real_a):.3f}  shuffled {np.mean(shuf_a):.3f}  random {np.mean(rand_a):.3f}')
print(f'turns:  real {np.nanmean(real_t):+.3f}  shuffled {np.nanmean(shuf_t):+.3f}  random {np.nanmean(rand_t):+.3f}')
print(f'real < own shuffle: {np.mean(np.array(real_a) < np.array(shuf_a))*100:.0f}%')
