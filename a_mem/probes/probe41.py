"""Probe 41: READING LOOP v2 — the metabolism.
Epochs of 1,000 words; after each: REVISIT deferred (unlock via new stems),
PRUNE read-taught atoms that became derivable (self-reorganization).
Gate: evidence-ordered candidates, sequence-exact stems, attested-remainder
arbitration; homophone analyses ledgered correct-by-sound.
Metrics/epoch: known, deferred, unlocked, pruned, censuses, aligned
coverage, REAL confabs (invariant: 0).
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
import sys
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features as feat

def shp(p):
    f = feat(p)
    if str(getattr(f, "kind", "?")) == "vowel": return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
def skey(w): return tuple(shp(p) for p in corpus[w])

attested_rem = defaultdict(set); byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    attested_rem[sfx].add(tuple(rem)); byb[base][sfx] = w
ALL_REMS = set()
for s_, rs in attested_rem.items(): ALL_REMS |= rs

cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"):
    cnt.update(l.split())
stream = [w for w, c in cnt.most_common() if c >= 4 and w in corpus and len(w) >= 4][:6000]
stream_set = set(stream)

D = len(vec(corpus["the"], "shape"))
rows = np.zeros((40000, D)); meta = []; nrows = 0
known = {}; retired = {}
def add_rows(b):
    global nrows
    rows[nrows] = vec(corpus[b], "shape"); meta.append(("BARE", b, None)); nrows_ = nrows + 1
    globals()["nrows"] = nrows_
    for sfx in SUFFIXES:
        if sfx in modal_phon:
            rows[globals()["nrows"]] = predict(corpus[b], sfx, "shape", "SEAM")
            meta.append(("DER", b, sfx)); globals()["nrows"] += 1
def teach(b, prov):
    known[b] = prov; add_rows(b)

for b in list(byb.keys())[:15]: teach(b, "birth")

def gate(obs, kind, b, sfx):
    if b in retired: return False
    if kind == "BARE":
        return tuple(obs) == tuple(corpus[b])
    L = len(corpus[b])
    return len(obs) > L and tuple(obs[:L]) == tuple(corpus[b]) and tuple(obs[L:]) in attested_rem[sfx]

def analyze(w, exclude=None):
    obs = corpus[w]; v = vec(obs, "shape")
    sc = rows[:nrows] @ v
    order = np.argsort(sc)[::-1][:14]
    for i in order:
        if sc[i] < 0.98: break
        kind, b, sfx = meta[i]
        if b == exclude: continue
        if gate(obs, kind, b, sfx):
            return (kind, b, sfx)
    return ("REFUSE", None, None)

def looks_derived(w):
    p = corpus[w]
    return any(tuple(p[-k:]) in ALL_REMS for k in (1, 2)) and len(p) >= 5

test = [(b, s, w) for b, d in byb.items() if b in stream_set for s, w in d.items()][:300]
def coverage():
    ok = real = homo = 0
    for b, s, w in test:
        k, gb, gs = analyze(w)
        if k == "DER" and gb == b and gs == s: ok += 1
        elif k != "REFUSE":
            same_sound = gb in corpus and tuple(corpus[gb]) == tuple(corpus[b] if k == "DER" else corpus[w])
            if same_sound: homo += 1
            else: real += 1
    return ok / len(test) * 100, real, homo

deferred = []; census = []; unlocked = pruned = 0
print("epoch  known  deferred  unlocked  pruned  census  coverage%  REALconfab  homoph")
for ep in range(6):
    chunk = stream[ep * 1000:(ep + 1) * 1000]
    for w in chunk:
        k, gb, gs = analyze(w)
        if k == "REFUSE" and w in byb and w not in known and w not in retired:
            if looks_derived(w): deferred.append(w)
            else:
                same = [b for b in known if skey(b) == skey(w)]
                if same: census.append((w, same[0]))
                teach(w, "read")
    still = []
    for w in deferred:
        k, gb, gs = analyze(w)
        if k == "DER":
            unlocked += 1
        else:
            still.append(w)
    deferred = still
    for b in [x for x, p in known.items() if p == "read"]:
        k, gb, gs = analyze(b, exclude=b)
        if k == "DER":
            retired[b] = f"pruned: {gb}+{gs}"
            del known[b]; pruned += 1
    cov, real, homo = coverage()
    print(f"  {ep+1}    {len(known):5d}   {len(deferred):5d}    {unlocked:5d}    {pruned:4d}   {len(census):4d}    {cov:5.1f}      {real:3d}       {homo:3d}")
print(f"\nsample prunes: {list(retired.items())[:3]}")
print(f"sample census: {census[:3]}")
