"""
elfix/emergent/emergent_unit.py  —  Tier 3: self-forming higher units
=======================================================================
THE NEW RUNG. The heart of the system, and the only piece whose central claim
is unproven. It carries a MANDATORY falsification gate (see scripts/milestone1).

PROVENANCE
----------
- Promotion machinery (candidate -> confirmed, confidence-gated): [GCL]
  malleable_library (malleable->confirmed tiers).
- Ternary evidence + centre/width honesty: [ElfIX] ternary_valence (why_piece6)
  and relational (why_piece15) — "never a centre without its width".
- Boundary cues (sonority minima, coda reversal): Tier 2 trajectory.
- The clustering itself: [NEW->original]. Units emerge where sub-trajectories
  cluster in the READABLE feature manifold. Nearest established cousins, cited
  as scaffolding not authority:
    * Kohonen (1982), Self-Organizing Maps — topology-preserving feature maps
    * agglomerative clustering
    * CONTRAST baseline: Byte-Pair Encoding — Sennrich et al. (2016), Kudo
      (2018) — which merge units by ORTHOGRAPHIC FREQUENCY. ElfIX merges by
      GEOMETRIC COHERENCE of sound trajectories instead. That is the novelty.

DESIGN LAW CHECK
----------------
Law 6 (readable AND self-forming, no gradient black box): the groupings are
GIVEN by the data's geometry (quantized arc descriptors), not learned by an
optimiser. Every emergent unit has a describable shape.
Law 1 (earned geometry): the tightness/quantization is read from the data
distribution (see `auto_quantum`), never a magic constant.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Iterable
from collections import defaultdict
from ..trajectory.trajectory import Trajectory
from ..sonority import sonority_phonotactic


# ── Arc extraction: a sonority arc is the span around one peak ────────────────
def arcs(traj: Trajectory) -> List[Tuple[int, int]]:
    """
    Split a trajectory into sonority arcs at its minima. Each arc is a
    (start, end) half-open index span containing exactly one peak. Arcs are the
    syllable-sized chunks the geometry proposes on its own.
    """
    seams = traj.minima()
    bounds = [0] + [s + 1 for s in seams] + [len(traj)]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
            if bounds[i] < bounds[i + 1]]


def geometry_boundaries(symbols: List[str]) -> List[int]:
    """
    The seams the SOUND proposes for a word, earned from its contour:
      (1) sonority minima between peaks   -> syllable seams
      (2) coda sonority reversals         -> appendix / suffix seams
    Returns sorted unique interior boundary indices (0 < b < len).

    This is what the falsification gate scores against held-out morpheme
    boundaries, versus a frequency (BPE) baseline.
    """
    t = Trajectory.of(symbols)
    bs = set(s + 1 for s in t.minima()) | set(t.coda_reversals())
    return sorted(b for b in bs if 0 < b < len(t))


def syllable_boundaries(symbols: List[str]) -> List[int]:
    """
    The geometry's NATIVE syllabifier: maximal-onset syllable seams, the boundary
    placed AT each interior sonority minimum (the trough consonant joins the
    following syllable's onset). This differs from `geometry_boundaries` only by
    the intervocalic-consonant convention:

      morpheme/coda (geometry_boundaries):  min + 1   ->  run | ing  ,  + coda seams
      syllable/onset (this fn, Maximal Onset):  min   ->  ru  | ning

    Maximal-onset syllabification (Kahn 1976, Selkirk 1982) and morphological
    segmentation systematically disagree by exactly this offset; the same sonority
    contour yields both. No coda-reversal appendix seams: those are a morpheme
    cue, not a syllable cue.

    The contour here uses the EARNED PHONOTACTIC sonority (sonority.py), not the
    phonetic scale the morpheme path uses — the two are kept apart on purpose
    (dual scale). On the corpus-earned Maximal-Onset gold this scores F1 ~0.93 vs
    BPE ~0.40 (scripts/syllable_eval) — the geometry's strongest evidence so far.
    """
    t = Trajectory.of(symbols, son=sonority_phonotactic)
    n = len(t)
    return sorted(b for b in set(t.minima()) if 0 < b < n)


def geometry_boundaries_emergent(symbols: List[str],
                                 inventory: Dict[Tuple, "EmergentUnit"],
                                 quanta: Tuple[float, float],
                                 both_sides: bool = False) -> List[int]:
    """
    Boundaries that PREFER cutting where a high-frequency emergent unit ends.

    This is the Tier 3 thesis under test (spec Piece 3, Law 6): self-forming
    RECURRING units refine the seams, not contour cues acting alone.

    The candidate seams are the same the contour proposes (`geometry_boundaries`),
    but a sonority-minimum seam is kept only when the recurring arc-shape it
    delimits is a CONFIRMED emergent unit — present in `inventory`, i.e. its
    descriptor recurred >= min_count across the corpus (`discover`). Coda
    reversals (the suffix/appendix seams) are kept unconditionally: the appendix
    IS the morpheme cue, and a one-phoneme appendix is not a peak-centred arc.

    Because `arcs()` partitions a word at exactly the minima `geometry_boundaries`
    uses, the result is always a SUBSET of `geometry_boundaries` — a refinement.
    Emergent evidence can WITHHOLD a contour seam (drop over-segmentation), never
    invent one the contour didn't already propose. With an empty inventory it
    returns exactly `geometry_boundaries` (the honest degenerate case).

    `quanta` MUST match the widths used to build `inventory`, or descriptors
    won't align. `both_sides=False` (default) keeps a seam if EITHER flanking arc
    is confirmed (gentle filter); True requires BOTH (aggressive).
    """
    t = Trajectory.of(symbols)
    n = len(t)
    bs = set(b for b in t.coda_reversals() if 0 < b < n)
    confirmed = (lambda span: describe(t, span, quanta) in inventory) \
        if inventory else (lambda span: True)
    for left, right in zip(arcs(t), arcs(t)[1:]):
        seam = left[1]                      # == right[0]: the interior boundary
        if not (0 < seam < n):
            continue
        keep = (confirmed(left) and confirmed(right)) if both_sides \
            else (confirmed(left) or confirmed(right))
        if keep:
            bs.add(seam)
    return sorted(bs)


# ── Arc descriptor: the readable 'shape' of an arc (its cluster key) ──────────
def describe(traj: Trajectory, span: Tuple[int, int],
             quanta: Tuple[float, float]) -> Tuple:
    """
    A small, readable descriptor of an arc's SHAPE. Two arcs with the same
    descriptor are 'the same emergent unit'. Every field is human-describable:
      (length, start_sonority, peak_sonority, end_sonority, q_place, q_manner)
    `quanta` is the PER-AXIS earned bin width (place_q, manner_q): place and
    manner have different natural spreads (~0.111 vs ~0.222), so each axis gets
    its own width (Law 1). Required, from auto_quanta(); never set by hand.
    """
    a, b = span
    con = traj.contour[a:b]
    pts = traj.points[a:b]
    if not con or not pts:
        return ()
    n = len(con)
    place_q, manner_q = quanta
    place_mean = sum(p[2] for p in pts) / n
    manner_mean = sum(p[3] for p in pts) / n
    return (n, round(con[0]), round(max(con)), round(con[-1]),
            round(place_mean / place_q), round(manner_mean / manner_q))


def auto_quantum(traj_iter: Iterable[Trajectory], axis: int = 2) -> float:
    """
    Earn the quantization width for one `axis` from the data (Law 1): 1.4826 * MAD
    of arc means (MAD-as-std estimate). NO floor and NO sample cap — the width IS
    the measured spread, not a clamped magic number. axis 2 = place, axis 3 =
    manner. (The prior `max(0.15, ...)` floor was binding and masked the earned
    place width ~0.111 — removed in task 3.)
    """
    vals = []
    for t in traj_iter:
        for a, b in arcs(t):
            pts = t.points[a:b]
            if pts:
                vals.append(sum(p[axis] for p in pts) / len(pts))
    if not vals:
        return 0.2           # only reached on an empty corpus (no arcs to bin)
    vals.sort()
    med = vals[len(vals) // 2]
    dev = sorted(abs(v - med) for v in vals)
    mad = dev[len(dev) // 2]
    if mad == 0:
        return 0.2           # no spread at all (degenerate); value is irrelevant
    return round(1.4826 * mad, 3)


def auto_quanta(traj_iter: Iterable[Trajectory]) -> Tuple[float, float]:
    """
    Earn the PER-AXIS bin widths (place_q, manner_q) for describe(). Place (axis 2)
    and manner (axis 3) have different natural spreads (~0.111 vs ~0.222 on the
    full corpus), so each earns its own width rather than sharing one — retiring
    the single-quantum approximation flagged in task 3. Pass a re-iterable.
    """
    trajs = list(traj_iter)
    return (auto_quantum(trajs, 2), auto_quantum(trajs, 3))


# ── The emergent inventory: cluster arcs across a corpus ──────────────────────
@dataclass
class EmergentUnit:
    descriptor: Tuple
    count: int                 # attestation (ternary: >0 attested)
    centroid: List[float]      # centre  (Law 4: never a centre ...)
    spread: float              # width   (... without its width)
    example: List[str]         # a representative phoneme span


def discover(corpus: List[List[str]], quanta: Tuple[float, float] = None,
             min_count: int = 3) -> Dict[Tuple, EmergentUnit]:
    """
    Build the emergent unit inventory from a corpus of phoneme sequences.
    An arc-shape that recurs >= min_count times is a confirmed emergent unit
    (the malleable->confirmed promotion, [GCL] malleable_library). Each unit
    reports centre + spread (Law 4) and is attested by count (ternary +1).

    Returns {descriptor: EmergentUnit}. Fast: O(total arcs), hashing only —
    no pairwise distance, no gradients (Law 6).
    """
    trajs = [Trajectory.of(w) for w in corpus]
    if quanta is None:
        quanta = auto_quanta(trajs)

    buckets: Dict[Tuple, list] = defaultdict(list)   # descriptor -> [centroids]
    examples: Dict[Tuple, List[str]] = {}
    for t in trajs:
        for a, b in arcs(t):
            d = describe(t, (a, b), quanta)
            if not d:
                continue
            pts = t.points[a:b]
            cen = [sum(p[k] for p in pts) / len(pts) for k in range(len(pts[0]))]
            buckets[d].append(cen)
            examples.setdefault(d, t.symbols[a:b])

    inv: Dict[Tuple, EmergentUnit] = {}
    for d, cens in buckets.items():
        if len(cens) < min_count:
            continue                      # absence != zero: unseen-enough stays absent
        dim = len(cens[0])
        centroid = [sum(c[k] for c in cens) / len(cens) for k in range(dim)]
        # spread = mean L2 distance of members to centroid (the honest width)
        spread = sum(
            (sum((c[k] - centroid[k]) ** 2 for k in range(dim)) ** 0.5)
            for c in cens
        ) / len(cens)
        inv[d] = EmergentUnit(d, len(cens), centroid, round(spread, 4),
                              examples[d])
    return inv


if __name__ == "__main__":
    print("plant boundaries:", geometry_boundaries(["p", "l", "AE", "n", "t"]))
    print("cats  boundaries:", geometry_boundaries(["k", "AE", "t", "s"]))
    print("running boundaries:",
          geometry_boundaries(["r", "AH", "n", "IH", "NG"]))
