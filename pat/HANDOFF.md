# HANDOFF — agent (the shell)

Status: **complete**. 7/7 battery tests green (~80 s), `demo_creature.py`
runs the life story in 26 s, the REPL works end to end. Stopping per
spec — the creature rests knowing things it was taught, on disk, with
receipts.

## What was built

The spec, whole: `agent/loop.py` (the heartbeat: perceive → segment →
recall → act → respond → write-on-teachable-moments, a_mem-backed
persistence, restart recovery, provenance log), `agent/repertoire.py`
(five verbs behind the Router protocol, the alien law),
`agent/cli.py` (the honest REPL), pinned fixtures with checksums
(`data/fixtures/`, generated once by `scripts/make_fixtures.py`),
the three batteries plus the restart and alien hard tests,
`examples/demo_creature.py`. a_mem and mirror imported, untouched.

## Measured numbers

The table is in README.md. Headlines: the learning gap lands at
**exactly 60 points** (the probe's number) with zero confabulation in
both arms and every ON gain traced to a logged refusal-plus-confirmation
write; composition holds 92–100% per clause at every input length with
16/16 aliens refused and 100% clean-clause containment; teach→use 15/19
(probe 14/19, same pinned 19 threads); restart recovery 5/5.

## Deviations and findings (flagged)

1. **The shuffled-order protocol, third sighting.** Probes 33/34 build
   their base maps from probe-19's module-level pairs — which are
   SHUFFLED in place. Building fixtures from the raw mining order
   instead shifts the per-base suffix order, the teach-pair forms, and
   the thread outcomes (measured: teach→use 13/19 raw vs 15/19
   shuffled). Same class as the probe-20 sampling note in mirror's
   HANDOFF. The fixture generator now uses `Transform.fit`'s exposed
   shuffled order; anyone rebuilding fixtures must too.
2. **"Analyze relatives" read as written (plural).** The restart test
   counts a taught base as recovered if EITHER of its derived forms
   analyzes correctly. A modal-allomorph mismatch on one form (e.g.
   't'-final bases whose -ed takes epenthetic IH-d, which the modal
   SEAM proposal cannot represent) is honest refusal physics, not
   amnesia — and the restart test's subject is memory. Allomorph
   coverage lives in the batteries' statistics, where it is measured,
   not asserted per-form.
3. **PyPI namespace collision, recorded for operators:** `a-mem` is a
   real (unrelated) package on PyPI. A backgrounded
   `pip install -e mirror` with default index access resolved
   `a-mem>=0.2.0` from PyPI and clobbered the local editable's
   metadata mid-build. Local editable installs in this stack should use
   `--no-build-isolation --no-index`. (Cleaned up; environment verified.)
4. **Input hygiene at the perception boundary:** PowerShell pipes
   prepend a UTF-8 BOM, which made the first verb alien
   (`'﻿know'`). `segment()` strips BOM and zero-width characters —
   the one place the closed world touches a real terminal.
5. The `walk` verb derives its prompt from the first attested corpus
   sentence containing the origin word (the spec left prompt derivation
   open). Word-level endpoints make shakier itineraries than V-3's
   category centroids — closure rises but not always monotonically;
   the journey-verb test asserts final > first, per the V-3 gate shape.
6. Suffix-side SEAM proposals only in `analyze` (probe 33/34 protocol);
   the loop's L3 prefix layer exists in mirror and can attach behind the
   Router without touching the shell — ranked, not built.

## Next-frontier ranking

1. **Stage integration** — multi-topic sessions: the dual-threshold
   stage segmenting long inputs so the creature holds topic through
   interruptions *in conversation*, not just in batteries.
2. **Richer routing behind the Router protocol** — synonyms, argument
   patterns, maybe the L3 prefix layer in `analyze`.
3. **The phrasing slot** (D-5, still open by design): organ outputs are
   structured records; a phrasing organ would render them — the slot
   stays empty until a probe earns it.
4. **Open-world vocabulary growth** — `remember` currently requires the
   CMU lexicon; growing past it is a new physics question (the a_mem
   grid dial is the capacity side of the same frontier).

**Stop.** The creature rests — taught, persistent, and honest about
every one of its refusals.
