"""E-3: the tower (probe 50) — doctrine with numbers.

Four floors, each a projection that forgets one thing:

  SEQUENCE  the phoneme string itself — nothing forgotten; the exact
            gate lives here.
  CONE      raw integer counts (unigrams + bigrams) — ORDER forgotten
            beyond adjacency; addition is EXACT here: the decoder
            lives on this floor, and the cone identity below is an
            integer equality, not a similarity.
  SPHERE    unit-normalized counts — MAGNITUDE forgotten; cosine
            country; the proposer lives here, and every curvature
            phenomenon (tilt, junction cost, dilution) is the price of
            the normalization.
  ANGLE     thresholded consonance — DIRECTION alone.

"Exactness beats similarity" restated as geometry: work as high up the
tower as the artifacts allow. The system already staffs the floors —
gate at sequence, decoder at cone, proposer at sphere — and this
module simply exposes the cone beside the sphere: `counts_of` (raw
integer counts, the flat floor) and `mass` (the L1 radius the sphere
throws away; exposed, deliberately unused — the radius channel is a
standing non-goal, noted so nobody 'discovers' it by accident).

The measured doctrine (recorded in the battery): the real base->derived
tilt is ~22.5 degrees against the 45-degree orthogonal ideal (the
base's mass leans the ray); the per-junction charge ||a+b|| - 1 runs
~0.535 over the ad-quadratum floor sqrt(2) - 1 = 0.414; and the
DILUTION LAW — relative curvature goes as junctions/mass, so the
3-morpheme SUM-cosine EXCEEDS the 2-morpheme one: the sphere flattens
as words grow, and the seam matters most for short words.
"""
from collections import defaultdict

from .embed import shape


def counts_of(phones):
    """The cone floor: raw INTEGER shape counts (unigram + bigram),
    as a dict keyed ('u', shape) / ('b', shape, shape). Addition on
    this floor is exact; nothing is normalized away."""
    c = defaultdict(int)
    ss = [shape(p) for p in phones]
    for s in ss:
        c[("u", s)] += 1
    for a, b in zip(ss, ss[1:]):
        c[("b", a, b)] += 1
    return dict(c)


def add_counts(*counts):
    out = defaultdict(int)
    for c in counts:
        for k, n in c.items():
            out[k] += n
    return dict(out)


def junction_bigram(left_phone, right_phone):
    """The seam's cone contribution: one bigram count at the join."""
    return {("b", shape(left_phone), shape(right_phone)): 1}


def cone_identity(prefix_pron, base_pron, remainder):
    """The cone is flat: counts(p+b+s) == counts(p) + counts(b) +
    counts(s) + the junction bigrams — EXACT integer equality for any
    phonologically faithful concatenation. Returns (lhs, rhs) dicts
    for the caller to compare."""
    full = list(prefix_pron) + list(base_pron) + list(remainder)
    lhs = counts_of(full)
    joins = [junction_bigram(prefix_pron[-1], base_pron[0])]
    if remainder:
        joins.append(junction_bigram(base_pron[-1], remainder[0]))
    rhs = add_counts(counts_of(prefix_pron), counts_of(base_pron),
                     counts_of(remainder), *joins)
    return lhs, rhs


def mass(phones):
    """The radius the sphere forgets: total count mass (L1). Exposed
    for the doctrine, DELIBERATELY UNUSED by any organ — the radius
    channel is a standing non-goal."""
    return sum(counts_of(phones).values())
