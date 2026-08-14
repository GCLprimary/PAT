"""Probe 50: THE TOWER (the user's curvature question, measured).
Claims to test:
  1 TILT — the angle between v(base) and v(base+sfx): the "45 degrees"
    is the orthogonal ideal; measure the real tilt.
  2 COST — ||v(a)+v(b)|| vs the sphere's charge (normalization divides
    by it); per-junction cost ~ sqrt2 - 1 in the orthogonal limit.
  3 CURVATURE ACCUMULATES — 3-morpheme words (prefix+base+suffix):
    cos(unit(SUM), actual) must be LOWER than the 2-morpheme 0.878.
  4 THE CONE IS FLAT — in raw count space the identity is EXACT:
    counts(p+b+s) == counts(p)+counts(b)+counts(s)+junction bigrams.
    Integer equality, asserted, no cosine anywhere.
"""
import warnings, numpy as np
from collections import defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

# raw (unnormalized) count embedder mirroring vec()'s features
import sys
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features as feat
def shp(p):
    f = feat(p)
    return ("V",) if str(getattr(f, "kind", "?")) == "vowel" else \
        (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
DIMS = {}
def counts_of(phones):
    c = defaultdict(int)
    ss = [shp(p) for p in phones]
    for s in ss: c[("u", s)] += 1
    for a, b in zip(ss, ss[1:]): c[("b", a, b)] += 1
    return c
def cvec(c):
    for k in c:
        if k not in DIMS: DIMS[k] = len(DIMS)
    v = np.zeros(4096)
    for k, n in c.items(): v[DIMS[k]] = n
    return v

# 1 & 2 — tilt and per-junction cost over 400 suffix pairs
tilts, costs, orth = [], [], []
for base, sfx, w, rem in pairs[:400]:
    va, vw = vec(corpus[base], "shape"), vec(corpus[w], "shape")
    tilts.append(np.degrees(np.arccos(np.clip(va @ vw, -1, 1))))
    vb = vec(rem, "shape") if rem else None
    if vb is not None:
        n = np.linalg.norm(va + vb)
        costs.append(n - 1.0)             # the sphere's charge minus flat
        orth.append(np.degrees(np.arccos(np.clip(va @ vb, -1, 1))))
print(f"1 TILT base->derived: mean {np.mean(tilts):.1f} deg (45 = orthogonal ideal)")
print(f"2 COST per junction: mean ||a+b||-1 = {np.mean(costs):.3f} "
      f"(sqrt2-1 = {np.sqrt(2)-1:.3f}); base-vs-suffix angle mean {np.mean(orth):.1f} deg")

# triples: prefix + base + suffix, all attested in corpus
pref = []
for w2 in corpus:
    for p in ("re", "un", "over", "out", "under", "mis", "pre"):
        if w2.startswith(p) and w2[len(p):] in corpus and len(w2[len(p):]) >= 3:
            pref.append((p, w2[len(p):], w2))
byb2 = defaultdict(dict)
for base, sfx, w, rem in pairs: byb2[base][sfx] = (w, rem)
triples = []
for p, base, pw in pref:
    for sfx, (w, rem) in byb2.get(base, {}).items():
        full = p + w
        if full in corpus:
            triples.append((p, base, sfx, w, pw, full, rem))
triples = triples[:200]
print(f"\n3-morpheme words found: {len(triples)} (e.g., "
      + ", ".join(t[5] for t in triples[:4]) + ")")

# 3 — curvature accumulation on the sphere
c2, c3 = [], []
for base, sfx, w, rem in pairs[:200]:
    s = vec(corpus[base], "shape") + (vec(rem, "shape") if rem else 0)
    c2.append(float((s / np.linalg.norm(s)) @ vec(corpus[w], "shape")))
for p, base, sfx, w, pw, full, rem in triples:
    parts = vec(corpus[pw][:len(corpus[pw]) - len(corpus[base])], "shape") \
        + vec(corpus[base], "shape") + (vec(rem, "shape") if rem else 0)
    c3.append(float((parts / np.linalg.norm(parts)) @ vec(corpus[full], "shape")))
print(f"3 SPHERE: cos(unit(SUM), actual)  2-morph {np.mean(c2):.3f}   "
      f"3-morph {np.mean(c3):.3f}   (curvature accumulates: {np.mean(c3) < np.mean(c2)})")

# 4 — the cone: exact integer identity with junction bigrams
exact = 0
for p, base, sfx, w, pw, full, rem in triples:
    pph = corpus[pw][:len(corpus[pw]) - len(corpus[base])]
    bph, fph = corpus[base], corpus[full]
    if list(fph) != list(pph) + list(bph) + list(rem): continue
    lhs = counts_of(fph)
    rhs = counts_of(pph)
    for k, n in counts_of(bph).items(): rhs[k] += n
    for k, n in counts_of(rem).items(): rhs[k] += n
    for a, b in ((pph[-1], bph[0]),) + (((bph[-1], rem[0]),) if rem else ()):
        rhs[("b", shp(a), shp(b))] += 1
    exact += int(dict(lhs) == dict(rhs))
print(f"4 CONE: counts(p+b+s) == sum of parts + junction bigrams: "
      f"{exact}/{len(triples)} EXACT integer identities")
