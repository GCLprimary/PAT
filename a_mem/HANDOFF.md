# HANDOFF — Phase 1 build

Status: **complete**. 29/29 tests green (~14 s), demo end-to-end in ~0.7 s,
wheel builds. Stopping here per spec; no Phase 3 work started.

## What was built

The full spec layout: `amem/` package (constants, harness, contraction,
field, absolute, library, clock, api), 8 test files, `examples/demo_cli.py`,
`pyproject.toml`. Reference behavior ported from `probes/gauge.py` (the
dual-gauge machine, canonical spray-proportional deviation included) with
the stage matching `GaugeV5(decode_amp=0)` — the configuration every
winning protocol (probes 8–12) actually used.

Port fidelity, measured:

| metric | probe reference | port |
|---|---|---|
| sieve split, saturated field | 264/264 | 264/264 |
| aligned quiet survival (250 ticks) | 100% at full mass | 100%, mean mass 7.0 |
| random 7-pt survival | ~20% | passes ≤45% gate |
| selector k=3 / k=8 / k=12 | 100 / ~90 / ~79% | 100 / 94 / **79% exactly** |
| autonomous recall margin | +0.645 | +0.630 |
| residency margin k=1 → k=2 | +0.94 → +0.005 | +0.943 → +0.004 |
| budget across (v,d) corners | ~10–12% | 0.106 / 0.136 / 0.121 |
| confidence validity r | ~+0.40 | passes ≥ +0.25 gate |
| calibration portrait | ring + dark center | uniform ring (2.7×8), center 0.0 |

## Deviations from the reference probes (all deliberate)

1. **Outpour never paints the signature, in either gauge.** The plain
   `gauge.py` machine had a center-blob core glow in `_outpour_tick`; the
   canonical protocols all ran `GaugeV5(decode_amp=0)`, which skips it.
   Law 3 is now structural: there is no decode path in the codebase at all.
   The absolute engine's beats are unused by every canonical protocol
   (anchor writes are quiet-dynamics; calibration is pure indraw), so this
   changes nothing measured.
2. **Absolute indraw clamps activation at 1.0** (as `engine.py` did;
   `gauge.py` omitted the clamp but never ran absolute indraw in anger).
   Without it a plenum cell reaches 0.6 + 0.45 = 1.05 and the bounds
   invariant breaks. Calibration portrait shape is unaffected.
3. **Calibration runs on the absolute engine** (spec law 4). Probe 9's F1
   measured the plenum on the *normalized* machine, where it is invisible
   (uniformity sits below relative thresholds — its flat signature is
   exactly zero). That blindness is now itself a test
   (`test_calibration.py`); the ring+dark-center portrait comes from the
   absolute plenum.
4. **Vectorized indraw transport** (precomputed integer maps +
   `np.add.at`, same accumulation order) and **hoisted sustain**
   (algebraically identical to the per-offset `where` loop). Statistical
   baselines unaffected; bit-exactness with the probe scripts was not a goal —
   determinism under a seed within this build is tested.
5. **Persistence round-trip test lives in `test_coherence.py`** — the spec's
   8-file test layout was kept rather than adding a ninth file.
6. **Hard-pair dwell numbers.** The overlap-0.62 pair is (5,5)–(8,8)
   (measured 0.623). Averaged over seeds 5–10: dwell 1 ≈ 77% tenancy,
   dwell 2 ≈ 90%+. "Needs dwell 2" reproduces directionally; the clean
   100%-at-dwell-2 figure holds only at the canonical seed. The test
   asserts the aggregate (d1 ≤ 0.9, d2 ≥ 0.85, d2 > d1).
7. **Writes run on the persistent stage** (reset to zero, stamp, 8 beats),
   equivalent to the probes' fresh-engine-per-imprint modulo RNG stream.
   Recall and sequence page-turn the same stage — law 2 is in the API path,
   not just the physics.
8. **Cue-route selection** matches the cue mask against stored anchor
   skeletons by cosine (the spec names "partial anchors" as a selecting cue
   but no probe measured this route; the signature route is probe 8's
   protocol exactly). Works cleanly at library sizes tested.

## Observations worth carrying to Phase 2

- **Confidence is valid but weak as a level.** Absolute anchor-completion
  values ranged 0.14–0.83 across patterns in otherwise-successful recalls
  (correlation with purity confirmed at r ≥ +0.25). With θ = 0.7 the
  adaptive clock frequently runs to its cap of 4 on items that dwell-1
  handles — the spec's "over-dwells on easy items," observed here too.
  Supports the completion-slope-at-beat-1 candidate for clock v2
  (Phase 2 decision #4).
- **Selector k=12 lands at exactly 79%** with the same angular-collision
  structure implied by the spec — the radius channel (decision #2) remains
  the obvious lever.
- **Write-time overlap reporting works** (demo shows 0.12 max for the
  3-pattern set; the danger threshold 0.45 is enforced as a flag only,
  per Phase 1 scope). Decision #3 (reject / relocate / warn) is ready to
  slot into `Memory.write` — the report is already computed there.
- The anchor skeletons for the canonical patterns are tiny (6–7 cells).
  Cues of 3 cells complete to ~60-cell reconstructions reliably. Sparser
  fractions were not re-probed in this build (probe 5/6 report the curve).

## Open questions noticed during the build

1. Should `recall(signature=...)` optionally use flat-field-corrected
   cosine? The portrait is stored (never painted), but classification is
   raw cosine (probe 8's protocol). Probe 9 F2 tested a corrected variant;
   its measured benefit at k=12 is not recorded in the probe files I had.
2. `sequence` judges the stage holder against every stored imprint each
   step (O(library) cosines per item). Fine at Phase 1 scale; a Phase 3
   capacity target of ≥25 identities may want the judgment optional.
3. The normalized stamp behaves differently from a zero field (write path)
   vs a flat field (deploy path) — both match probe protocol, but the
   asymmetry deserves a sentence in any future payload-encoder design:
   imprints assume a *dark* stage, cues assume a *flat* one.
4. `Memory(grid=...)` is honored throughout (maps are grid-parameterized),
   but every validated number is grid-23. Other grids are unprobed physics.

## Suggested Phase 2 agenda

Exactly the spec's six decisions; nothing found during the build changes
their framing. Decision #1 (payload encoding) remains the critical one —
everything in this build treats patterns as given constellations, and the
overlap/purity machinery is ready to enforce whatever separation policy
the encoder needs.
