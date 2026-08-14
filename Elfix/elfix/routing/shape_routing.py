"""
elfix/routing/shape_routing.py  —  Tier 6: shape selects the operation
========================================================================
PROVENANCE
----------
- [GCL] geometric_ops (triangle->filter, pentagon->accumulate, hexagon->compare)
  — the one genuinely novel idea salvaged from GCL.
- Canonical cousin: [NEW->established] conditional computation / Mixture-of-
  Experts ROUTING — Jacobs et al. (1991), Shazeer et al. (2017). ElfIX's gate
  is a READABLE geometric predicate on the trajectory, not a learned router.

DESIGN DECISION: the operation set is DISCOVERED, not declared. We do NOT
hand-assign triangle->filter. The routing classes are the arc-shapes that EARNED
their existence by recurring (>= min_count, the same promotion as Tier 3's
discover()) — NOT a magic top-k. A non-recurring arc routes to NOVEL (-1), the
same novelty Tier 7 reads as low recognition: routing and readout agree on what
is new.

What each class is, and where it tends to sit in a word, are EARNED and readable
(class_shape, class_position). And the OPERATION each class performs is now EARNED
too (spec Piece 6's open question, RESOLVED): `learn_ops` reads it off real
running-text behaviour — H(next | class). A class that predicts its continuation
ACCUMULATES (carries context forward); one whose continuation is as uncertain as
the global baseline is a BOUNDARY (reset). The two-regime split is DISCOVERED by
2-means on the entropy, not declared. Falsification (scripts/routing_ops.py): the
earned dispositions align with REAL structure — boundary-op classes are word-final,
accumulate-op classes word-internal (corr ~0.81). The op SET is discovered; the op
SEMANTICS are now read off the data, exactly as the spec said they would be once a
downstream task existed.

DESIGN LAW CHECK
----------------
Law 1: the class inventory is earned by recurrence (min_count), no magic top-k;
the op split is earned by 2-means on measured entropy, no magic threshold.
Law 6: every routing class is a readable arc shape; route() and class_op() are
lookups you can recompute by hand.
"""

from __future__ import annotations
import math
from collections import Counter
from typing import List, Dict, Tuple
from ..trajectory.trajectory import Trajectory
from ..emergent.emergent_unit import arcs, describe, auto_quanta

# word-position labels for an arc within its word (the discovered routing signal)
_POSITIONS = ("sole", "initial", "medial", "final")


def _position(i: int, n_arcs: int) -> str:
    if n_arcs == 1:
        return "sole"
    if i == 0:
        return "initial"
    return "final" if i == n_arcs - 1 else "medial"


def _entropy(cnt: Counter) -> float:
    """Shannon entropy (bits) of a count distribution."""
    tot = sum(cnt.values()) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in cnt.values() if v)


def _two_means(vals: List[float], iters: int = 30) -> float:
    """1-D 2-means split point — DISCOVERS the boundary between two regimes in a
    list of values (here: per-class next-entropy), rather than declaring one."""
    if len(vals) < 2:
        return vals[0] if vals else 0.0
    lo, hi = min(vals), max(vals)
    for _ in range(iters):
        mid = (lo + hi) / 2
        left = [v for v in vals if v < mid]
        right = [v for v in vals if v >= mid]
        if not left or not right:
            break
        nlo, nhi = sum(left) / len(left), sum(right) / len(right)
        if abs(nlo - lo) < 1e-9 and abs(nhi - hi) < 1e-9:
            break
        lo, hi = nlo, nhi
    return (lo + hi) / 2


