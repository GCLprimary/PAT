"""
elfix/forward.py  —  Tiers 4-7 in one readable forward pass + the rung
=======================================================================
Tier 3 validated (syllables F1 ~0.93; morpheme recall via additive appendix
units), so per the spec build order we may finally wire the upper tiers together.
This composes them on one utterance, keeping every value inspectable:

  units      Tier 1/3  a word -> syllable units, each a centre + width (Law 4)
  attention  Tier 4    counted all-pairs cosine over the unit centres
  carry      Tier 5    a leaky integrator folding the units in sequence
  routes     Tier 6    each unit's discovered shape-class (op stub, Tier 6 status)
  recog/T    Tier 7    fraction of units that are KNOWN emergent units -> temperature
  word       THE RUNG  compose the syllable units into one word unit (centre+width)

`forward` runs the WORD level (phonemes -> syllables -> word). `forward_utterance`
runs the SAME machinery one level up on a multi-word utterance from running text:
words are the units (each itself a syllable->word rung), Tier-4 attention runs
BETWEEN words, Tier-5 carry runs ACROSS them at the re-validated 0.67 rate
(reset per utterance), and the rung composes the words into an UTTERANCE unit —
the full phonemes -> syllables -> words -> utterance hierarchy, on real text.

THE MORPHEME->WORD RUNG (the new structural piece)
--------------------------------------------------
`compose` builds a parent unit from child units: the parent centre is the
reliability-weighted blend of child centres (a tighter child pulls harder), and
its width is the honest total dispersion = within (mean child width) + between
(spread of child centres). For one child the parent inherits it exactly. This is
self-forming composition: the word is literally the weighted average of its
syllables, and you can point at every term.

PROVENANCE
----------
- Tier 4 attention: compare/all_pairs (Vaswani et al. 2017, readable variant).
- Tier 5 carry: carry/decaying_carry (leaky integrator; earned rate).
- Tier 6 routing: routing/shape_routing (MoE-style, readable geometric gate).
- Tier 7 readout: readout/recognition (adaptive temperature).
- centre+width at every rung: [ElfIX] relational (Law 4).
- The rung composition is [NEW->original]: higher units form from the geometry of
  lower ones, no gradients (Law 6).

DESIGN LAW CHECK
----------------
Law 4: every Unit (phoneme, syllable, word) carries centre AND width. Law 6: the
rung forms by counted composition, not an optimiser. Law 1: the carry rate and
the recognition->temperature constants are earned/inspectable, not magic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from .trajectory.trajectory import Trajectory
from .emergent.emergent_unit import syllable_boundaries, arcs, describe
from .carry.decaying_carry import DecayingCarry, EARNED_RATE
from .compare.all_pairs import attention
from .readout.recognition import score_to_temperature


def _centre_width(points: List[List[float]]) -> Tuple[List[float], float]:
    """Centre = mean point; width = mean L2 distance of members to it (Law 4)."""
    n = len(points)
    dim = len(points[0])
    centre = [sum(p[k] for p in points) / n for k in range(dim)]
    width = sum(sum((p[k] - centre[k]) ** 2 for k in range(dim)) ** 0.5
                for p in points) / n
    return centre, width


@dataclass
class Unit:
    """A unit at any rung, as a position = centre + width (Law 4)."""
    level: str                 # 'syllable' | 'word' | ...
    symbols: List[str]
    centre: List[float]
    width: float

    @classmethod
    def of(cls, level: str, symbols: List[str], points: List[List[float]]) -> "Unit":
        centre, width = _centre_width(points)
        return cls(level, list(symbols), centre, width)


def _spans(n: int, bounds: List[int]) -> List[Tuple[int, int]]:
    edges = [0] + sorted(b for b in bounds if 0 < b < n) + [n]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)
            if edges[i] < edges[i + 1]]


def syllable_units(symbols: List[str]) -> List[Unit]:
    """Segment a word into syllable units (maximal-onset seams), each centre+width."""
    t = Trajectory.of(symbols)
    if not t.points:
        return []
    return [Unit.of("syllable", t.symbols[a:b], t.points[a:b])
            for a, b in _spans(len(t), syllable_boundaries(symbols))]


def morpheme_units(symbols: List[str], appendix_inventory) -> List[Unit]:
    """Segment a word into MORPHEME units (contour seams + additive appendix
    seams), each centre+width. The sibling of `syllable_units`; `compose` lifts
    EITHER to a word unit — the rung is level-agnostic, so the morpheme->word and
    syllable->word paths share one composition (Law 6)."""
    from .emergent.appendix import geometry_boundaries_additive
    t = Trajectory.of(symbols)
    if not t.points:
        return []
    bounds = geometry_boundaries_additive(symbols, appendix_inventory)
    return [Unit.of("morpheme", t.symbols[a:b], t.points[a:b])
            for a, b in _spans(len(t), bounds)]


def compose(units: List[Unit], level: str = "word") -> Optional[Unit]:
    """
    THE RUNG: form a parent unit from child units. Parent centre = reliability-
    weighted blend of child centres (weight = 1/(1+width); a tighter child pulls
    harder). Parent width = within (weighted mean child width) + between (weighted
    spread of child centres about the blend) — honest total dispersion (Law 4).
    """
    if not units:
        return None
    dim = len(units[0].centre)
    w = [1.0 / (1.0 + u.width) for u in units]
    z = sum(w) or 1.0
    centre = [sum(wi * u.centre[k] for wi, u in zip(w, units)) / z
              for k in range(dim)]
    between = sum(wi * sum((u.centre[k] - centre[k]) ** 2 for k in range(dim)) ** 0.5
                  for wi, u in zip(w, units)) / z
    within = sum(wi * u.width for wi, u in zip(w, units)) / z
    symbols = [s for u in units for s in u.symbols]
    return Unit(level, symbols, centre, within + between)


def recognition(symbols: List[str], inventory: Dict, quanta: Tuple[float, float]
                ) -> float:
    """Tier 7 score: the fraction of this word's arcs that are KNOWN emergent
    units (present in `inventory`). High -> recognised -> commit; low -> novel ->
    stay open. Empty/absent inventory -> 0.0 (no basis, stay open)."""
    if not inventory:
        return 0.0
    t = Trajectory.of(symbols)
    spans = arcs(t)
    if not spans:
        return 0.0
    known = sum(1 for span in spans if describe(t, span, quanta) in inventory)
    return known / len(spans)


@dataclass
class ForwardResult:
    units: List[Unit]                 # Tier 1/3: the syllable units
    word: Unit                        # THE RUNG: the composed word unit
    attention: List[List[float]]      # Tier 4: all-pairs weight matrix
    carry: List[float]                # Tier 5: context after the bleed
    recognition: float                # Tier 7: how recognised (0..1)
    temperature: float                # Tier 7: the resulting reshape T
    routes: Optional[List[int]]       # Tier 6: per-arc shape-class id (-1 novel)


def forward(symbols: List[str], inventory: Dict = None,
            quanta: Tuple[float, float] = None, router=None,
            rate: float = EARNED_RATE) -> Optional[ForwardResult]:
    """
    One forward pass over a word. Tiers 4-7 compose, then the rung builds the word.
    `inventory`/`quanta` (from emergent.discover/auto_quanta) drive Tier-7
    recognition; `router` (a ShapeRouter) drives Tier 6. Both optional — without
    them recognition is 0 (everything novel) and routes is None. Pure, counted.
    """
    units = syllable_units(symbols)
    if not units:
        return None
    pts = [u.centre for u in units]

    # Tier 7: recognition sets the reshape temperature, which sharpens Tier 4.
    recog = recognition(symbols, inventory, quanta) if inventory else 0.0
    temp = score_to_temperature(recog)

    # Tier 4: counted all-pairs attention over the unit centres, sharpened by T.
    weights = attention(pts, temp)

    # Tier 5: a leaky integrator folds the units in order; what persists survived.
    carry = DecayingCarry(len(pts[0]), rate)
    for p in pts:
        carry.update(p)

    # Tier 6: route each arc by its discovered shape (ops are stubs, Tier 6 status).
    routes = router.route(Trajectory.of(symbols)) if router is not None else None

    # THE RUNG: compose the syllable units into the word unit.
    word = compose(units, "word")
    return ForwardResult(units, word, weights, carry.read(), recog, temp, routes)


# ── Utterance level: the whole ladder over a multi-word utterance ─────────────
def word_unit(word: str, phonemes: List[str]) -> Optional[Unit]:
    """A word as a unit, composed from its syllables (the syllable->word rung),
    relabeled by the word string for readability. None if it has no nucleus."""
    sylls = syllable_units(phonemes)
    if not sylls:
        return None
    u = compose(sylls, "word")
    u.symbols = [word]
    return u


@dataclass
class UtteranceResult:
    words: List[Unit]                 # the word units (each a syllable->word rung)
    utterance: Unit                   # THE RUNG one level up: words -> utterance
    attention: List[List[float]]      # Tier 4: BETWEEN-word all-pairs weights
    carry_trajectory: List[List[float]]   # Tier 5: carry state after each word
    recognition: float                # Tier 7: fraction of words attested
    temperature: float
    saliences: List[float]            # Tier 6: each word's carry salience (its predictiveness)


def forward_utterance(tokens, rate: float = EARNED_RATE,
                      router=None) -> Optional[UtteranceResult]:
    """
    Run the ladder over a multi-word utterance (a list of running_text Tokens):
    each in-vocab word becomes a unit (centre+width, itself a syllable->word rung),
    Tier-4 attention runs BETWEEN words, Tier-5 carry runs ACROSS them at the
    re-validated 0.67 rate (the carry starts fresh — utterance boundary = reset),
    Tier-7 recognition is the fraction of words attested, and the rung composes the
    words into an UTTERANCE unit. OOV words (no phonemes) are skipped.

    Tier 6 (when `router` has earned ops via learn_ops): SHAPE SELECTS THE OPERATION,
    as a SALIENCE on the carry update. A word folds into the carry weighted by its
    mean arc PREDICTIVENESS (the earned accumulate<->boundary disposition): a
    content word with predictive internal arcs carries strongly; a function word
    (a single boundary arc) contributes little. NOTE: a hard reset-at-boundary was
    measured and REJECTED — word-final arcs are nearly all boundary, so it flushed
    every word and destroyed the cross-word memory; lexical context persists at 0.67
    across word boundaries, so the op modulates WEIGHT, it does not reset.
    """
    units, kept = [], []
    for t in tokens:
        if t.phonemes:
            u = word_unit(t.word, t.phonemes)
            if u is not None:
                units.append(u); kept.append(t)
    if not units:
        return None
    pts = [u.centre for u in units]
    total = len(tokens) or 1
    recog = sum(1 for t in tokens if getattr(t, "tag", None) == "attested") / total
    temp = score_to_temperature(recog)
    weights = attention(pts, temp)                 # Tier 4: between words
    carry = DecayingCarry(len(pts[0]), rate)       # Tier 5: across words, fresh
    gated = router is not None and bool(router.predictiveness)
    traj, saliences = [], []
    for t, u in zip(kept, units):
        sal = 1.0
        if gated:                                  # Tier 6: shape sets carry salience
            ids = router.route(Trajectory.of(t.phonemes))
            preds = [router.predictiveness.get(c, 0.0) for c in ids]
            sal = sum(preds) / len(preds) if preds else 0.0
        traj.append(list(carry.update(u.centre, salience=sal)))
        saliences.append(sal)
    utt = compose(units, "utterance")              # THE RUNG: words -> utterance
    return UtteranceResult(units, utt, weights, traj, recog, temp, saliences)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    from elfix.emergent.emergent_unit import discover, auto_quanta
    from elfix.emergent.appendix import discover_appendices
    from elfix.routing.shape_routing import ShapeRouter
    corpus = list(load_cmu().values())
    trajs = [Trajectory.of(w) for w in corpus[:8000]]
    quanta = auto_quanta(trajs)
    inv = discover(corpus[:8000], quanta=quanta)
    appendix = discover_appendices(corpus)
    router = ShapeRouter(trajs)
    print("=== word level: phonemes -> syllables -> word ===")
    for w in (["r", "AH", "n", "IH", "NG"], ["k", "AE", "t", "s"]):
        r = forward(w, inv, quanta, router=router)
        sylls = ["".join(u.symbols) for u in r.units]
        morphs = ["".join(u.symbols) for u in morpheme_units(w, appendix)]
        print(f"\n{' '.join(w)}:")
        print(f"  syllables {sylls}  ->  word (rung), width {r.word.width:.3f}")
        print(f"  morphemes {morphs}  ->  word (rung)")
        print(f"  Tier 7 recognition {r.recognition:.2f} -> T {r.temperature}; "
              f"Tier 4 attention {len(r.attention)}x{len(r.attention)}; "
              f"Tier 6 routes {r.routes}")

    print("\n=== utterance level: words -> utterance, on a real Brown sentence ===")
    from elfix.running_text import load_utterances, tag_utterances
    cmu = load_cmu()
    utts = load_utterances()
    tagged, _ = tag_utterances(utts[:4000], cmu)
    # Tier 6: earn the op semantics on a slice, so the carry can be shape-gated
    streams = []
    for utt in tagged:
        s = [c for t in utt if t.phonemes
             for c in router.route(Trajectory.of(t.phonemes))]
        if len(s) > 1:
            streams.append(s)
    router.learn_ops(streams)

    toks = tagged[0]
    ur = forward_utterance(toks, router=router)             # shape-gated carry
    words = [t.word for t in toks]
    kept = [t.word for t in toks if t.phonemes]
    print(f"\n{' '.join(words)}")
    print(f"  {len(ur.words)} word units -> utterance unit (width {ur.utterance.width:.3f})")
    print(f"  Tier 7 recognition {ur.recognition:.2f} -> T {ur.temperature}")
    print(f"  Tier 4 attention {len(ur.attention)}x{len(ur.attention)} BETWEEN words; "
          f"Tier 5 carry across {len(ur.carry_trajectory)} words at rate {EARNED_RATE}")
    sal = sorted(zip(kept, ur.saliences), key=lambda x: x[1])
    hi = ", ".join(f"{w}({s:.2f})" for w, s in sal[-3:][::-1])
    lo = ", ".join(f"{w}({s:.2f})" for w, s in sal[:3])
    print(f"  Tier 6 shape-gated carry (salience = arc predictiveness):")
    print(f"      weighs HIGH: {hi}    weighs LOW: {lo}")
    if len(ur.words) > 1:
        i = 1
        j = max((k for k in range(len(ur.words)) if k != i),
                key=lambda k: ur.attention[i][k])
        print(f"  e.g. '{kept[i]}' attends most to '{kept[j]}' (nearest sound-shape)")
