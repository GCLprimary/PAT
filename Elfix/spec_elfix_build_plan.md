# Build Spec — Sound as Earned Geometry

**Name:** ElfIX *(a play on 3·6·9 and "Felix" — coined by the author, so the system is named
from within rather than after an external figure. It carries forward the name of the ElfIX
phonology ladder this work continues and completes.)*

**One-line purpose:** A language model whose units are points and trajectories in a feature
space that **sound already has**, where higher-order units **form themselves** from the geometry
of lower ones, and where **every value traces back to a count you can point at**.

This is the unification of the two systems you stored away. They were never two ideas. GCL had
the ambition — *sound forms shapes* — wearing imported geometry. The original **ElfIX ladder** had
the earned geometry but stopped at scalars before letting shapes form. This project — **ElfIX**,
carrying that lineage's name forward — keeps the earned half of each and discards the imported half.

---

## The Design Laws

These are inviolable. Every piece below is checked against them.

1. **Earned geometry only.** Every coordinate, axis, distance, and threshold must be *derived from
   the sound or counted from the corpus*. No constant whose value comes from outside the data.
   *(NEW law — the lesson from triaging GCL. The φ-chain, Mersenne, Ω_m, and Dual-13 derivations
   failed your own `cubic_nearmiss` "is this load-bearing or decoration?" test, so they are out.)*

2. **Absence ≠ zero.** A unit unseen in a context is *absent*, not present-at-zero. Forbidden
   (structural) and unattested (evidential) are different facts and never collapse.
   *(Ported — ElfIX `slope_source`, why_piece3.)*

3. **One source of truth.** Any derived set (prefix legality, boundary tables, the unit
   inventory) is a *view* of one ground table, re-derived and asserted in test, never hand-listed.
   *(Ported — ElfIX `onset_legality`, why_piece1.)*

4. **Never a centre without its width.** A unit's position is reported as centre **and** spread.
   A peaked, high-support unit pins tight; a flat or low-support one stays honestly wide.
   *(Ported — ElfIX `relational`, why_piece15.)*

5. **Ternary evidence.** Attested (+1) / silent (0) / evidenced-against (−1) wherever the corpus
   can be silent on a legal possibility.
   *(Ported — ElfIX `ternary_valence`, why_piece6.)*

6. **Readable AND self-forming — no gradient black box in the core.** The higher rungs must form
   from the geometry of the data, not be learned by an opaque optimiser. This is the research bet;
   see §Open Bets. *(NEW — original bet.)*

---

## Provenance legend

Every piece is tagged with where it came from:

- `[ElfIX]` — ported from the **original ElfIX phonology ladder** (the precursor this project is
  named after and continues; file / piece named).
- `[GCL]` — salvaged from GeometricClarityLab's **top box only** (the part that computes).
- `[cleankit]` — from the cleankit precursor.
- `[Mind_Space]` — from the original `.drawio` mind map.
- `[NEW→established]` — new to your system, but grounded in published work (cited).
- `[NEW→original]` — genuinely new design move. Flagged honestly as unproven.

---

## Deliberately dropped (and why)

Listing what is *out* is part of the discipline — Law 1 has to bite on something.

| Dropped | Origin | Why |
|---|---|---|
| 3-6-9 axis flips | `[Mind_Space]` 3,6,9 cluster | Imported geometry; axis assignment not earned from sound. |
| φ-chain path lengths (Sq=φ, φ², φ³) | `[GCL]` `transducer`, `axis_state` | Swappable for hand-set constants; decorative, not load-bearing. |
| Ω_m / Mersenne / Dual-13 thresholds | `[GCL]` `invariants`, `ouroboros_engine` | Cosmological provenance does no computational work (Law 1). |
| Möbius 5-twist surface position | `[GCL]` `mobius_reader` | A relabel of pipeline stages, not a mechanism. |
| pi2_sphere cosmology | `[GCL]` `pi2_sphere` | Out of scope; self-disclaimed ("without claiming empirical reality"). |

