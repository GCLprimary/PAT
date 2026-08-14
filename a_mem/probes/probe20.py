"""Probe 20: THE LOOP -- propose / reflect / keep-what-stands, with an audit.
Task: given a surface derived word, recover (base, suffix) -- or REFUSE if
the base is unknown to memory. Layered loop:
  L1: is the observation itself a known base? (reflect against bare bases)
  L2: propose base x suffix bindings, reflect bound predictions vs observation
  settle if best standing agreement >= theta, else refuse.
Test set: 20 derived words with bases IN memory + 20 with bases WITHHELD.
Baselines: raw nearest-neighbor (no transform); longest-suffix stripping.
"""
import sys, tempfile, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

rng2 = np.random.default_rng(11)
byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    byb[base][sfx] = w
cands = [b for b, d in byb.items() if len(d) >= 1 and len(b) >= 4]
rng2.shuffle(cands)
known_bases = cands[:40]
withheld = cands[40:80]

def pick_tests(bases, n):
    out = []
    for b in bases:
        for sfx, w in byb[b].items():
            out.append((b, sfx, w)); break
        if len(out) >= n: break
    return out
test_known = pick_tests(known_bases, 20)
test_unknown = pick_tests(withheld, 20)
SP = "shape"

base_vecs = {b: vec(corpus[b], SP) for b in known_bases}
bound = {}  # (b, sfx) -> bound prediction
for b in known_bases:
    for sfx in SUFFIXES:
        if sfx in modal_phon:
            bound[(b, sfx)] = predict(corpus[b], sfx, SP, "SEAM")

def loop_analyze(w_pron, theta):
    obs = vec(w_pron, SP)
    # L1: bare reflection
    s1 = {b: float(obs @ v) for b, v in base_vecs.items()}
    b1 = max(s1, key=s1.get)
    if s1[b1] >= theta:
        return ("BARE", b1, None, s1[b1], 1)
    # L2: bound reflection
    s2 = {k: float(obs @ v) for k, v in bound.items()}
    k2 = max(s2, key=s2.get)
    if s2[k2] >= theta:
        return ("BOUND", k2[0], k2[1], s2[k2], 2)
    return ("REFUSE", None, None, max(s1[b1], s2[k2]), 2)

def strip_baseline(word):
    for sfx in sorted(SUFFIXES, key=len, reverse=True):
        if word.endswith(sfx) and word[:-len(sfx)] in known_bases:
            return word[:-len(sfx)], sfx
    return None, None

def nn_baseline(w_pron):
    obs = vec(w_pron, SP)
    s = {b: float(obs @ v) for b, v in base_vecs.items()}
    b = max(s, key=s.get)
    return b, s[b]

print(f"known bases in memory: {len(known_bases)}; tests: {len(test_known)} known / {len(test_unknown)} withheld")
print("\ntheta   KNOWN: base+sfx correct | refused(bad)   WITHHELD: refused(good) | confabulated")
for theta in (0.90, 0.95, 0.98):
    okk = refk = 0
    for b, sfx, w in test_known:
        mode, pb, ps, sc, depth = loop_analyze(corpus[w], theta)
        if mode == "REFUSE": refk += 1
        elif pb == b and ps == sfx: okk += 1
    refu = confab = 0
    for b, sfx, w in test_unknown:
        mode, pb, ps, sc, depth = loop_analyze(corpus[w], theta)
        if mode == "REFUSE": refu += 1
        else: confab += 1
    print(f"{theta:.2f}     {okk}/20 correct | {refk} refused        "
          f"{refu}/20 refused | {confab} confabulated")

print("\nbaselines on KNOWN set:")
ok = 0
for b, sfx, w in test_known:
    pb, ps = strip_baseline(w)
    ok += int(pb == b and ps == sfx)
print(f"  longest-suffix strip: {ok}/20 base+sfx correct (has orthography; no refusal concept)")
ok = 0
for b, sfx, w in test_known:
    pb, _ = nn_baseline(corpus[w])
    ok += int(pb == b)
print(f"  raw NN (no transform): {ok}/20 base correct, 0/20 suffix (cannot name one)")
ok = 0
for b, sfx, w in test_unknown:
    pb, sc = nn_baseline(corpus[w])
    ok += 1  # NN always answers
print(f"  raw NN on WITHHELD: confabulates {ok}/20 (no refusal mechanism)")
