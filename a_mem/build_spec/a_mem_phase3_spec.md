# a_mem — Phase 3 Build Specification

**Prerequisite:** Phase 1 tree at `~/a_mem` (accepted), `DECISIONS_final.md`
(all rulings probe-backed), reference probes 13–16 available on request.
**Rule of the house:** propose tests before features; acceptance is an
inequality. When a result contradicts this spec, stop and flag — do not
reconcile silently.
**Scope:** implement exactly the items below, then write `HANDOFF2.md` and
stop. The system rests after Phase 3.

---

## W-1 · Radius channel (D-2) — the capacity mechanism

Extend the contraction with mass-weighted hop-age tracking and bin core
arrivals by age: signature becomes 9 cells × 6 hop bins (54-dim), replacing
the 9-vector as the classification code. Reference implementation: probe 13/14
`GaugeCap` (age blend on every mass addition; bin = round(hop_age) − 1,
clamped 0–5).

- API: `recall(signature=...)` accepts both 9-vector (legacy, warns) and
  54-vector. Library stores 54-dim codes; a migration note in HANDOFF2.
- Optional flag `core_mode="combo"` adds the ring×radius 150-dim code
  (25 ring cells × 6 bins) for small libraries; default is radius.
- **Acceptance:** `test_capacity` extended — 24-identity bank (probe 13's
  positions), classification ≥88% at k=24 for radius mode (measured 90%);
  legacy 9-vector path still passes existing selector tests.

## W-2 · Hybrid encoder + id-keyed recall (D-1, D-3, D-5)

New module `amem/encoder.py` + `amem/hooks.py`.

- **Embedding index:** minimal internal nearest-neighbor store
  (numpy cosine over stored unit vectors; no external deps). Modular: a
  protocol class so a real vector DB can replace it later (D-5).
- **Write path:** `hook.write_episode(embedding, payload_meta)` →
  placement optimizer chooses a constellation position maximizing distance
  to existing placements; if best achievable overlap vs any stored original
  ≥ 0.45 → relocate per D-3; if the caller pins placement → store-with-warning
  (warning recorded in library meta). Placement capacity is packing-limited
  (~9 at Chebyshev-5 on the 13-wide zone — probe 15); when the zone is full,
  raise a documented `PlacementFull` error (grid scaling is future work, not
  Phase 3).
- **Recall path:** `hook.recall_context(embedding)` → nearest-neighbor match
  in embedding space → episode id → anchor recall (Phase 1 route). The
  encoder NEVER re-derives placement at recall (probe-15 law).
- **Acceptance:** `test_encoder` — 8 episodes, noisy re-encounters at
  sigma ∈ {0.05, 0.10, 0.20}: end-to-end identity accuracy ≥95% at
  sigma ≤ 0.10 (embedding-space matching makes this near-trivial — that is
  the point); zero placement re-derivations on the recall path (assert by
  construction/spy); write-time separation report shows all pairwise
  original overlaps < 0.45 or a recorded warning.

## W-3 · Clock v2 scaffolding (D-4)

- Recall/sequence log completion trajectories (c1..c_cap) per turn into a
  runtime calibration buffer (`stats()` exposes summary).
- Two candidate policies behind `clock="calibrated" | "delta" | "level"`
  (default `level`, the shipped v1):
  - calibrated: threshold = quantile of collected c1 distribution
    (self-tuning after N≥30 samples; falls back to level before that);
  - delta: turn early iff (c2 − c1) below a floor AND c1 above a floor
    (fast crystallization signature), else level fallback.
- **Acceptance:** benchmark script (not a hard test) on the three canonical
  pairs × seeds 5–10: report accuracy and mean dwell per policy. Promote a
  candidate to default ONLY if accuracy ≥ level-v1 AND mean dwell strictly
  lower; otherwise level stays default and HANDOFF2 records the numbers.
  (Probe 14 already killed naive slope; do not resurrect it.)

## W-4 · Decode boundary (R-1)

`amem/decode.py`: a protocol class (`select(signature, library) -> mid`)
with the identity/cosine selector as the only implementation. The recall path
calls through it. No spatial decoding anywhere. One test asserts the boundary
exists and the default is pure selection.

## W-5 · New law tests (Phase 2 findings)

- `test_serial_position`: 5 sequential shared-field writes × ≥4 seeds —
  newest survival > middle mean, oldest > middle mean (U-curve, probe 16
  bands ±0.1); AND the clarifying test: the same 5 episodes written via the
  W-2 encoder (separated placements) show middle-age survival within 0.15 of
  newest (the U-curve is a shared-region phenomenon; separation neutralizes
  it). If the clarifying half FAILS, that is a finding — flag, don't force.
- `test_relocation_duty_of_care`: colliding pair (5,5)/(8,8) margins vs
  relocated (5,5)/(13,13): both relocated margins ≥ +0.45; incumbent margin
  under collision ≤ +0.40 (probe 16: +0.28).
- `test_cue_route` (R-2): k=12 bank, cue fractions 0.50 and 0.25, accuracy
  ≥95% each (measured 100%/100%).

## W-6 · demo_agent.py (D-5)

Scripted, runtime-agnostic: an "agent" processes 6 fake episodes
(random-embedding stand-ins), writes each via `write_episode`, then loses all
context; recovers each episode by noisy embedding via `recall_context`;
finishes with a serial procession of 3 recalled episodes via `sequence`.
Prints identity accuracy (expect 6/6) and total runtime (< 10 s).

## W-7 · Close-out

- Entire Phase 1 suite still green (amend only the baselines DECISIONS
  renumbers: dwell bands per R-3).
- `HANDOFF2.md`: state, measured numbers, deviations, and a ranked
  next-three-probes list (standing candidates: grid scaling past
  PlacementFull; clock-candidate promotion data; combo-mode value at k≤16).
- Update README with the hybrid recall diagram (embedding → id → anchors →
  stage) and the six laws + two new ones.
- **Stop.** The system rests.

## Non-goals
Real runtime integration, external vector DBs, grid scaling, performance
work, UI, and anything not listed above.
