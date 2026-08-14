"""Probe 30: the two doors.
A) TOPIC RUNG: predict the true middle-content centroid of held sentences.
   Predictors: endpoint midpoint vs single endpoints vs global mean.
   If midpoint >> singles, two endpoints constrain the middle REGION.
B) REFOUNDING: discourse working-memory. Constructed documents = 3 segments
   x 4 sentences from different Brown categories. Stage model: maintained
   state s; per sentence v: if cos(s,v) < theta -> PAGE-TURN (boundary),
   reset; else s <- blend. Baseline: memoryless consecutive-sentence cosine
   thresholded. Metric: boundary F1 (tolerance 1), theta fit on dev docs.
"""
import sys, os, warnings, numpy as np
from collections import Counter
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/review6/mirror")
from mirror.meaning import MeaningGeometry
import nltk, re
from nltk.corpus import brown

g = MeaningGeometry()
cnt = Counter()
sents_all = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus.txt")]
for s in sents_all: cnt.update(s)
STOP = set(w for w, _ in cnt.most_common(120))

def centroid(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if not vs: return None
    v = np.mean(vs, axis=0); n = np.linalg.norm(v)
    return v / n if n > 0 else None

print("A · TOPIC RUNG — cosine(predicted, true middle centroid)")
held = [s for s in sents_all if len(s) >= 8][-2000:]
rng = np.random.default_rng(5)
G = centroid([w for s in held[:400] for w in s])
rows = {"midpoint": [], "endpoint-a": [], "endpoint-b": [], "global": []}
n = 0
for s in held:
    ws = [w for w in s if w in g and w not in STOP]
    ws = list(dict.fromkeys(ws))
    if len(ws) < 5: continue
    a, b, mids = ws[0], ws[-1], ws[1:-1]
    mc = centroid(mids)
    if mc is None: continue
    va, vb = g.vec(a), g.vec(b)
    vm = va + vb; vm /= np.linalg.norm(vm)
    rows["midpoint"].append(float(vm @ mc))
    rows["endpoint-a"].append(float(va @ mc))
    rows["endpoint-b"].append(float(vb @ mc))
    rows["global"].append(float(G @ mc))
    n += 1
    if n >= 300: break
for k, v in rows.items():
    print(f"   {k:11s} {np.mean(v):+.3f}")

print("\nB · DISCOURSE WORKING-MEMORY — boundary F1 (tol 1)")
def norm_sent(sent):
    line = " ".join(sent).lower()
    line = re.sub(r"[-]+", " ", line)
    line = re.sub(r"[^a-z' ]", "", line)
    return [w for w in line.split() if w]

CATS = ["news", "religion", "science_fiction", "romance", "government", "hobbies"]
cat_sents = {}
for c in CATS:
    ss = [norm_sent(s) for s in brown.sents(categories=c)]
    cat_sents[c] = [s for s in ss if len([w for w in s if w in g and w not in STOP]) >= 3]

def make_doc(rng):
    cats = rng.choice(CATS, 3, replace=False)
    doc, bounds, pos = [], [], 0
    for c in cats:
        start = rng.integers(0, len(cat_sents[c]) - 4)
        seg = cat_sents[c][start:start + 4]
        doc += seg; pos += len(seg); bounds.append(pos)
    return doc, set(bounds[:-1])   # internal boundaries only

def sent_vecs(doc):
    return [centroid(s) for s in doc]

def stage_boundaries(vs, theta, blend=0.5):
    s = vs[0]; out = set()
    for i in range(1, len(vs)):
        v = vs[i]
        if v is None: continue
        if s is None or float(s @ v) < theta:
            out.add(i); s = v          # page-turn: flatten, reseat
        else:
            s = blend * s + (1 - blend) * v
            s /= np.linalg.norm(s)
    return out

def memoryless_boundaries(vs, theta):
    out = set()
    for i in range(1, len(vs)):
        if vs[i] is None or vs[i - 1] is None: continue
        if float(vs[i - 1] @ vs[i]) < theta:
            out.add(i)
    return out

def f1(pred, gold, tol=1):
    tp = sum(1 for b in gold if any(abs(b - p) <= tol for p in pred))
    prec = tp / len(pred) if pred else 0.0
    rec = tp / len(gold) if gold else 0.0
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0

rng = np.random.default_rng(9)
docs = [make_doc(rng) for _ in range(50)]
dev, test = docs[:15], docs[15:]
best = {}
for name, fn in (("stage+page-turn", stage_boundaries), ("memoryless", memoryless_boundaries)):
    bt, bf = None, -1
    for theta in np.arange(0.05, 0.95, 0.05):
        f = np.mean([f1(fn(sent_vecs(d), theta), b) for d, b in dev])
        if f > bf: bf, bt = f, theta
    tf = np.mean([f1(fn(sent_vecs(d), bt), b) for d, b in test])
    best[name] = (bt, tf)
    print(f"   {name:16s} theta*={bt:.2f}  test F1 = {tf:.3f}")
rand = np.mean([f1(set(rng.choice(range(1, 12), 2, replace=False)), b) for d, b in test])
print(f"   random-2-cuts     test F1 = {rand:.3f}")
