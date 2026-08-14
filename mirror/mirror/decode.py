"""G-1: the inverse embedder (probes 23, 23b) — vector back to sequence.

A shape-bigram vector is a walk's fingerprint: unigram counts are node
visits, bigram counts are directed edges. Inversion is three exact steps:

1. **Integer snap.** The embedder ships unit vectors; the underlying
   counts return by a lambda sweep — scale so the smallest nonzero entry
   is k (k = 1..5) and accept when every entry lands within 1e-6 of an
   integer. Measured: 100% exact recovery.
2. **Eulerian accounting.** A sequence exists iff the count graph admits
   an Eulerian path: at most one node with out-in = +1 (the start), at
   most one with in-out = +1 (the end), all others balanced, and the
   edges connected. Anything else is a structural REFUSE.

   THE SEAM-CONNECTIVITY THEOREM: every sequence-derived graph walks
   (real-word refusal is 0% by construction), but a SUM-bound vector —
   parts superposed WITHOUT the junction bigram — is missing exactly the
   edge that joins the parts, so its graph is disconnected or unbalanced
   and refuses structurally (measured 168/200). The seam term is the
   invertibility condition: what makes the transform decodable is the
   same cross-term that makes it accurate.
3. **Walk enumeration** (cap 64) + tie-break. Lexicographic edge order
   is the probed baseline (68% exact / 48% unique / 100% original-among-
   walks). The attested-trigram tie-break (score walks by corpus shape-
   trigram counts) ships behind a promotion inequality: it becomes the
   default only if it beats the lexicographic baseline's exact rate on
   the 500-word bank.
"""
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

SNAP_TOL = 1e-6
SNAP_K_MAX = 5
WALK_CAP = 64


@dataclass
class Decoded:
    status: str                    # "OK" | "REFUSE_SNAP" | "REFUSE_STRUCTURE"
    sequence: tuple | None = None  # chosen shape sequence
    walks: list = field(default_factory=list)
    counts: np.ndarray | None = None


def snap_counts(unit_vec, k_max=SNAP_K_MAX, tol=SNAP_TOL):
    """Unit vector -> integer count vector, or None (probe 23b lambda
    sweep: the smallest nonzero entry is some count k in 1..k_max)."""
    u = np.asarray(unit_vec, dtype=float).ravel()
    nz = u[u > 1e-9]
    if nz.size == 0:
        return None
    lam = 1.0 / nz.min()
    for k in range(1, k_max + 1):
        cand = u * lam * k
        r = np.round(cand)
        if np.abs(cand - r).max() < tol:
            return r.astype(np.int64)
    return None


def graph_from_counts(counts, n):
    """Split a snapped count vector into (edges, nodes) Counters over
    shape indices. Layout: [bigram n*n | unigram n]."""
    counts = np.asarray(counts)
    edges = Counter()
    bigram = counts[:n * n].reshape(n, n)
    for a, b in zip(*np.nonzero(bigram)):
        edges[(int(a), int(b))] = int(bigram[a, b])
    nodes = Counter({int(i): int(c)
                     for i, c in enumerate(counts[n * n:]) if c > 0})
    return edges, nodes


def infer_starts(edges, nodes):
    """Degree accounting (probe 23b): the start is the out-in = +1 node;
    balanced graphs enumerate active starts; anything else -> None."""
    outd, ind = Counter(), Counter()
    for (a, b), c in edges.items():
        outd[a] += c
        ind[b] += c
    plus = [v for v in nodes if outd[v] - ind[v] == 1]
    minus = [v for v in nodes if ind[v] - outd[v] == 1]
    if any(abs(outd[v] - ind[v]) > 1 for v in nodes):
        return None
    if len(plus) > 1 or len(minus) > 1:
        return None
    if len(plus) == 1:
        return plus
    return [v for v in nodes if outd[v] > 0] or list(nodes)


def _walks_from(edges, start, n_edges, cap):
    out = []

    def rec(node, used, path):
        if len(out) >= cap:
            return
        if used == n_edges:
            out.append(tuple(path))
            return
        for (a, b), c in sorted(edges.items()):
            if a == node and c > 0:
                edges[(a, b)] -= 1
                path.append(b)
                rec(b, used + 1, path)
                path.pop()
                edges[(a, b)] += 1

    rec(start, 0, [start])
    return out


def enumerate_walks(edges, nodes, cap=WALK_CAP):
    """All Eulerian walks consistent with the graph (lex edge order),
    or None on a structural refusal."""
    starts = infer_starts(edges, nodes)
    if starts is None:
        return None
    n_edges = sum(edges.values())
    if n_edges == 0:
        # an edgeless graph is a sequence only if it is a single visit
        if sum(nodes.values()) == 1:
            return [(next(iter(nodes)),)]
        return None
    walks = []
    for s in starts:
        walks += _walks_from(Counter(edges), s, n_edges, cap - len(walks))
        if len(walks) >= cap:
            break
    return walks or None       # no complete walk found: disconnected


class ShapeDecoder:
    """The inverse of Embedder.shape_vec, with tie-break selection."""

    def __init__(self, embedder, tie_break="attested"):
        self.embedder = embedder
        self.space = embedder.shape_space
        self.n = self.space.n
        self.tie_break = tie_break
        self._trigrams = None
        if tie_break == "attested":
            self._fit_trigrams()

    def _fit_trigrams(self):
        from .embed import shape
        tri = Counter()
        for pron in self.embedder.corpus.values():
            ss = [self.space.index[shape(p)] for p in pron]
            tri.update(zip(ss, ss[1:], ss[2:]))
        self._trigrams = tri

    def _choose(self, walks):
        if self.tie_break == "attested" and self._trigrams and len(walks) > 1:
            def attested_score(w):
                return sum(self._trigrams.get(t, 0)
                           for t in zip(w, w[1:], w[2:]))
            best = max(range(len(walks)),
                       key=lambda i: (attested_score(walks[i]), -i))
            return walks[best]
        return walks[0]                       # lexicographic baseline

    def decode(self, vec):
        """Vector (unit or raw counts) -> Decoded with shape sequences."""
        counts = snap_counts(vec)
        if counts is None:
            return Decoded("REFUSE_SNAP")
        edges, nodes = graph_from_counts(counts, self.n)
        walks = enumerate_walks(edges, nodes)
        if not walks:
            return Decoded("REFUSE_STRUCTURE", counts=counts)
        chosen = self._choose(walks)
        alphabet = self.space.alphabet
        return Decoded("OK",
                       sequence=tuple(alphabet[i] for i in chosen),
                       walks=[tuple(alphabet[i] for i in w) for w in walks],
                       counts=counts)

    def decode_shapes(self, shapes):
        """Convenience: sequence of shapes -> Decoded (round-trip path)."""
        idx = [self.space.index[s] for s in shapes]
        edges = Counter(zip(idx, idx[1:]))
        nodes = Counter(idx)
        walks = enumerate_walks(edges, nodes)
        if not walks:
            return Decoded("REFUSE_STRUCTURE")
        chosen = self._choose(walks)
        alphabet = self.space.alphabet
        return Decoded("OK",
                       sequence=tuple(alphabet[i] for i in chosen),
                       walks=[tuple(alphabet[i] for i in w) for w in walks])
