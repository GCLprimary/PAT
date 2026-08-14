"""Probe 32: TOPIC-TO-TOPIC. Waypoint-steered generation.
Journey: category A -> category B. Four 6-token legs; the audit target
interpolates along the itinerary w(t) = norm((1-t)vA + t vB), t = leg/3.
Steered vs UNSTEERED (static prompt-topic audit, v2 behavior) vs REVERSED
itinerary (B->A; causality control).
Metrics: closure (cos of emitted content words to vB by leg -- steered must
rise), departure (cos to vA falls), end-proximity steered > unsteered,
reversed closes on A instead; refusal rate vs endpoint relatedness.
"""
import sys, os, re, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/review6/mirror")
from mirror.meaning import MeaningGeometry
from nltk.corpus import brown

g = MeaningGeometry()
big = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt") if len(l.split()) >= 6]
uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
for s in big:
    uni.update(s)
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1
STOP = set(w for w, _ in uni.most_common(120))

def norm_sent(sent):
    line = " ".join(sent).lower()
    line = re.sub(r"[-]+", " ", line)
    line = re.sub(r"[^a-z' ]", "", line)
    return [w for w in line.split() if w]

def centroid(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if not vs: return None
    v = np.mean(vs, axis=0); n = np.linalg.norm(v)
    return v / n if n > 0 else None

CATS = ["news", "religion", "science_fiction", "romance", "government", "hobbies"]
cat_vec, cat_sents = {}, {}
for c in CATS:
    ss = [norm_sent(s) for s in brown.sents(categories=c)]
    ss = [s for s in ss if len([w for w in s if w in g and w not in STOP]) >= 3]
    cat_sents[c] = ss
    cat_vec[c] = centroid([w for s in ss[:300] for w in s])

def prompt_attested(p):
    tri_hit = (p[-2], p[-1]) in tri and sum(tri[(p[-2], p[-1])].values()) >= 2
    bigs = all(p[i + 1] in bi.get(p[i], {}) for i in range(len(p) - 1))
    return tri_hit or bigs

def leg_beam(ctx_words, used, depth=6, width=8):
    outs = [(list(ctx_words), set(used))]
    for _ in range(depth):
        nxt = []
        for path, u in outs:
            c2 = (path[-2], path[-1])
            pool = tri[c2].most_common(3) if c2 in tri else \
                   (bi[path[-1]].most_common(2) if path[-1] in bi else [])
            for w, c in pool:
                bg = (path[-1], w)
                if bg in u: continue
                nxt.append((path + [w], u | {bg}))
        outs = nxt[:width]
        if not outs: break
    return [(p[len(ctx_words):], u) for p, u in outs]

def leg_score(tokens, target):
    ws = [w for w in tokens if w in g and w not in STOP]
    if not ws or target is None: return -1.0, ws
    return float(np.mean([g.vec(w) @ target for w in ws])), ws

TH = 0.10
def journey(prompt, vA, vB, mode):
    ctx = list(prompt); used = set()
    legs = []
    for k in range(4):
        t = k / 3.0
        if mode == "steer": tgt = vA * (1 - t) + vB * t
        elif mode == "rev": tgt = vB * (1 - t) + vA * t
        else: tgt = None
        if tgt is not None:
            n = np.linalg.norm(tgt); tgt = tgt / n if n > 0 else tgt
        else:
            tgt = centroid(prompt) if centroid(prompt) is not None else vA
        cands = leg_beam(ctx, used)
        if not cands: return legs, "REFUSE_BEAM"
        scored = sorted(((leg_score(tk, tgt)[0], tk, u) for tk, u in cands), reverse=True)
        s, best, u2 = scored[0]
        if s < TH: return legs, "REFUSE_AUDIT"
        legs.append(best); ctx += best; used = u2
    return legs, "OK"

rng = np.random.default_rng(7)
pairs = []
for a in CATS:
    for b in CATS:
        if a != b: pairs.append((a, b))
rng.shuffle(pairs)
pairs = pairs[:20]

res = {m: {"closB": np.zeros(4), "closA": np.zeros(4), "n": np.zeros(4), "ref": 0, "runs": 0}
       for m in ("steer", "unsteer", "rev")}
feas = []
for a, b in pairs:
    vA, vB = cat_vec[a], cat_vec[b]
    prompts = [tuple(s[:3]) for s in cat_sents[a][:400] if prompt_attested(tuple(s[:3]))][:2]
    for p in prompts:
        for mode in ("steer", "unsteer", "rev"):
            legs, st = journey(p, vA, vB, mode)
            R = res[mode]; R["runs"] += 1
            if st != "OK":
                R["ref"] += 1
                if mode == "steer": feas.append((float(vA @ vB), 1))
                continue
            if mode == "steer": feas.append((float(vA @ vB), 0))
            for k, tk in enumerate(legs):
                _, ws = leg_score(tk, vB)
                if not ws: continue
                R["closB"][k] += float(np.mean([g.vec(w) @ vB for w in ws]))
                R["closA"][k] += float(np.mean([g.vec(w) @ vA for w in ws]))
                R["n"][k] += 1

print("cos to TARGET B by leg (1->4)  [closure = rising]")
for m in ("steer", "unsteer", "rev"):
    R = res[m]
    row = R["closB"] / np.maximum(R["n"], 1)
    print(f"  {m:8s} " + "  ".join(f"{x:+.3f}" for x in row) +
          f"   refused {R['ref']}/{R['runs']}")
print("cos to SOURCE A by leg (steered should fall; reversed should rise)")
for m in ("steer", "rev"):
    R = res[m]
    row = R["closA"] / np.maximum(R["n"], 1)
    print(f"  {m:8s} " + "  ".join(f"{x:+.3f}" for x in row))
feas = np.array(feas)
if len(feas):
    med = np.median(feas[:, 0])
    lo = feas[feas[:, 0] < med][:, 1].mean() * 100
    hi = feas[feas[:, 0] >= med][:, 1].mean() * 100
    print(f"steered refusal: distant pairs {lo:.0f}%  vs close pairs {hi:.0f}%")