---

## The Ladder

Each piece states its **Guarantee** (one line, the only thing it promises), its **Provenance**,
the **Why**, and the **Open question** it carries. Built bottom-up; each rung stands on the one below.

### Tier 0 — Substrate: the feature space

**Piece 0 · `feature_substrate`**
- **Guarantee:** Each phoneme is a fixed point in ℝᵈ whose coordinates are articulatory distinctive
  features; phonemes that differ in one feature differ in one coordinate.
- **Provenance:** `[ElfIX]` `phoneme_features` (why_piece2) for the "differ only where they differ"
  representation. Grounded in `[NEW→established]` distinctive-feature theory — Jakobson, Fant & Halle,
  *Preliminaries to Speech Analysis* (1952); Chomsky & Halle, *The Sound Pattern of English* (1968);
  and **Feature Geometry** — Clements (1985), Sagey (1986), which arranges features as a structured
  geometry rather than a flat bundle.
- **Why:** This is the one place geometry is *given* rather than built. The vowel subspace is the
  formant plane (F1/F2), a literal 2-D map — Peterson & Barney (1952). Law 1 is satisfied at the
  root: the axes are articulation, not invention.
- **Open question:** sonority magnitude. The sonority scalar is one coordinate, but its *spacing*
  (why nasals at 3 not 2.7) is still the borrowed ordinal scale ElfIX flagged. The designated fix is
  corpus-derived sonority — carry the open question forward, do not pretend it's closed.
  `[ElfIX]` why_piece2's own unresolved note.

### Tier 1 — Units as points

**Piece 1 · `unit_point`**
- **Guarantee:** Any unit (phoneme now; higher units later) has a position = centre + width in the
  substrate, plus a deterministic positional signature.
- **Provenance:** centre+width from `[ElfIX]` `relational` (Law 4). Positional signature from
  `[Mind_Space]` Remainder-Containers 4×4 grid traversal, implemented as `[GCL]` `symbolic_compiler`
  (the box string). Kept because it is deterministic and field-independent — a stable cross-session key.
- **Why:** Two orthogonal readable views of one unit (continuous position + discrete box signature)
  give the comparison stage two independent handles without either being a black box.
- **Open question:** whether the box signature earns its keep once trajectory geometry (Tier 2) exists,
  or becomes redundant. Build it, then measure; do not assume.

### Tier 2 — Sequences as trajectories

**Piece 2 · `trajectory`**
- **Guarantee:** An utterance is an ordered path through the substrate; its first derivative is the
  sonority slope; its sonority minima are candidate boundaries.
