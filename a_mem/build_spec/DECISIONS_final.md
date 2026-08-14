# DECISIONS.md — Phase 2, FINAL

Phase 1: ACCEPTED (29/29 independently re-run; contraction hand-verified).
Phase 2 probes: suites 13–16. Every ruling below is probe-backed.

**R-1** — Decode path: keep a reintroducible module boundary (`amem/decode.py`
protocol, identity-only default). No implementation in Phase 3.

**R-2** — Cue-route: probed on the shipped package at k=12 — 100% at 50% cues,
100% at 25% cues. Ship the acceptance tests with those baselines.

**R-3** — Dwell baselines amended to statistical bands: hard pair (overlap
0.62) dwell 1 ≈ 77%, dwell 2 ≥ 90% across seeds.

**D-1** — Payload encoding: HYBRID, sharpened by probe 15's failure (hashed
placement round-trip = 42% at sigma 0.05; recall must never re-derive
placement). Embedding matching happens in embedding space (nearest neighbor)
→ episode id → a_mem anchor recall (the probe-8 route, 100%). The encoder is
write-time-only placement optimization.

**D-2** — Capacity: RADIUS CHANNEL (hop-age bins). Probe 13/14: radius-alone
90% at k=24 (baseline 83%); ring-24 88%; ring×radius combo 100% through k=16
but 88% at 24 (dilutes at scale). Radius is the mechanism; combo is an
optional small-library mode.

**D-3** — Separation: auto-relocate below overlap 0.45 when the encoder
places; store-with-warning when the caller pins. Probe 16: colliding pair
(0.62) margins +0.28/+0.11 — collision damages the INCUMBENT too; relocated
(0.23) margins +0.70/+0.56. Relocation is duty of care, not preference.

**D-4** — Clock v2: slope-as-level FAILED (probe 14: fast-exit never fired;
hard pair dipped to 90%). Phase 3 ships calibration collection plus two
candidate policies behind a flag; level-v1 remains default unless a candidate
beats it (see spec acceptance).

**D-5** — Integration: modular, runtime-agnostic hook pair
(write_episode / recall_context). User's own agent is TBD; nothing binds to a
specific runtime.

**D-6** — Folded into D-2 and D-4. Ratified.

**New laws from Phase 2 probes (become tests):**
- Serial-position law: sequential writes onto a shared field produce
  primacy+recency (6 seeds: newest 0.69, oldest 0.43, middle 0.21, std ≤0.04).
  Per-episode placement is expected to neutralize it (clarifying test).
- Collision contaminates the incumbent, not just the newcomer.