class ShapeRouter:
    """Routes each arc to a discovered, recurring shape-class (Tier 6)."""

    def __init__(self, corpus_trajs: List[Trajectory], min_count: int = 3):
        self.quanta = auto_quanta(corpus_trajs)
        # count each arc-shape, and tally where in the word it tends to occur
        counts: Counter = Counter()
        pos: Dict[Tuple, Counter] = {}
        for t in corpus_trajs:
            spans = arcs(t)
            for i, span in enumerate(spans):
                d = describe(t, span, self.quanta)
                if not d:
                    continue
                counts[d] += 1
                pos.setdefault(d, Counter())[_position(i, len(spans))] += 1
        # EARNED classes: shapes that recur >= min_count (absence != zero), by count
        self.classes: List[Tuple] = [d for d, k in counts.most_common() if k >= min_count]
        self.counts: Dict[Tuple, int] = {d: counts[d] for d in self.classes}
        self.positions: Dict[Tuple, Counter] = {d: pos[d] for d in self.classes}
        self.index: Dict[Tuple, int] = {d: i for i, d in enumerate(self.classes)}
        # Operation semantics: EARNED from running-text behaviour via learn_ops()
        # (spec Piece 6 — discovered, not declared). Empty until then.
        self.disposition: Dict[int, str] = {}      # class id -> 'accumulate' | 'boundary'
        self.predictiveness: Dict[int, float] = {}  # class id -> info gain about next, [0,1]
        self.op_threshold: float = 0.0
        self.next_baseline: float = 0.0

    def route(self, traj: Trajectory) -> List[int]:
        """Routed class id for each arc; -1 = NOVEL (non-recurring) shape."""
        return [self.index.get(describe(traj, span, self.quanta), -1)
                for span in arcs(traj)]

    def learn_ops(self, arc_streams: List[List[int]], min_obs: int = 50) -> Dict[int, str]:
        """
        EARN each class's OPERATION from running-text behaviour (spec Piece 6:
        discovered, not declared). For each class, measure the entropy of what
        FOLLOWS it, H(next | class), over the arc streams. A class that PREDICTS
        its continuation (low entropy) carries context forward -> ACCUMULATE; one
        whose continuation is as uncertain as the global baseline (high entropy)
        is a BOUNDARY -> reset. The two regimes are DISCOVERED by a 2-means split
        on the entropy, not declared. Sets `disposition` and `predictiveness`.
        """
        nxt: Dict[int, Counter] = {}
        allnext: Counter = Counter()
        for s in arc_streams:
            for a, b in zip(s, s[1:]):
                nxt.setdefault(a, Counter())[b] += 1
                allnext[b] += 1
        base = _entropy(allnext)
        nh = {c: _entropy(cnt) for c, cnt in nxt.items()
              if sum(cnt.values()) >= min_obs}
        if not nh:
            return {}
        thr = _two_means(list(nh.values()))
        self.next_baseline = base
        self.op_threshold = thr
        self.predictiveness = {c: max(0.0, (base - h) / base) if base else 0.0
                               for c, h in nh.items()}
        self.disposition = {c: ("accumulate" if h < thr else "boundary")
                            for c, h in nh.items()}
        return self.disposition

    def class_op(self, class_id: int) -> str:
        """The earned operation of a class: 'accumulate' / 'boundary' / 'unknown'
        (too few observations, or learn_ops not run)."""
        return self.disposition.get(class_id, "unknown")

    def class_shape(self, class_id: int) -> str:
        """Readable arc shape of a routing class (Law 6)."""
        if not (0 <= class_id < len(self.classes)):
            return "novel"
        n, s0, sp, s1, qp, qm = self.classes[class_id]
        d = self.classes[class_id]
        return (f"len {n}, sonority {s0}->{sp}->{s1}, place~{qp}, manner~{qm} "
                f"(recurs {self.counts[d]}x)")

    def class_position(self, class_id: int) -> str:
        """Where in the word this class tends to sit — the discovered routing
        signal a future op-map can read (initial/medial/final/sole)."""
        if not (0 <= class_id < len(self.classes)):
            return "novel"
        tally = self.positions[self.classes[class_id]]
        total = sum(tally.values()) or 1
        top, n = tally.most_common(1)[0]
        return f"{top} ({n / total:.0%})"
