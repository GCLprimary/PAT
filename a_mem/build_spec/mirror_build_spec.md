# mirror — Reasoning Core Integration · Build Specification

**Location:** `~/mirror` (working name; rename at will)
**Prerequisites:** `~/a_mem` installed (Phase 3 tree); ElfIX repo available at a
configurable path (default sibling `~/Elfix`). mirror imports both; it owns
neither. Reference probes 17–21 delivered alongside this spec.
**House rules:** tests before features; acceptance by inequality; contradictions
flagged, never reconciled silently. Build, write `HANDOFF.md`, **stop** — review
happens with the humans.

**Law-scope note (read first):** a_mem's no-float/exact-arithmetic law applies to
its harness and contraction, unchanged. The meaning geometry (W-4) uses log-PPMI
floats legitimately — every value still traces to a count (Law: traceability, not
integer-ness, is the invariant outside the lattice). Do not "fix" this.

---

## What this package is

The integration layer that composes the five probe-validated organs into one
system:
- **represent** — voicing-neutral shape-bigram embeddings (ElfIX features)
- **transform** — seam-aware binding: bind(base, suffix-category) → predicted form
- **memory** — a_mem episodes via EpisodeHooks (unchanged)
- **loop** — mirror analysis: propose / reflect / settle-or-refuse
- **meaning** — PPMI count geometry + the form|meaning rung (cross-modal recall)

## Modules and acceptance

### W-1 `mirror/embed.py` — the embedder (from probe 18)
Shape-bigram + unigram vectors over ElfIX `(manner, place)` voicing-neutral
shapes, `("V",)` for sonority ≥ 6. One function: `shape_vec(phonemes) -> unit vec`.
- **Tests (25-word bank from probe 18, grid-47 a_mem):** noisy self-recall at
  fixed-angle cos 0.90 ≥ 85% (measured 92%); relative-form recall ≥ 60%
  (measured 78%, chance 4%); near-form discrimination 3/3. Crowding
  (mean nn-cosine) reported, not asserted.

### W-2 `mirror/transform.py` — seam binding (from probe 19)
`fit(pairs)` learns modal suffix shape-forms from a train split (mined
base→derived pairs; miner included, ~20k pairs from the CMU data).
`bind(base_pron, suffix) -> vec` = shape_vec(base + modal form) — the SEAM rule.
Persist the learned suffix inventory.
- **Tests:** held-out mean cosine(bind, actual) ≥ 0.98 (measured 0.997);
  sibling-library retrieval through a_mem ≥ 38/39 with SEAM strictly ≥ SUM
  (measured 39/39 vs 38/39). Assert SEAM ≥ SUM on cosine in both spaces
  (measured +0.14 phon, +0.12 shape).

### W-3 `mirror/loop.py` — the mirror (from probe 20)
Two-layer analyze: L1 bare reflection against known bases; L2 bound reflection
over base × suffix proposals; settle at agreement ≥ θ (default **0.98**), else
REFUSE. Return (mode, base, suffix, score, depth).
- **Tests (40 known bases, 20 known / 20 withheld test words):** known-set
  base+suffix correct ≥ 17/20 at θ=0.98 (measured 19/20, 1 safe refusal);
  withheld-set refusal 20/20 with **zero confabulation** (hard assert);
  and the laziness law as a test: accuracy at θ=0.90 must be LOWER than at
  θ=0.98 (measured 4/20 vs 19/20) — if this inverts, the embedder or corpus
  changed character; flag it.

### W-4 `mirror/meaning.py` — the count geometry (from probe 21 + fix)
Corpus builder per the ElfIX data contract (Brown via NLTK; the repo's
`make_corpus.py` conventions). Window-4 co-occurrence over top-4000 vocab,
**content-only context dimensions** (exclude top-120 frequency words as
contexts — the probe-21 fix), PPMI with zeros kept zero (ternary-zero law).
- **Tests:** relatedness — for ≥ 20 curated (word, related, random) triples
  (e.g. water/surface, war/civil, music/songs, money/tax), cos(word, related) >
  cos(word, random) in ≥ 90%; suffix-offset agreement reported with its random
  floor (measured +0.022 vs −0.001) — report-only, too weak to assert.

### W-5 `mirror/rung.py` — the form|meaning rung (from probe 21)
Episodes as concatenated unit-normalized blocks `[shape | meaning]` written
through EpisodeHooks; cross-modal cue = one block zeroed.
- **Tests (24-word bank):** meaning-only → form episode ≥ 90% (measured 100%);
  form-only → meaning ≥ 90% (measured 100%); chance 4%.

### W-6 `examples/demo_core.py`
End-to-end, < 30 s: load organs; present a NOVEL derived word (base in memory) →
loop analyzes it → retrieve the base's family from a_mem → print the base's
meaning neighborhood; then present a word with an UNKNOWN base → loop refuses,
says so plainly. This demo is the system's one-paragraph existence proof.

### W-7 Close-out
`HANDOFF.md` with measured numbers, deviations, and the scaling menu ranked
(candidates: corpus scale-up for W-4 strength; lexicon scale via a_mem grid
dial; morphological breadth — prefixes/compounds through the same W-2/W-3
machinery; rung crowding at 100+ words). **Stop after HANDOFF.**

## Non-goals
Corpus scale-up, prefix/compound coverage, performance work, the agent shell,
any machinery/sensor variant, UI. All of that is the next conversation, not
this build.
