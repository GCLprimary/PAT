"""V-2: centered region navigation (probes 29, 30A) — and law 1.

CENTER BEFORE MEASURING. Dense meaning space has a global component —
every vector leans toward the corpus mean, so raw cosines to averaged
targets are inflated by hubness, not meaning. Three probes were fooled
by this before it became law. All region/topic similarity in workshop
code goes through this module's centered vectors; raw cosines to
averaged targets are forbidden.

A region is a centered centroid; `between(vA, vB)` is the normalized
centered midpoint — the geometry's own answer to "what lies between two
topics" (probe 30A: two endpoints constrain the middle REGION).

THE CLOSED NEGATIVE (probe 29, kept as evidence): word-level path
completion over graph media — diffusion or shortest-path over meaning-kNN
or attestation graphs — LOSES to this space's own midpoint geometry
(best field 0.054 vs midpoint 0.067 recall@10). Do not rebuild graph
diffusion here; the dense space already knows what lies between.
"""
import numpy as np


class CenteredSpace:
    """The centering helper: the geometry's global component, removed.

    The canonical workshop centering is FREQUENCY-WEIGHTED (pass the
    pinned corpus's unigram counts as `weights`): the global component
    is what the corpus on average points at, not the unweighted vocab
    mean. Measured: the weighted center collapses the journey controls
    onto their probe bands (unsteered ~+0.04) where the unweighted mean
    leaves a ~+0.2 shared-component offset inflating every cosine.
    """

    def __init__(self, geometry, stop=None, weights=None):
        self.geometry = geometry
        self.stop = set(stop) if stop else set()
        vecs = np.stack([geometry.vec(w) for w in geometry.vocab])
        if weights is None:
            self.center = vecs.mean(axis=0)
        else:
            w = np.array([float(weights.get(x, 0))
                          for x in geometry.vocab])
            self.center = (vecs * (w / w.sum())[:, None]).sum(axis=0)

    def centered(self, v):
        """Raw vector -> unit centered vector."""
        c = np.asarray(v, dtype=float) - self.center
        n = np.linalg.norm(c)
        return c / n if n > 0 else c

    def word(self, w):
        return self.centered(self.geometry.vec(w))

    def cos(self, u, v):
        """Centered cosine of two RAW vectors (the only similarity
        workshop code is allowed to take against averaged targets)."""
        return float(self.centered(u) @ self.centered(v))

    def region(self, words):
        """Centered centroid of a bag of words (content words only when
        a stop list was provided). None if nothing lands in the space."""
        vs = [self.geometry.vec(w) for w in words
              if w in self.geometry and w not in self.stop]
        if not vs:
            return None
        return self.centered(np.mean(vs, axis=0))

    def between(self, v_a, v_b):
        """The normalized centered midpoint of two RAW vectors."""
        m = self.centered(v_a) + self.centered(v_b)
        n = np.linalg.norm(m)
        return m / n if n > 0 else m

    def waypoint(self, v_a, v_b, t):
        """Centered-normalized interpolation (1-t)*vA + t*vB (V-3)."""
        m = (1.0 - t) * self.centered(v_a) + t * self.centered(v_b)
        n = np.linalg.norm(m)
        return m / n if n > 0 else m
