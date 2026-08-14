"""Probe 40: THE READING LOOP (self-creation, gated).
The creature reads corpus_big in frequency order. For each word:
  - analyze via shape loop + PHON GATE (stem theta_p=0.77 + attested-
    remainder arbitration). Known/derivable -> nothing to learn.
  - REFUSED + attested (count >= 5, in CMU, len >= 4): SELF-TEACH as a
    new base with provenance 'read', UNLESS it looks derived (remainder
    matches an attested suffix form) -> defer, wait for the stem.
Measured: vocabulary growth, coverage on a held derived-form test set,
confabulations (gate on -> must stay 0), self-census (collisions the
creature discovers about itself as it grows).
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
def phonv(seq): return vec(seq, "phon")

attested_rem = defaultdict(set)
byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    attested_rem[sfx].add(tuple(rem)); byb[base][sfx] = w
ALL_REMS = set()
for s_, rs in attested_rem.items(): ALL_REMS |= rs

cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"):
    cnt.update(l.split())
stream = [w for w, c in cnt.most_common() if c >= 5 and w in corpus and len(w) >= 4][:3000]

known = {}          # base -> provenance
def teach(b, prov): known[b] = prov

for b in list(byb.keys())[:15]:
    teach(b, "birth")

TH, TH_P = 0.98, 0.77
def analyze(w):
    obs = corpus[w]; ov = vec(obs, "shape")
    best = None; bs = -1
    for b in known:
        s = float(ov @ vec(corpus[b], "shape"))
        if s > bs: bs, best = s, ("BARE", b)
        for sfx in SUFFIXES:
            if sfx not in modal_phon: continue
            s2 = float(ov @ predict(corpus[b], sfx, "shape", "SEAM"))
            if s2 > bs: bs, best = s2, ("DER", b, sfx)
    if bs < TH or best is None: return ("REFUSE",)
    # PHON GATE
    if best[0] == "BARE":
        b = best[1]
        if len(obs) == len(corpus[b]) and float(phonv(obs) @ phonv(corpus[b])) >= 0.999:
            return best
        return ("REFUSE",)
    b, sfx = best[1], best[2]
    L = len(corpus[b])
    if len(obs) <= L: return ("REFUSE",)
    if float(phonv(obs[:L]) @ phonv(corpus[b])) < TH_P: return ("REFUSE",)
    if tuple(obs[L:]) not in attested_rem[sfx]: return ("REFUSE",)
    return best

def looks_derived(w):
    p = corpus[w]
    return any(tuple(p[-k:]) in ALL_REMS for k in (1, 2)) and len(p) >= 5

test = [(b, s, w) for b, d in byb.items() for s, w in d.items()][:400]
def coverage():
    ok = confab = 0
    for b, s, w in test:
        r = analyze(w)
        if r[0] == "DER" and r[1] == b and r[2] == s: ok += 1
        elif r[0] != "REFUSE":
            if not (r[0] == "BARE" and r[1] == w): confab += 1
    return ok / len(test) * 100, confab

deferred = []
census = []
snap = []
for i, w in enumerate(stream):
    r = analyze(w)
    if r[0] == "REFUSE" and w in byb and w not in known:
        if looks_derived(w):
            deferred.append(w)
        else:
            k = skey(w)
            hits = [b for b in known if skey(b) == k]
            if hits: census.append((w, hits[0]))
            teach(w, "read")
    if i in (99, 499, 999, 1999, 2999):
        cov, cf = coverage()
        snap.append((i + 1, len(known), cov, cf, len(census), len(deferred)))

print("words-read  known-bases  coverage%  confabs  self-census  deferred")
for row in snap:
    print("   {:5d}      {:5d}      {:5.1f}      {:3d}       {:4d}      {:4d}".format(*row))
prov = Counter(known.values())
print(f"\nprovenance ledger: {dict(prov)}")
print("sample self-census entries (creature's own ambiguity ledger):",
      census[:4])
