"""E-3 (probe 50): the tower — doctrine with numbers.

THE CONE IS FLAT: on every phonologically-faithful prefix+base+suffix
triple, counts(p+b+s) equals the sum of part counts plus the junction
bigrams — EXACT integer equality, no cosine anywhere. The unfaithful
remainder is the VOWEL-REDUCTION CENSUS (English declining to
concatenate), counted and named, never scored as error.

Recorded bands (the sphere's curvature doctrine): base->derived tilt
22.5 ± 3 degrees (45 is the orthogonal ideal; the base's mass leans
the ray); per-junction charge ||a+b|| − 1 = 0.535 ± 0.03 over the
ad-quadratum floor √2 − 1 = 0.414; and the DILUTION LAW — relative
curvature ∝ junctions/mass, so the 3-morpheme SUM-cosine EXCEEDS the
2-morpheme one: the sphere flattens as words grow, and the seam
matters most for short words.
"""
from collections import defaultdict

import numpy as np
import pytest

from mirror.geometry import cone_identity, counts_of, mass

PREFIXES = ("re", "un", "over", "out", "under", "mis", "pre")


@pytest.fixture(scope="module")
def triples(embedder, transform):
    byb = defaultdict(dict)
    for base, sfx, w, rem in transform.pairs:
        byb[base][sfx] = (w, rem)
    out = []
    for w2 in embedder.corpus:
        for p in PREFIXES:
            if w2.startswith(p) and w2[len(p):] in embedder.corpus \
                    and len(w2[len(p):]) >= 3:
                base = w2[len(p):]
                for sfx, (w, rem) in byb.get(base, {}).items():
                    if p + w in embedder.corpus:
                        out.append((p, base, sfx, w, w2, p + w, rem))
    return out[:200]


def test_cone_identity_exact(embedder, triples):
    """Integer equality on every faithful triple; the census named."""
    faithful = census = exact = 0
    for p, base, sfx, w, pw, full, rem in triples:
        pph = list(embedder.corpus[pw][:len(embedder.corpus[pw])
                                       - len(embedder.corpus[base])])
        bph = list(embedder.corpus[base])
        fph = list(embedder.corpus[full])
        if fph != pph + bph + list(rem):
            census += 1              # vowel reduction: not an error
            continue
        faithful += 1
        lhs, rhs = cone_identity(pph, bph, list(rem))
        exact += int(lhs == rhs)
    print(f"\ncone: {exact}/{faithful} EXACT integer identities; "
          f"vowel-reduction census {census} (named, not scored)")
    assert faithful >= 150
    assert exact == faithful, \
        f"THE CONE BENT: {faithful - exact} faithful triples broke " \
        f"integer additivity — the flat floor is load-bearing"
    assert census > 0, "the census emptied — English started " \
        "concatenating; check the corpus"


def test_curvature_bands_and_dilution(embedder, transform, triples):
    tilts, costs = [], []
    for base, sfx, w, rem in transform.pairs[:400]:
        va = embedder.shape_vec(embedder.corpus[base])
        vw = embedder.shape_vec(embedder.corpus[w])
        tilts.append(np.degrees(np.arccos(np.clip(va @ vw, -1, 1))))
        if rem:
            costs.append(np.linalg.norm(
                va + embedder.shape_vec(rem)) - 1.0)
    tilt, cost = float(np.mean(tilts)), float(np.mean(costs))
    c2 = []
    for base, sfx, w, rem in transform.pairs[:200]:
        s = embedder.shape_vec(embedder.corpus[base]) + \
            (embedder.shape_vec(rem) if rem else 0)
        c2.append(float((s / np.linalg.norm(s))
                        @ embedder.shape_vec(embedder.corpus[w])))
    c3 = []
    for p, base, sfx, w, pw, full, rem in triples:
        pph = embedder.corpus[pw][:len(embedder.corpus[pw])
                                  - len(embedder.corpus[base])]
        parts = embedder.shape_vec(pph) + \
            embedder.shape_vec(embedder.corpus[base]) + \
            (embedder.shape_vec(rem) if rem else 0)
        c3.append(float((parts / np.linalg.norm(parts))
                        @ embedder.shape_vec(embedder.corpus[full])))
    m2, m3 = float(np.mean(c2)), float(np.mean(c3))
    print(f"\ntilt {tilt:.1f}°  cost {cost:.3f} "
          f"(floor {np.sqrt(2) - 1:.3f})  dilution 2-morph {m2:.3f} "
          f"< 3-morph {m3:.3f}")
    assert abs(tilt - 22.5) <= 3.0, \
        f"tilt {tilt:.1f}° left its band — the shape space's mass " \
        f"balance moved"
    assert abs(cost - 0.535) <= 0.03, \
        f"junction cost {cost:.3f} left its band"
    assert cost > np.sqrt(2) - 1
    assert m3 > m2, \
        "THE DILUTION LAW inverted — curvature stopped scaling as " \
        "junctions/mass"


def test_mass_exposed_and_unused(embedder):
    """The radius accessor exists (doctrine) and no organ consults it
    (non-goal, standing) — the assertion is the module docstring plus
    this smoke: mass is additive where the cone is faithful."""
    pron = embedder.corpus["understanding"]
    assert mass(pron) == sum(counts_of(pron).values())
    a, b = embedder.corpus["under"], embedder.corpus["standing"]
    assert mass(list(a) + list(b)) == mass(a) + mass(b) + 1
