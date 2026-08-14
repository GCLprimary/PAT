"""V-1: the discourse stage (probe 31b) — maintained topic state with the
dual-threshold policy.

CONSONANCE != COMMITMENT (law 2). Integration is generous: anything
within theta_c of the current state blends in. Page-turns are strict and
deliberate: a LONE dissonant sentence never turns the page — it is HELD
as pending (an interruption, until proven otherwise). Only a second
dissonant that is mutually consonant with the pending one (>= theta_a)
earns a deliberate turn, onto their blend. One threshold doing both jobs
was the measured failure mode: single-theta v1 recalled 18% at
interrupters where DUAL holds 71%.

Reference numbers (interruption battery): at-interrupt 71% (memoryless
1%), in-seg 99%, post 94%, overall 83% vs v1 69%; cost = seg-start 64%
(the deliberate-turn lag tax — commitment takes one extra sentence).

LAW-1 SCOPE NOTE (measured, flagged in HANDOFF): the stage's consonance
cosines are RAW — the theta defaults were calibrated on raw sentence-
centroid cosines (probe 31b), and running the stage on centered vectors
inverts the battery (overall 89% raw -> 43% centered: every sentence
reads dissonant at theta_c = 0.45). Law 1's centering governs region
NAVIGATION (midpoints, waypoints, steering); the stage's sentence-to-
state consonance lives at a different cosine scale. The stage therefore
takes any object with a .region(words) method; the battery uses the raw
space in mirror.stage.RawTopicSpace.
"""
from dataclasses import dataclass

import numpy as np

# Defaults promoted by the pinned-battery sweep on the probe-machine
# corpora (owner-ruled "ship whatever the inequality supports"): lowering
# theta_c 0.45 -> 0.35 recovers in-seg to 100% (fewer false holds) and
# lifts overall to 88.7% >= v1's 87.5%, with at-interrupt flat at 83.3%.
# The plateau is robust (identical across theta_a 0.55-0.85); the
# seg-start lag tax (58.3%) is structural, not threshold-tunable. The
# spec's original probe-31b defaults were (0.45, 0.65).
THETA_C = 0.35      # consonance: generous integration
THETA_A = 0.55      # commitment: strict, mutually-consonant page-turn
BLEND = 0.5


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class RawTopicSpace:
    """Normalized raw centroids — the space the stage's thetas were
    calibrated on (probe 31b). Not for region navigation (law 1)."""

    def __init__(self, geometry, stop=None):
        self.geometry = geometry
        self.stop = set(stop) if stop else set()

    def region(self, words):
        vs = [self.geometry.vec(w) for w in words
              if w in self.geometry and w not in self.stop]
        if not vs:
            return None
        return _unit(np.mean(vs, axis=0))


@dataclass
class Observation:
    state: np.ndarray | None
    turned: bool
    held: bool


class DiscourseStage:
    """Maintained topic state over a stream of sentence vectors."""

    def __init__(self, space, theta_c=THETA_C, theta_a=THETA_A, blend=BLEND):
        self.space = space          # CenteredSpace (law 1)
        self.theta_c = theta_c
        self.theta_a = theta_a
        self.blend = blend
        self.state = None
        self.pending = None

    def reset(self):
        self.state = None
        self.pending = None

    def observe(self, sentence_or_vec):
        """One sentence in. Returns Observation(state, turned, held).

        turned: a deliberate page-turn happened on this sentence.
        held:   this sentence was dissonant and is being held pending.
        """
        if isinstance(sentence_or_vec, (list, tuple)):
            v = self.space.region(sentence_or_vec)
        else:
            v = np.asarray(sentence_or_vec, dtype=float)
        if v is None:
            return Observation(self.state, False, False)

        if self.state is None:
            self.state = v
            self.pending = None
            return Observation(self.state, False, False)

        if float(self.state @ v) >= self.theta_c:
            self.state = _unit(self.blend * self.state +
                               (1.0 - self.blend) * v)
            self.pending = None
            return Observation(self.state, False, False)

        if self.pending is not None and \
                float(self.pending @ v) >= self.theta_a:
            self.state = _unit(self.pending + v)     # deliberate turn
            self.pending = None
            return Observation(self.state, True, False)

        self.pending = v                              # lone dissonant: HOLD
        return Observation(self.state, False, True)


class SingleThetaStage:
    """The v1 policy, kept as the comparison run (probe 30B): one
    threshold does both jobs — and fails the interruption battery."""

    def __init__(self, space, theta=THETA_A, blend=BLEND):
        self.space = space
        self.theta = theta
        self.blend = blend
        self.state = None

    def reset(self):
        self.state = None

    def observe(self, sentence_or_vec):
        if isinstance(sentence_or_vec, (list, tuple)):
            v = self.space.region(sentence_or_vec)
        else:
            v = np.asarray(sentence_or_vec, dtype=float)
        if v is None:
            return Observation(self.state, False, False)
        if self.state is None or float(self.state @ v) < self.theta:
            turned = self.state is not None
            self.state = v
            return Observation(self.state, turned, False)
        self.state = _unit(self.blend * self.state + (1.0 - self.blend) * v)
        return Observation(self.state, False, False)
