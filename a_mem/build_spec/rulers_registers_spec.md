# mirror — Rulers & Registers Build Specification (probes 35–37)

**Location:** `~/alignment_field/mirror` (extends the accepted tree — the
last uploaded monorepo IS the current state; a_mem and agent untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part V → stop.
**Reference probes delivered:** probe35 (imposter ceiling), probe36 (dual
ruler + stamped registers), probe36b (phase ruler), probe37 + probe37b
(the English agreement test — broken ruler kept as evidence, corrected
frame beside it).

**New laws this build codifies:**
1. **Irrational for identity, rational for rhythm.** The √2 ruler's stamps
   never repeat (order/nesting); the 5:4 ruler's phases always return
   (cycles). One organ, two clocks, each provably unable to do the other's
   job (Weyl equidistribution vs LCM-20 re-alignment).
2. **Exactness extends to ℤ[√2].** Stamps are integer pairs (m, n) meaning
   m + n√2; comparisons are integer comparisons; no float is ever
   evaluated in a stamp or phase decision. Same law-5 spirit as ℤ[i].
3. **Subject identification is the frontier, not agreement.** The register
   mechanism is sound; knowing which noun opens it is where difficulty
   lives. Document in the module; do not pretend the strict frame is a
   parser.
4. **Miner hygiene:** withheld/test sets must exclude derived forms that
   are themselves known bases (the 'listing' label-noise pattern — third
   member of the instrument-noise family).

---

## R-1 · `mirror/rulers.py` — the linear organ (probe 36, 36b)

- `Stamp`: exact ℤ[√2] pair per position; ordering and subtraction as
  integer-pair ops; a `value_never_evaluated` doctest proving no float path.
- `PhaseRuler`: position mod 20 (the 3-4-5 / 5:4 channel), plus
  `detect_cycle(events) -> (concentration, phase)` via phase histogram.
- **Tests:** stamp ordering exact at 10^6 positions; pinned noisy-event
  fixture: hidden 20-cycle found at ≥ 8× mean concentration with exact
  phase (measured 12.8×, phase 7/7); √2-phase histogram on the same
  fixture ≤ 2.5× (the blindness assertion — if the aperiodic ruler ever
  "detects" a cycle, something is wrong with the fixture, flag it).

## R-2 · `mirror/registers.py` — stamped register bank (probe 36)

- `RegisterBank`: `open(features, stamp)`, `close(stamp) -> register`
  binding to most-recent-open by exact stamp comparison; `peek()` for
  checkers that consult without closing.
- **Tests (synthetic dependency streams, pinned):** single dependency 100%
  at gaps {2, 5, 10, 20, 40}; nested two-dependency streams: stamped bank
  100% at every gap; the UNSTAMPED comparison run recorded (~50%, chance)
  — if unstamped ever rises materially above chance, the generator's
  streams stopped being nested; flag.

## R-3 · agreement register (probe 37b)

- `mirror/agreement.py`: number lexicon built from the repo's own mined
  -s pairs (sg = bases, pl = derived; ambiguous dropped; **law-4 hygiene
  applied**); the strict-frame miner (sentence-initial DET-N subject,
  PP-chain material, det/prep-gated between-nouns); the register checker
  (first DET-N opens; verb closes; consonance = number match).
- **Fixture:** mine once from the PINNED corpus_big with the fixed seed,
  pin the resulting case list as an artifact (expected ≈ 240 cases /
  12 attractors — record exact counts at build time).
- **Tests (pinned fixture):** REGISTER no-attractor ≥ 90% (measured 94%);
  REGISTER attractor ≥ recent-noun attractor + 30 points AND ≥ trigram
  attractor (measured 83% vs 17% vs 67%); recent-noun attractor ≤ 40%
  (the seduction assertion — it's the control that proves the attractors
  are real; if it rises, the fixture's attractors aren't attractors).
- The broken first miner (probe 37) stays in the repo as evidence with a
  docstring naming the adjunct failure.

## R-4 · imposter-ceiling diagnostic (probe 35)

- `mirror/diagnostics.py`: `imposter_ceiling(known_bases, withheld) ->
  (ceiling, true_min, true_mean)` computing the score distributions over
  a pinned known/withheld split (law-4 hygiene on the withheld set).
- **Tests:** wrong-binding ceiling < 0.98 (measured 0.9769) — this is the
  safety-case number: the shipped θ sits above the highest lie the
  geometry can tell; true-binding mean ≥ 0.99; the report includes plateau
  width (documented, not asserted — malleability is organ-specific).

## R-5 · Close-out

`HANDOFF.md` Part V: measured numbers, deviations, fixture counts, and the
next-frontier ranking (standing candidates: attractor mining at scale —
better subject filters for real n; second feature register (tense concord);
the schooled twin / BLiMP run wiring registers in; WS-353 comparative row;
the sensor-alphabet world). **Stop.**

## Non-goals
Parsing, BLiMP/lesson experiments (designed, unprobed at build scale),
sensor worlds, agent changes, WS-353 fetch, performance work.
