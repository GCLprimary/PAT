# HANDOFF2 — Phase 3 build

Status: **complete**. 42/42 tests green (~48 s; the full Phase 1 suite
included and untouched except the R-3 dwell bands, which Phase 1 already
carried). `demo_cli.py` ~1 s, `demo_agent.py` ~1.2 s (target < 10 s).
The system rests.

## What was built (per the Phase 3 spec)

- **W-1 Radius channel (D-2):** mass-weighted hop-age tracking in the
  stroke engine (probe 13/14 `GaugeCap` mechanics), 9×6 = 54-dim radius
  code as the default classification signature, 25×6 = 150-dim ring×radius
  combo behind `core_mode="combo"`. 9-dim signatures still classify
  (legacy path, warns). Store format v2; v1 stores load (entries without
  radius codes classify via 9-dim only — re-write entries to upgrade).
- **W-2 Hybrid encoder (D-1/D-3/D-5):** `amem/encoder.py` (protocol-based
  embedding index + numpy implementation; write-time placement optimizer,
  max-min Chebyshev, corner-first deterministic; `PlacementFull` at the
  ~9-slot packing limit) and `amem/hooks.py` (`write_episode` /
  `recall_context`). Auto-relocation below overlap 0.45 for encoder
  placements; store-with-warning for pinned. Embeddings persist in entry
  metadata; the index rebuilds from the library on restart.
- **W-3 Clock scaffolding (D-4):** completion trajectories logged from
  every recall/sequence into a runtime buffer (`stats()["clock"]`);
  `CalibratedDwell` and `DeltaDwell` behind the flag; level-v1 default.
- **W-4 Decode boundary (R-1):** `amem/decode.py` — Selector protocol,
  CosineSelector the only implementation, recall routes through it.
- **W-5 New law tests:** serial-position U-curve (+ clarifying half),
  relocation duty of care, cue route at k=12.
- **W-6** `examples/demo_agent.py`; **W-7** this document + README.

## Measured numbers (port vs probe/DECISIONS reference)

| metric | reference | this build |
|---|---|---|
| radius classification k=24 | 90% | **90%** |
| legacy angular k=24 | 83% | **83%** |
| combo k=16 / k=24 | 100% / 88% | **100% / 88%** |
| full sweep (k=8/12/16/20/24, radius) | — | 100/92/94/90/90% |
| U-curve: newest / oldest / middle | 0.69 / 0.43 / 0.21 (std ≤ .04) | 0.69 / 0.43 / 0.21 (std ≤ .04) |
| encoder-written completion by age | no gradient expected | 0.62–0.77, no gradient — **U-curve neutralized, clarifying test passed** |
| relocation margins, collided | +0.28 / +0.11 | +0.282 / +0.108 |
| relocation margins, relocated | +0.70 / +0.56 | +0.702 / +0.557 |
| cue route k=12 @ 0.50 / 0.25 | 100% / 100% | 100% / 100% |
| encoder end-to-end σ=0.05/0.10/0.20 | ≥95% at σ≤0.10 | 100% / 100% / 100% |

## Clock benchmark (W-3 acceptance — promotion inequality)

3 canonical pairs × seeds 5–10, 10 measured turns each, 12-turn warmup:

| policy | mean accuracy | mean dwell | hard pair |
|---|---|---|---|
| level-v1 | 98% | 3.19 | 95% |
| calibrated (median-c1) | 97% | **1.00** | 90% |
| delta | 98% | 3.19 | 95% |

**Verdict: level-v1 stays default.** Calibrated fails the accuracy half of
the inequality (97 < 98, hard pair 95→90); delta fails the dwell half —
its early-turn floors never fired, the same failure shape as probe 14's
naive fast-exit. Note for the next probe: calibrated buys a 3.2× dwell
reduction for one point of mean accuracy — the interesting region is
between the median-c1 threshold and level, not at either end.

## Deviations (all deliberate, none silent)

1. **Placement is a separation optimizer, not probe 15's hash.** D-1
   ruled the hash out (42% round-trip); the spec's "maximizing distance"
   is implemented as greedy max-min Chebyshev with corner-first
   deterministic tie-break — it reproduces the 9-slot Chebyshev-5 packing
   exactly, verified by test.
2. **The encoder is shape-aware.** Probe 15 silently clipped pattern
   cells that fell off the lattice (LINE at cx=14 reaches x=23); the
   package refuses to store a clipped pattern, so candidates that would
   clip are excluded from placement instead.
3. **The relocation loop withdraws a flagged write before retrying** —
   otherwise the withdrawn candidate's own imprint contaminates the next
   candidate's overlap report. (The probes never implemented the loop;
   this is the first real implementation of D-3.)
4. **Vectorized hop-age transport**, relying on the injectivity of
   z → z/(1+i); injectivity is asserted at map construction (integer
   check, decision-zone clean).
5. **Combo code is 150-dim** (25×6 with a structurally dark center) —
   probe 14's header said "144" counting live cells only; the reference
   array was 25×6. Same object.
6. **Benchmark's calibrated policy used min_samples=12** (warmup-sized)
   rather than 30, so self-tuning is reachable inside the benchmark's
   turn budget; the shipped default stays 30.
7. **`wipe()` clears hop ages** (the reference GaugeCap never wiped —
   fresh engines per probe; the persistent stage needs flat nothing to
   mean age-0 nothing too).
8. **Calibration is untouched by W-1**: the flat-field portrait remains
   the 9-dim absolute-gauge measurement (law 4). Binned calibration was
   not specified and was not built.

## Observations

- The radius channel's gain concentrates exactly where D-2 said:
  same-angle identities (legacy's k=20→24 slide 85→83% becomes 90→90%).
- Write-time relocation visibly works in the demo agent: episode 6
  withdrew two flagged placements before settling at overlap 0.39.
- Completion-confidence remains a weak level signal (0.0–0.86 across
  successful recalls in the demo) — consistent with Phase 1 and with the
  calibrated policy's accuracy dip.

## Ranked next three probes

1. **Grid scaling past PlacementFull.** The 23-lattice packs ~9 episodes;
   everything else in the system (selector at 90% @ k=24, embedding index
   unbounded) is ready for more. Probe: does a 31- or 47-lattice preserve
   the sieve/survival/budget laws and raise the packing limit
   proportionally? (Standing candidate; now the binding constraint.)
2. **Clock promotion, second attempt.** The benchmark localizes the
   target: a threshold between median-c1 and level that keeps the hard
   pair ≥ 95% while cutting dwell below ~2. Candidates: higher quantile
   (0.75), or pair-difficulty-conditioned thresholds using the stored
   overlap matrix (the write-time overlap already predicts which tenants
   are hard).
3. **Combo-mode value at k ≤ 16.** Combo is exactly 100% through k=16 and
   dilutes past it. Probe: auto-switching core_mode on library size
   (combo ≤ 16, radius above), and whether combo's ring cells buy
   anything once the radius channel exists at small k.

The system rests.
