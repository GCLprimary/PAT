"""R-4: the imposter ceiling (probe 35) — the safety case, CORRECTED.

THE FINDING (this build's principal result, owner-ruled into the tests):
probe 35's claim — "theta = 0.98 sits above the highest lie the geometry
can tell" — is FALSE over the open vocabulary. The voicing-neutral shape
space is many-to-one at the word level: 51.6% of mined bases live in a
homoshape collision group (ball/bell/bill/bowl/pool/pull are one shape
word), so the population imposter ceiling is EXACTLY 1.0 — no threshold
can separate identical vectors. Probe 35's clean 0.9769 was a lucky
draw (a random 40-base vocabulary carries a colliding pair ~43% of the
time), and the shipped learning battery ALREADY CONTAINED a perfect
imposter (cell / seal): its zero-confabulation result survived on
argmax tie order.

The truth has three layers, and the diagnostic reports all three:

  1. ceiling_all      — 1.0 whenever a homoshape imposter is in reach:
                        the collision layer. Curating the KNOWN set does
                        not help; observations come from the world.
  2. ceiling_distinct — the near-miss continuum among genuinely distinct
                        shapes (~0.98 and GROWING with vocabulary size:
                        0.9769 at the probe's draw, 0.9839 at n=40).
  3. realized ceiling — what a specific pinned battery actually exposed;
                        the composition battery's is 0.9245, which is
                        the honest explanation of its clean run.

The repair is measured and ranked (next frontier): a phoneme-space
second gate in analyze — the 1560-dim phon space separates every
homoshape pair found. Until it lands, zero confabulation is a property
of a vocabulary, checkable with shape_collisions(), not a property of
the geometry.

Law-4 hygiene (the 'listing' pattern) still applies to the withheld set;
it is necessary, and this build proved it is not sufficient.
"""
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from .embed import shape


@dataclass
class ImposterReport:
    ceiling: float           # ceiling_all: with collisions, exactly 1.0
    ceiling_distinct: float  # highest lie among distinct-shape imposters
    true_min: float          # the low tail of true bindings (allomorphs)
    true_mean: float         # where true bindings mass
    plateau_width: float     # true_mean - ceiling_distinct (documented)
    n_true: int
    n_wrong: int
    collisions: list = field(default_factory=list)   # (word, base, sfx)
    excluded: list = field(default_factory=list)     # law-4 hygiene drops


def shape_seq(pron):
    return tuple(shape(p) for p in pron)


def shape_collisions(embedder, words):
    """The census tool: groups of distinct words sharing one shape
    sequence. Zero groups is the precondition the old safety case
    silently assumed."""
    groups = defaultdict(list)
    for w in words:
        groups[shape_seq(embedder.corpus[w])].append(w)
    return {k: v for k, v in groups.items() if len(v) > 1}


def imposter_ceiling(embedder, transform, known_bases,
                     known_forms, unknown_forms):
    """Score distributions over known/withheld derived words — all three
    layers of the truth. See module docstring."""
    known_bases = list(known_bases)
    known_set = set(known_bases)
    excluded = [w for _, _, w in list(known_forms) + list(unknown_forms)
                if w in known_set]

    bindings = {}
    for b in known_bases:
        pron = list(embedder.corpus[b])
        bindings[(b, None)] = (embedder.shape_vec(pron), shape_seq(pron))
        for sfx in transform.suffixes:
            v = transform.bind(pron, sfx)
            if v is not None:
                bindings[(b, sfx)] = (
                    v, shape_seq(pron + transform.modal_phon[sfx]))

    true_scores, wrong_scores = [], []
    ceiling_distinct = -1.0
    collisions = []
    for group, forms in (("known", known_forms), ("unknown", unknown_forms)):
        for base, sfx, w in forms:
            if w in known_set:
                continue
            obs = embedder.shape_vec(embedder.corpus[w])
            oseq = shape_seq(embedder.corpus[w])
            for key, (vec, bseq) in bindings.items():
                s = float(obs @ vec)
                if group == "known" and key == (base, sfx):
                    true_scores.append(s)
                    continue
                wrong_scores.append(s)
                if bseq == oseq:
                    collisions.append((w, key[0], key[1]))
                else:
                    ceiling_distinct = max(ceiling_distinct, s)

    true_mean = float(np.mean(true_scores))
    return ImposterReport(
        ceiling=max(wrong_scores),
        ceiling_distinct=ceiling_distinct,
        true_min=float(min(true_scores)),
        true_mean=true_mean,
        plateau_width=true_mean - ceiling_distinct,
        n_true=len(true_scores),
        n_wrong=len(wrong_scores),
        collisions=collisions,
        excluded=excluded,
    )


def realized_ceiling(embedder, transform, bases, observed):
    """Layer 3: the ceiling a specific battery actually exposed —
    observed = [(word, true_base)] scored against every binding of
    `bases` except the true base's."""
    bindings = {}
    for b in bases:
        pron = list(embedder.corpus[b])
        bindings[(b, None)] = embedder.shape_vec(pron)
        for sfx in transform.suffixes:
            v = transform.bind(pron, sfx)
            if v is not None:
                bindings[(b, sfx)] = v
    ceiling, arg = -1.0, None
    for w, true_base in observed:
        obs = embedder.shape_vec(embedder.corpus[w])
        for (kb, ks), vec in bindings.items():
            if kb == true_base:
                continue
            s = float(obs @ vec)
            if s > ceiling:
                ceiling, arg = s, (w, kb, ks)
    return ceiling, arg
