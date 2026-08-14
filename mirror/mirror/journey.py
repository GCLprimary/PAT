"""V-3: topic-to-topic generation (probe 32b) — itinerary-steered journeys.

THE CORRIDOR IS SET AT PROPOSAL TIME (law 3). Steering biases the
proposal pool itself: each beam step takes the trigram top-10 (bigram
top-6 backoff), reranks it by centered cosine to the current waypoint
plus a small attestation bonus (0.05·log1p(count)), and keeps the top 4.
Audit-only steering — same pool, steering applied only at leg selection —
is 2–3x weaker (measured +0.184 end-closure vs +0.295). The audit
disposes only among what was proposed.

CENTER BEFORE MEASURING (law 1): waypoints, rerank scores, and all
closure numbers live in centered space. The causality control is part of
the acceptance: a REVERSED itinerary must close on A instead of B — if
steering passes but reversal fails, something other than the itinerary
is moving the text.

Anti-rut and prompt-attestation refusal are inherited unchanged from
G-4. The dual-corpus law holds: the proposer volume-scales (pinned
corpus_big.txt), the meaning geometry coherence-scales (Brown dense).
"""
from dataclasses import dataclass, field

import numpy as np

LEGS = 4
LEG_DEPTH = 6
BEAM_WIDTH = 12
POOL_TRI = 10
POOL_BI = 6
POOL_KEEP = 4
COUNT_BONUS = 0.05
THETA_LEG = 0.0


class Itinerary:
    """Waypoints w(t) = centered-normalized (1-t)·vA + t·vB."""

    def __init__(self, space, v_a, v_b, legs=LEGS):
        self.space = space
        self.v_a, self.v_b = v_a, v_b
        self.legs = legs
        self.waypoints = [space.waypoint(v_a, v_b, k / (legs - 1))
                          for k in range(legs)]

    def reversed(self):
        return Itinerary(self.space, self.v_b, self.v_a, self.legs)


@dataclass
class Leg:
    tokens: list
    closure_to_b: float      # centered cos of leg content to target B
    closure_to_a: float      # centered cos of leg content to source A


@dataclass
class JourneyResult:
    status: str              # "OK" | "REFUSE_PROMPT" | "REFUSE_BEAM" | "REFUSE_AUDIT"
    legs: list = field(default_factory=list)


class Journey:
    def __init__(self, proposer, geometry, space, depth=LEG_DEPTH,
                 width=BEAM_WIDTH, keep=POOL_KEEP, count_bonus=COUNT_BONUS,
                 theta_leg=THETA_LEG):
        self.p = proposer
        self.g = geometry
        self.space = space
        self.depth = depth
        self.width = width
        self.keep = keep
        self.count_bonus = count_bonus
        self.theta_leg = theta_leg

    # ── inherited refusal (G-4) ──────────────────────────────────────
    def prompt_attested(self, prompt):
        p = tuple(prompt)
        tri_hit = ((p[-2], p[-1]) in self.p.tri and
                   sum(self.p.tri[(p[-2], p[-1])].values()) >= 2)
        bigs = all(p[i + 1] in self.p.bi.get(p[i], {})
                   for i in range(len(p) - 1))
        return tri_hit or bigs

    # ── the steered proposal pool (law 3) ────────────────────────────
    def _pool(self, ctx2, last, target):
        cands = self.p.tri.get(ctx2)
        pool = (cands.most_common(POOL_TRI) if cands else
                (self.p.bi[last].most_common(POOL_BI)
                 if last in self.p.bi else []))
        if target is None:            # unsteered control: count order
            return pool[:self.keep]
        scored = sorted(
            pool,
            key=lambda wc: (float(self.space.word(wc[0]) @ target)
                            if wc[0] in self.g else -1.0)
            + self.count_bonus * np.log1p(wc[1]),
            reverse=True)
        return scored[:self.keep]

    def _leg_beam(self, ctx, used, target):
        outs = [(list(ctx), set(used))]
        for _ in range(self.depth):
            nxt = []
            for path, u in outs:
                pool = self._pool((path[-2], path[-1]), path[-1], target)
                for w, _ in pool:
                    bg = (path[-1], w)
                    if bg in u:                     # anti-rut (G-4)
                        continue
                    nxt.append((path + [w], u | {bg}))
            outs = nxt[:self.width]
            if not outs:
                break
        return [(p[len(ctx):], u) for p, u in outs]

    def _leg_region(self, tokens):
        ws = [w for w in tokens if w in self.g and w not in self.p.stop]
        if not ws:
            return None
        return np.mean([self.space.word(w) for w in ws], axis=0)

    def travel(self, prompt, itinerary, steer="propose"):
        """steer: 'propose' (the law), 'audit' (recorded control),
        'off' (unsteered flat control)."""
        prompt = list(prompt)
        if not self.prompt_attested(prompt):
            return JourneyResult("REFUSE_PROMPT")
        ca = self.space.centered(itinerary.v_a)
        cb = self.space.centered(itinerary.v_b)
        ctx, used, legs = list(prompt), set(), []
        for k, target in enumerate(itinerary.waypoints):
            pool_target = target if steer == "propose" else None
            cands = self._leg_beam(ctx, used, pool_target)
            if not cands:
                return JourneyResult("REFUSE_BEAM", legs)
            if steer == "off":
                select_target = self.space.region(prompt)
                if select_target is None:
                    select_target = self.space.centered(itinerary.v_a)
            else:
                select_target = target
            scored = []
            for tokens, u in cands:
                r = self._leg_region(tokens)
                scored.append((float(r @ select_target) if r is not None
                               else -1.0, tokens, u))
            s, best, u2 = max(scored, key=lambda x: (x[0], x[1]))
            if s < self.theta_leg:
                return JourneyResult("REFUSE_AUDIT", legs)
            r = self._leg_region(best)
            legs.append(Leg(best,
                            float(r @ cb) if r is not None else 0.0,
                            float(r @ ca) if r is not None else 0.0))
            ctx += best
            used = u2
        return JourneyResult("OK", legs)
