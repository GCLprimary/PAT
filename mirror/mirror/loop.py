"""W-3 + G-3 + F-2: the mirror loop — propose / reflect / settle-or-refuse.

Given a surface pronunciation, recover its analysis against what memory
actually knows — or REFUSE. Three layers (probe 20; L3 from probe 25):

  L1  bare reflection: is the observation itself a known base?
  L2  bound reflection, suffix side: base x suffix SEAM proposals.
  L3  bound reflection, prefix side: prefix x base SEAM proposals.

Settle when the best standing agreement clears theta; otherwise refuse.
The laziness law (probe 20, kept as a test): LOWERING theta makes the
loop WORSE on knowns (4/20 at 0.90 vs 19/20 at 0.98) — an eager mirror
settles for the first flattering reflection. Strictness is where the
accuracy comes from; if that ever inverts, the embedder or corpus has
changed character.

THE PHON GATE (F-2, probe 39; the Part V repair). Shape proposes,
phon disposes: once a layer shape-accepts candidates, the settlement
happens INSIDE that layer under the gate —

  - candidates are walked in evidence order (shape score, then
    stem-phon consonance), never dict order;
  - the winner must pass stem-scoped phon identity AND suffix/prefix
    arbitration (bare forms: full-length phon identity);
  - a tie identical under every mechanism is refused, not ordered;
  - if every shape-accepted candidate is vetoed, the loop REFUSES with
    the gate's named reason — the gate never rescues an analysis from a
    lower layer; it only vetoes settlements.

This retires dict-order tie survival (the learning battery's cell/seal
luck) and turns the homoshape imposter ceiling of 1.0 into refusals:
zero confabulation becomes a property of the gated pipeline over the
open vocabulary, not of a lucky vocabulary draw.
"""
from dataclasses import dataclass

from .gate import PhonGate, evidence_walk

THETA_DEFAULT = 0.98


@dataclass(frozen=True)
class Analysis:
    mode: str                # "BARE" | "BOUND" | "PRE" | "REFUSE"
    base: str | None
    suffix: str | None
    score: float             # best standing agreement
    depth: int               # layers consulted
    prefix: str | None = None
    reason: str = ""         # refusals name their reason (gate-vetoed
                             # settlements name the mechanism)


class MirrorLoop:
    def __init__(self, embedder, transform, base_prons, space="shape",
                 gate=True):
        """base_prons: {base_word: phoneme tuple} — what memory knows.
        L3 proposals exist only when the transform learned prefixes.
        gate: True builds the phon gate from the transform (the F-2
        default), a PhonGate instance is used as-is, None/False runs
        ungated (diagnostics and before/after tables only)."""
        self.embedder = embedder
        self.transform = transform
        self.space = space
        self.base_prons = {b: list(pr) for b, pr in base_prons.items()}
        self.gate = (PhonGate.from_transform(transform) if gate is True
                     else (gate or None))
        self.base_vecs = {b: embedder.vec(pr, space)
                          for b, pr in base_prons.items()}
        self.bound = {}
        for b, pr in base_prons.items():
            for sfx in transform.suffixes:
                self.bound[(b, sfx)] = transform.bind(pr, sfx, space)
        self.bound_prefix = {}
        for b, pr in base_prons.items():
            for pre in transform.prefixes:
                self.bound_prefix[(b, pre)] = \
                    transform.bind_prefix(pr, pre, space)

    def analyze(self, pron, theta=THETA_DEFAULT):
        pron = list(pron)
        obs = self.embedder.vec(pron, self.space)
        gate = self.gate
        best = -1.0
        # L1: bare reflection against known bases
        depth = 1
        s1 = {b: float(obs @ v) for b, v in self.base_vecs.items()}
        if s1:
            best = max(best, max(s1.values()))
            cands = [b for b, s in s1.items() if s >= theta]
            if cands:
                if gate is None:
                    b1 = max(s1, key=s1.get)
                    return Analysis("BARE", b1, None, s1[b1], 1)
                ranked = sorted(
                    ((b, s1[b], gate.bare_cos(pron, self.base_prons[b]))
                     for b in cands),
                    key=lambda t: (-t[1], -t[2], t[0]))
                win, why = evidence_walk(
                    ranked,
                    lambda b: gate.check_bare(pron, self.base_prons[b]))
                if win is not None:
                    return Analysis("BARE", win[0], None, win[1], 1)
                return Analysis("REFUSE", None, None, best, 1, reason=why)
        # L2: suffix-bound proposals
        if self.bound:
            depth = 2
            s2 = {k: float(obs @ v) for k, v in self.bound.items()}
            best = max(best, max(s2.values()))
            cands = [k for k, s in s2.items() if s >= theta]
            if cands:
                if gate is None:
                    k2 = max(s2, key=s2.get)
                    return Analysis("BOUND", k2[0], k2[1], s2[k2], 2)
                ranked = sorted(
                    ((k, s2[k],
                      gate.stem_cos(pron, self.base_prons[k[0]]))
                     for k in cands),
                    key=lambda t: (-t[1], -t[2], t[0]))
                win, why = evidence_walk(
                    ranked,
                    lambda k: gate.check_bound(
                        pron, self.base_prons[k[0]], k[1]))
                if win is not None:
                    k = win[0]
                    return Analysis("BOUND", k[0], k[1], win[1], 2)
                return Analysis("REFUSE", None, None, best, 2, reason=why)
        # L3: prefix-bound proposals (probe 25)
        if self.bound_prefix:
            depth = 3
            s3 = {k: float(obs @ v) for k, v in self.bound_prefix.items()}
            best = max(best, max(s3.values()))
            cands = [k for k, s in s3.items() if s >= theta]
            if cands:
                if gate is None:
                    k3 = max(s3, key=s3.get)
                    return Analysis("PRE", k3[0], None, s3[k3], 3,
                                    prefix=k3[1])
                ranked = sorted(
                    ((k, s3[k],
                      gate.tail_cos(pron, self.base_prons[k[0]]))
                     for k in cands),
                    key=lambda t: (-t[1], -t[2], t[0]))
                win, why = evidence_walk(
                    ranked,
                    lambda k: gate.check_prefix(
                        pron, self.base_prons[k[0]], k[1]))
                if win is not None:
                    k = win[0]
                    return Analysis("PRE", k[0], None, win[1], 3,
                                    prefix=k[1])
                return Analysis("REFUSE", None, None, best, 3, reason=why)
        return Analysis("REFUSE", None, None, best, depth,
                        reason="no analysis stands")
