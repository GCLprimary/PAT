# mirror — Scaling Build Specification (probe-22-backed)

**Location:** `~/mirror` (extends the accepted build; a_mem untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile. Build, `HANDOFF.md`, stop.

**What probe 22 rewrote (read before building):** the scaling menu assumed the
meaning organ was data-starved. Measured: 5× corpus moved suffix-offsets only
+0.022→+0.026, while **SVD-300 compression on the SAME 1M corpus tripled them**
(+0.066/+0.076/+0.082, relatedness 20/20). And stacking mismatched genres
(Brown+Gutenberg+Reuters) *hurt* at 5M (+SVD relatedness 17/20, -ing/-s down).
Lessons, now law-shaped: **compression before corpus; coherence before volume.**

## S-1 · `meaning.py`: SVD densifier
Truncated SVD on the PPMI matrix (economy SVD, top-k=300, rows re-normalized).
Count-derived linear algebra — no gradients; law-scope note from the mirror
spec applies verbatim. Dense vectors become the default meaning space;
`dense=False` keeps sparse PPMI available.
- **Acceptance (1M Brown, recipe frozen):** suffix-offset agreement ≥ +0.05
  for each of -ed/-ing/-s with |random floor| ≤ 0.01 (measured
  .076/.066/.082); relatedness ≥ 18/20 (measured 20/20); rung tests from the
  accepted build still green with dense meaning blocks (re-run W-5 with
  dense=True; ≥ 90% both directions).

## S-2 · corpus registry + coherence policy
`meaning.build_corpus(sources=[...])` becomes a registry: each source built and
normalized separately under the contract; models may be built per-source or
combined explicitly. NO silent stacking.
- Ship a `coherence report`: for each source pair, relatedness-triple accuracy
  of combined vs best-single (probe 22's instrument). Combined is adopted only
  where it is ≥ best-single − 1 triple; otherwise per-source models stand.
- **Acceptance:** Brown-only remains the default; the report reproduces the
  probe-22 finding (stacked 5M underperforms Brown+SVD on ≥ 1 metric) as a
  regression sentinel — if stacking ever *helps* under this recipe, that's a
  finding to flag, not silently adopt.

## S-3 · rung crowding + placement documentation
No new mechanism (probe 22B: 39/39 and 38/39 at the grid-47 placement ceiling —
crowding is a non-issue below the ceiling). Work: document measured placement
capacity as **shape-dependent (39–44 at grid 47)** in a_mem-facing docs, and add
a mirror test that fills to PlacementFull and asserts cross-modal recall ≥ 90%
at whatever N placement allows (dense meaning blocks).

## S-4 · breadth (prefixes/compounds) — GATED, DO NOT BUILD
Menu item 2 has no probe behind it yet. The probe is defined (mine prefix
pairs un/re/dis/mis/pre where derived pron ENDS with base pron; SEAM binding
prefix-side; loop gains an L3) and runs in the next session. Building ahead of
the probe violates the house rule; this item exists so HANDOFF can rank it.

## S-5 · close-out
`HANDOFF.md`: measured numbers, deviations, and the next-probes ranking
(standing: prefix-breadth probe; dense-space crowding at grid > 47; coherent
large single-register corpus — e.g. a Wikipedia build — as the S-2 registry's
first big source, LOCAL ONLY, licensing noted).

## Non-goals
Prefix/compound implementation (S-4 gate), grid scaling beyond documentation,
agent shell, performance, machinery variants.
