# a_mem — Agent Memory System

Associative memory for software agents, built from three organs with
empirically measured roles (Alignment Field probe campaign, suites 1–16):

- **The Field ("the stage")** — a normalized, homeostatic 23×23 particle
  lattice. Activation renormalizes to sum = 1 every tick; all thresholds are
  multiples of the uniform share 1/N. "Nothing" is the flat state, not zero.
  Single-occupancy reconstruction workspace.
- **The Anchor Library ("where")** — per-memory sparse skeletons written in
  the absolute gauge (fixed thresholds, real zero) via quiet dynamics.
  Exact, durable, and the primary store.
- **The Core ("who")** — a compact identity code per memory produced by the
  parity-sieved inward contraction (division by (1+i) on the lattice,
  integer arithmetic only). Since Phase 3 the code is **radius-channeled**:
  9 core cells × 6 hop-age bins (54-dim), carrying angle AND radius of the
  spiral journey. Used **only** for classification. Never decoded into the
  field.

## Hybrid recall (Phase 3, D-1)

Episodes pair an external embedding with a lattice identity. Matching
happens in embedding space; the lattice does completion:

```
  write:   embedding ──> placement optimizer ──> constellation ──> stage
              │          (write-time ONLY,        anchors + 54-dim code
              │           max separation, D-3)    into the library
              └──────────> embedding index (id-keyed)

  recall:  noisy embedding ──> nearest neighbor ──> episode id
                                                        │
           reconstruction <── field completes <── half-anchors deployed
                              (page-turned stage)
```

The recall path **never re-derives placement** — probe 15 measured that
hash-placement round-trips at 42% under noise; embedding-space matching
plus id-keyed anchor recall runs at 100%.

## Design laws

1. **Residency = 1.** One memory on the stage at a time. Two residents blend
   irrecoverably (margin +0.94 → +0.005 measured).
2. **Page-turn is mandatory** for serial recall. Hot eviction is impossible
   (6/6 measured failures); every tenant change flattens the stage first.
3. **The core selects; it never paints.** Spatial decoding of the signature
   into the field degrades recall. Selection goes through the decode
   boundary (`amem/decode.py`); the only shipped selector is pure
   nearest-cosine.
4. **Calibration is an absolute-gauge operation.** The normalized gauge
   cannot see a plenum.
5. **Exact arithmetic in the harness.** Alignment certification uses squared
   integer distances only; the inward map uses integer division only after
   the parity check. No floats in any alignment or contraction decision.
6. **Purity ceilings are set at write time.** Overlapping stored patterns cap
   recall distinguishability permanently. The encoder auto-relocates below
   the 0.45 danger line; pinned placements store with a recorded warning.
7. **Serial-position law** (Phase 2): sequential writes onto a *shared*
   field produce primacy + recency (newest 0.69, oldest 0.43, middle 0.21);
   per-episode placement through the encoder neutralizes it.
8. **Collision contaminates the incumbent** (Phase 2): a colliding write
   damages the resident identity's margin too (+0.70 → +0.28). Relocation
   is duty of care, not preference.

All eight are enforced by the test suite — including tests that assert the
*failure* of hot eviction and the *blindness* of the normalized gauge.

## Install & run

```bash
pip install -e .
python examples/demo_cli.py         # core loop, ~1 s
python examples/demo_agent.py       # hybrid agent loop, ~1 s
python examples/benchmark_clock.py  # W-3 dwell-policy benchmark, ~40 s
python -m pytest tests              # full regression suite, ~50 s
```

(The demos also run from a fresh checkout without installing.)

## Quickstart

```python
from amem import Memory, EpisodeHooks

# lattice-level API
mem = Memory(grid=23, seed=7, path="~/a_mem/store")
mid = mem.write({(3, 3), (6, 3), (3, 7), (6, 7), (4, 4), (5, 5), (6, 6)})
rec = mem.recall(signature=sig54)      # 54-dim radius code (9-dim warns)
rec = mem.recall(cue=partial_cells)    # partial-anchor cue
rec = mem.recall(mid=mid)              # known identity (the hybrid route)
seq = mem.sequence([m1, m2, m1], dwell="adaptive")
mem.calibrate(); mem.stats(); mem.forget(mid)

# agent-level API (runtime-agnostic hook pair, D-5)
hooks = EpisodeHooks(mem)
mid = hooks.write_episode(embedding, payload_meta={"topic": "..."})
rec = hooks.recall_context(noisy_embedding)   # embedding -> id -> anchors
```

`Memory(core_mode="combo")` enables the 150-dim ring×radius code for small
libraries (100% through k=16). `clock="calibrated" | "delta"` selects the
candidate dwell policies (level-v1 remains default — see
`examples/benchmark_clock.py` and `HANDOFF2.md`).

## Layout

```
amem/
  constants.py      # the validated operating point (all numeric canon)
  harness.py        # exact-int alignment certification, offsets, shifts
  contraction.py    # parity sieve + inward map + ring/core indices (int-only)
  field.py          # normalized-gauge stage engine + hop-age radius channel
  absolute.py       # absolute-gauge anchor writer + calibration
  library.py        # (codes, anchors, metadata) store, JSON persistence v2
  clock.py          # page-turn; fixed/level/calibrated/delta dwell policies
  decode.py         # the decode boundary (R-1): selection only, ever
  encoder.py        # write-time placement optimizer + embedding index
  hooks.py          # write_episode / recall_context (D-5)
  api.py            # Memory: write / recall / sequence / forget / stats
tests/              # 42 tests; probe baselines and all eight laws as assertions
examples/           # demo_cli, demo_agent, benchmark_clock
```

## Regression baselines (port vs probe reference)

| metric                          | probe reference | this build |
|---------------------------------|-----------------|-----------|
| sieve theorem (saturated)       | 264 / 264       | 264 / 264 |
| aligned 7-pt quiet survival     | 100% full mass  | 100%, mass 7.0 |
| selector (legacy) k=3 / 8 / 12  | 100 / ~90 / ~79% | 100 / 94 / 79% |
| radius channel k=24             | 90%             | 90%       |
| combo k=16 / k=24               | 100 / 88%       | 100 / 88% |
| autonomous recall margin        | +0.645          | +0.630    |
| residency margin k=1 → k=2      | +0.94 → +0.005  | +0.943 → +0.004 |
| U-curve newest / oldest / middle| 0.69 / 0.43 / 0.21 | 0.69 / 0.43 / 0.21 |
| relocation margins (collided → relocated) | +0.28 → +0.70 | +0.28 → +0.70 |
| cue route k=12 @ 50% / 25% cues | 100% / 100%     | 100% / 100% |
| encoder end-to-end σ ≤ 0.10     | ≥ 95%           | 100%      |

## Measured limits

Placement capacity at grid 47 (encoder zone 2–37, Chebyshev-5 separation)
is **shape-dependent: 39–44 episodes** — measured 41 with mixed
constellation/line shapes (mirror probe 22B / S-3). Cross-modal recall
holds 100% right up to `PlacementFull`; crowding below the placement
ceiling is a non-issue. Grid scaling past the ceiling remains the top
standing probe.

History: `HANDOFF.md` (Phase 1), `build_spec/DECISIONS_final.md` (Phase 2),
`HANDOFF2.md` (Phase 3 close-out, deviations, next probes).

The system rests.
