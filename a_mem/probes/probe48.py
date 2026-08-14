"""Probe 48: THE FOLD (chapters — the metabolic synthesis step).
Chapter = unit-norm fold (mean) of a family's member vectors in shape
space, members = base + its mined derived forms (>= 3 members).
Two fold recipes: SURFACE (raw member observation vectors) vs BOUND
(base vec + seam-carrying bound vectors — the seams travel into the
fold). Measured:
  A addressing        — every member's nearest chapter is its own
  B held-out address  — a member EXCLUDED from the fold still finds it
  C crowding          — inter-chapter max-cosine census vs word-level
  D inherited census  — homoshape base pairs -> chapter collision?
     (prediction: the eyes lesson recurses a rung up)
"""
import warnings, numpy as np
from collections import defaultdict
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

fam = defaultdict(list)
for base, sfx, w, rem in pairs:
    fam[base].append((sfx, w))
families = [(b, d) for b, d in fam.items() if len(d) >= 3][:500]
print(f"families (>=3 derived): {len(families)}")

def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def fold_surface(b, members):
    vs = [vec(corpus[b], "shape")] + [vec(corpus[w], "shape") for _, w in members]
    return unit(np.sum(vs, axis=0))

def fold_bound(b, members):
    vs = [vec(corpus[b], "shape")]
    for sfx, w in members:
        if sfx in modal_phon:
            vs.append(predict(corpus[b], sfx, "shape", "SEAM"))
        else:
            vs.append(vec(corpus[w], "shape"))
    return unit(np.sum(vs, axis=0))

for name, fold in (("SURFACE", fold_surface), ("BOUND", fold_bound)):
    C = np.stack([fold(b, d) for b, d in families])
    labels = [b for b, _ in families]
    # A: full-member addressing
    ok = tot = 0
    for fi, (b, d) in enumerate(families):
        for w in [b] + [w for _, w in d]:
            s = C @ vec(corpus[w], "shape")
            ok += int(int(np.argmax(s)) == fi); tot += 1
    # B: held-out addressing (refold without the last derived member)
    hok = htot = 0
    for fi, (b, d) in enumerate(families):
        held_sfx, held_w = d[-1]
        C2row = fold(b, d[:-1])
        Cx = C.copy(); Cx[fi] = C2row
        s = Cx @ vec(corpus[held_w], "shape")
        hok += int(int(np.argmax(s)) == fi); htot += 1
    # C: crowding census
    G = C @ C.T
    np.fill_diagonal(G, -1)
    mx = G.max(axis=1)
    # D: inherited homoshape collisions among these families
    groups = defaultdict(list)
    for fi, (b, d) in enumerate(families):
        groups[skey(b)].append(fi)
    coll = [g for g in groups.values() if len(g) >= 2]
    pairsim = []
    for g in coll:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                pairsim.append(float(C[g[i]] @ C[g[j]]))
    print(f"\n{name} fold:")
    print(f"  A addressing (all members): {ok}/{tot} = {ok/tot*100:.1f}%")
    print(f"  B held-out member finds its chapter: {hok}/{htot} = {hok/htot*100:.1f}%")
    print(f"  C crowding: max inter-chapter cos mean {mx.mean():.3f}  p95 {np.quantile(mx,0.95):.3f}  max {mx.max():.4f}")
    if pairsim:
        print(f"  D inherited census: {len(coll)} colliding-base family groups; "
              f"chapter-pair cos mean {np.mean(pairsim):.4f}  max {np.max(pairsim):.4f}")
