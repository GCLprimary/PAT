# mirror — Workshop v1 Build Specification (probes 29–32)

**Location:** `~/mirror` (extends the accepted generation build; a_mem untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` → stop.
**Reference probes delivered:** probe29/29-notes (word-level path completion —
CLOSED negative, kept as evidence), probe30 (topic-rung constraint +
segmentation), probe31 + probe31b (interruption battery + the dual-threshold
policy), probe32 + probe32b (topic-to-topic steering, corrected run).

**New laws this build codifies (module docstrings + enforced in code):**
1. **Center before measuring.** All region/topic similarity uses vectors with
   the global corpus component removed (one shared helper; three probes were
   fooled by hubness before this became law). Raw cosines to averaged targets
   are forbidden in workshop code.
2. **Consonance ≠ commitment.** Integration is generous (θ_c); page-turns are
   strict and coherent (θ_a, mutually-consonant pending pair, turn onto their
   blend). One threshold doing both jobs is the measured failure mode.
3. **The corridor is set at proposal time.** Steering biases the proposal
   pool; audit-only steering is 2–3× weaker (measured). The audit disposes
   only among what was proposed.
4. **Artifact over recipe.** Test fixtures (documents, episode banks, category
   vectors) are generated ONCE at build time and pinned into the repo as
   files; tests read fixtures, never rebuild them from NLTK. (The G-4
   corpus-vintage lesson, applied preemptively.)

---

## V-0 · Housekeeping: pin the corpora, revisit the re-band

Pin `data/corpus.txt` and `data/corpus_big.txt` as shipped artifacts (copy
this machine's actual files; note their provenance and word counts in
`data/README`). Then re-run the G-4 gates against the spec-literal numbers
(salad 100/100, gap ≥ 50): if green on the pinned artifacts, retire the
re-band and restore the literal gates; if not, keep the band and record both
runs in HANDOFF. Flag, don't force.

## V-1 · `mirror/stage.py` — the discourse stage (probe 31b)

Maintained topic state with the DUAL-THRESHOLD policy:
- `observe(sentence_or_vec) -> (state, turned: bool, held: bool)`
- integrate at θ_c = 0.45 (blend 0.5, renormalize); lone dissonant → HOLD
  (state unchanged, dissonant stored as pending); a second dissonant that is
  mutually consonant with pending at θ_a = 0.65 → deliberate turn onto their
  blend. Thresholds are constructor parameters with these defaults.
- **Tests (pinned interruption fixture: 36 episodes, 6 per category, real
  a_mem writes, editorial interrupters at positions 3 and 5):**
  AT-INTERRUPT recall ≥ 60% (measured 71%); in-seg ≥ 95% (measured 99%);
  overall ≥ 78% (measured 83%); memoryless-at-interrupt recorded (measured
  1%) as the contrast line; single-θ v1 policy kept as a comparison run
  (measured 18% at interrupt) — if v1 ever beats DUAL overall, flag it.
- Strict segmentation regression (probe 30B, tol = 0, pinned docs):
  stage F1 ≥ memoryless F1 (measured 0.402 vs 0.315).

## V-2 · `mirror/regions.py` — centered region navigation (probes 29, 30A)

The centering helper (law 1) lives here. Region = centered centroid.
`between(vA, vB)` returns the normalized centered midpoint.
- **Tests (pinned held-sentence fixture):** midpoint-vs-middle-centroid
  cosine ≥ 2× either single endpoint and ≥ 10× a random word (measured
  +0.096 vs +0.059/+0.080 vs +0.006). Document the closed negative in the
  module docstring: word-level path completion on graph media loses to this
  space's own geometry (probe 29: best field 0.054 vs midpoint 0.067) —
  do not rebuild graph diffusion here.

## V-3 · `mirror/journey.py` — topic-to-topic generation (probe 32b)

Itinerary-steered generation on top of `generate.py`'s machinery:
- `Itinerary(vA, vB, legs=4)`: waypoint w(t) = centered-normalized
  (1−t)·vA + t·vB, t = leg/(legs−1).
- **Propose-time steering:** per beam step, take the trigram top-10 (bigram
  top-6 backoff), rerank by centered cosine to the current waypoint plus
  0.05·log1p(count), keep top-4; beam width 12, leg depth 6; anti-rut and
  prompt-attestation refusal inherited unchanged from G-4.
- `travel(prompt, itinerary) -> legs | refusal` with per-leg centered
  closure numbers attached.
- **Tests (pinned category-vector fixture, 20 ordered pairs × 2 prompts):**
  steered closure: mean centered cos→B at final leg ≥ +0.20 (measured
  +0.295) and strictly greater than leg 1; departure: cos→A final ≤ +0.15
  (measured +0.099); UNSTEERED flat: final cos→B ≤ +0.10 (measured ~+0.05);
  **REVERSAL control (the causality assertion):** reversed itinerary's
  final cos→A ≥ +0.25 (measured +0.324) AND its cos→B falls from leg 1 to
  final. If reversal fails while steering passes, something other than the
  itinerary is moving the text — flag, do not ship.
  Audit-only steering measured and recorded (≈ +0.184 end), not asserted.

## V-4 · `examples/demo_workshop.py`

< 45 s, two acts. Act 1: read a pinned multi-topic document with
interruptions aloud (print each sentence, the stage's held/turned verdict,
and the recalled episode) — show the stage holding through an interruption
and turning deliberately at the real boundary. Act 2 (the crown): a journey
from one category to another — print the itinerary, the four legs of text,
the centered closure numbers per leg, then run the REVERSED itinerary and
print both trajectories side by side. End with one refused journey
(unattested prompt) stating its reason plainly.

## V-5 · Close-out

`HANDOFF.md`: measured numbers, deviations, V-0 outcome (re-band retired or
kept), and the next-frontier ranking (standing: THE AGENT SHELL — every
organ now exists; local Wikipedia as the registry's first big source;
Morfessor/SIGMORPHON credibility run; the machinery/sensor variant, noted
once, unsteered). **Stop.**

## Non-goals
Fluent-prose pursuit, narrative/rhetorical planning (the itinerary is
geometric, not argumentative — say so in the README), word-level path
drawing (closed by probe 29 — evidence retained), agent shell (next
project), performance work, external LMs.