- **Provenance:** the slope key from `[ElfIX]` `slope_source` (why_piece3, "more dimension not more
  window" — factored modelling, Brown et al. 1992; Bilmes & Kirchhoff 2003). Path-as-object from
  `[Mind_Space]` (numbers as walks). Grounded in `[NEW→established]` **Articulatory Phonology** —
  Browman & Goldstein (1986–1992), where speech units *are* dynamical trajectories ("gestures") in
  articulator space; and the **Sonority Sequencing Principle** — Selkirk (1984), Clements (1990),
  which places syllable boundaries at sonority minima.
- **Why:** This is the rung where "sound forms shapes" stops being a slogan. The arch of `plant`
  (p→l→æ→n→t rising to the vowel, falling to the edges) is the trajectory, and it is earned entirely
  from Tier 0. No imported shape.
- **Open question:** how much of the trajectory beyond the sonority projection carries usable signal —
  the full ℝᵈ path vs the 1-D sonority contour. Measure before committing dimensions.

### Tier 3 — Self-forming higher units  *(the new rung — the heart of the system)*

**Piece 3 · `emergent_unit`**
- **Guarantee:** A recurring, geometrically coherent sub-trajectory (bounded by sonority minima)
  is promoted to a named higher unit when its recurrence count and within-cluster tightness cross
  thresholds; promotion uses ternary evidence and reports centre+width.
- **Provenance:** promotion machinery from `[GCL]` `malleable_library` (malleable→confirmed,
  confidence-gated) and `[ElfIX]` `ternary_valence` + `relational` (centre+width). Boundary cue from
  Tier 2. The clustering itself is `[NEW→original]`: units emerge where sub-trajectories cluster in
  the **readable** feature manifold. Nearest established cousins, cited as scaffolding not authority:
  Self-Organizing Maps — Kohonen (1982) — topology-preserving feature maps; agglomerative clustering;
  and as the *contrast* baseline, Byte-Pair-Encoding / unigram tokenisation — Sennrich et al. (2016),
  Kudo (2018) — which merge units by *orthographic frequency*. ElfIX merges by *geometric
  coherence of sound trajectories* instead. That difference is the whole novelty.
- **Why:** This is the leap from a ladder you hand-built to a ladder that builds itself, while staying
  readable (Law 6): the clusters that deserve to be syllables/morphemes are simply the sub-paths that
  land near each other — the grouping is *given by the data's geometry*, not learned by gradients.
- **Falsification (mandatory, in the discipline of "assert, don't assume"):** emergent boundaries
  must align with held-out human syllable (then morpheme) boundaries **above a frequency-matched
  baseline**. If they do not beat BPE-by-frequency on held-out segmentation, the central thesis has
  failed *here* and the build stops for diagnosis. Do not climb past a failed Tier 3.
- **Open question:** the tightness threshold. It must be *earned* (e.g. the elbow of the
  within-cluster-distance distribution), never a magic number (Law 1).

### Tier 4 — Comparison: counted all-pairs attention

**Piece 4 · `all_pairs`**
- **Guarantee:** Every active unit is scored against every other by distance/cosine in the readable
  space, producing a weighting matrix; no learned projections.
- **Provenance:** `[Mind_Space]` EXAMINE — this is the `Sync.` node finally turned into the 4×4
  comparator we discussed, generalised to N×N. Seeded by `[cleankit]` `similarity_recall` (stream
  overlap) and `[GCL]` `fft_normalize` / `holographic_linkage` (spectral views as an alternate
  distance). The mechanism is `[NEW→established]` **attention** — Bahdanau et al. (2014), Vaswani et
  al. (2017) — but in the **readable variant**: scores are counted similarities, not learned Q·K, so
  the O(n²) cost buys simultaneity *without* surrendering interpretability.
- **Why:** All-pairs comparison is the engine of self-formation (Tier 3 surfaces *which* groupings
  matter only because every unit can weigh every other). It is the operation you reached for across
  every system and never had cleanly.
- **Open question:** which distance. Cosine in feature space, trajectory (DTW-style) distance, or
  box-signature overlap — pick by held-out behaviour, not aesthetics.

### Tier 5 — Carry: interpretable recurrence

**Piece 5 · `decaying_carry`**
- **Guarantee:** A context state accumulates from resolved units and decays by a fixed corpus-set
  rate between steps; what persists is what was strong enough to survive the bleed.
- **Provenance:** `[GCL]` `relational_tension` (the decaying carry vector across sentences) — the one
  piece of GCL's recurrence that computes. Canonical name `[NEW→established]`: a recurrent hidden
  state / leaky integrator (the readable ancestor of RNN state).
- **Why:** simultaneous attention (Tier 4) sees *within* a window; the carry is how context survives
  *across* windows without an O(n²) blow-up over all history. Two complementary memories: all-pairs
  (sharp, local, expensive) + decaying carry (soft, global, cheap).
- **Open question:** the decay rate must be earned (e.g. from measured context half-life in the
  corpus), not the Mersenne-subtraction rate it had in GCL (Law 1 — that origin is dropped).

### Tier 6 — Routing: shape selects the operation

**Piece 6 · `shape_routing`**
- **Guarantee:** The geometry of the current trajectory selects which operation handles it
  (e.g. compare vs accumulate vs filter); the routing key is read from the shape, not learned.
- **Provenance:** `[GCL]` `geometric_ops` (triangle→filter, pentagon→accumulate, hexagon→compare) —
  the one genuinely novel idea in GCL. Reframed as `[NEW→established]` conditional computation:
  Mixture-of-Experts routing — Jacobs et al. (1991), Shazeer et al. (2017) — except ElfIX's gate is
  a *readable geometric predicate* on the trajectory, not a learned router. `[NEW→original]` in that
  the routing key is earned from sound-shape.
- **Why:** this is where you're beside the field on a live problem rather than behind it. Keep it,
  but earn the shape→op map from data (which shapes actually recur), don't hand-assign it.
- **Open question:** whether the operation set is discovered or declared. Prefer discovered.

### Tier 7 — Readout: confidence-gated commitment

**Piece 7 · `recognition_readout`**
- **Guarantee:** Output sharpness is set by how strongly the current input is recognised: high
  recognition → commit (low temperature); novel → stay open (high temperature). Continuous, no gate.
- **Provenance:** `[cleankit]` `recognition_score` + `score_to_temperature` verbatim in spirit
  (linear, two inspectable constants). Canonical `[NEW→established]`: adaptive / entropy-aware
  decoding. Confidence is *measured*, never a dialled constant — which keeps the readout honest.
- **Why:** the system's certainty should be a fact about recognition, not a free parameter. This is
  already doctest-green in cleankit; it ports almost unchanged.
- **Open question:** the curve. Linear now; a curved map (commit only at very high confidence) is a
  *post-data* change earned by observing real score distributions, not chosen up front.

---

## Build order & dependency notes

```
0 → 1 → 2        (substrate, points, trajectories)   ← mostly PORTABLE from ElfIX + cleankit
        ↓
        3        (self-forming units)                 ← FIRST RESEARCH MILESTONE + falsification gate
        ↓
   4 ←→ 5        (all-pairs + carry)                  ← the two memories
        ↓
   6 → 7         (routing, readout)                   ← only after 3 validates
```

Tiers 0–2 are largely a port: you already have the phoneme data, the slope key, the box encoder, and
the recognition→temperature wire. The real new work — and the place to spend effort first — is **Piece 3**.

---

## First milestone (the only thing worth building before anything else)

Build 0–2 from existing ElfIX phoneme data, implement Piece 3's trajectory clustering, and run the
**falsification test**: do emergent unit boundaries match held-out syllable boundaries above a
frequency-matched BPE baseline?

- **If yes:** the core thesis — *readable, self-forming units from earned sound-geometry* — has its
  first real evidence. Proceed up the ladder.
- **If no:** stop. The thesis failed at the cheapest possible rung, which is exactly where you want to
  learn it. Diagnose Piece 3 before building 4–7 on top of a hollow claim.

This gate is the entire reason to build bottom-up: it makes the central bet falsifiable at the
smallest scale, the same flawless-first discipline that runs through ElfIX.

---

## Open Bets (stated plainly, eyes open)

1. **Sound-first is underexplored, not proven.** The mainstream throws phonology away and tokenises
   orthography (BPE). A feature-geometric, sound-grounded substrate is a real road less travelled —
   and that is where new things come from — but "different substrate" is not "guaranteed scaling win."
   Sound-grounded models exist in research and have not dethroned text tokenisation at scale. Build it
   because it is real and yours; do not assume it wins.

2. **Readable AND self-forming is the actual research bet (Law 6).** The property that lets
   transformers self-form rungs (gradients) is the same property that makes them unreadable. ElfIX
   bets that earned geometry reaches self-formation *without* gradients, because the groupings are
   given by the data's shape rather than learned by an optimiser. This is the genuinely novel claim,
   and Piece 3's falsification test is its first and cheapest examination. It may not hold. That is
   what the gate is for.

---

*Format follows the ElfIX `spec_piece` / `why_piece` convention: each piece guarantees one thing,
cites its origin, and carries its open question forward unresolved rather than pretending it is closed.*
