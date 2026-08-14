# pat — The Front Door · Build Spec (Part XVI; release packaging)

**No new capabilities. This Part renames, documents, licenses, and
manifests — Pat's public face.** **Location:** `~/alignment_field` →
becomes `~/pat`. **House rules unchanged**, plus this Part's own
first law: **the suite is the rename's gate** — every test green
post-rename is the definition of done. Build → `HANDOFF.md` Part XVI
→ stop.

**Laws:**
1. **The suite is the rename's gate.** No behavior changes; 111+44+3
   (plus growth) green after the move, or the move isn't done.
2. **Bytes before paths.** Every pinned artifact's checksum is
   byte-identical after the move; manifests are re-pointed to new
   paths and re-verified. A changed hash anywhere is a stop-the-line
   flag.
3. **The README is the entry card.** One mechanism sentence under
   every number; no claim without a battery behind it; the honest
   boundaries stated unprompted.
4. **History ships.** The probes and the sixteen-Part HANDOFF are
   the method's fossil record — half the product. They go public
   with the code.

---

## R-1 · The rename

- Umbrella `alignment_field/` → **`pat/`**. Inner organs KEEP their
  names (a_mem, mirror, workshop, sensor) — they have histories and
  the HANDOFF cites them; the README's anatomy map translates.
- The shell package `agent/` → **`pat/`** (the shell IS Pat):
  `import pat`, and a console entry point **`pat`** that opens the
  REPL. All imports, paths, scripts, and fixtures updated.
- **Gates:** full suites green; `grep -r alignment_field` returns
  ZERO hits outside HANDOFF history and this spec; every manifest
  re-verified byte-identical (law 2); fresh-clone smoke test:
  `pip install -e .` then `pat`, and the REPL answers the live-log
  lines — `analyze government` → the elision refusal with receipt,
  `know side` → the biography, `analyze brillig` → the alien
  refusal. The demo installs itself.

## R-2 · The README (the front door itself)

Order: the descriptor line — **"Pat — a provenance-complete,
geometric smart-controller agent. Pat never gives pat answers."** —
then the LIVE TRANSCRIPT (the user's session log, lightly cleaned,
verbatim lines), then the entry card (numbers + mechanism
sentences: BLiMP forced + selective, inflection, wug, discovery,
auditor yields, zero-confab record), then the anatomy map (one line
per organ), quickstart (clone → install → `pat`), the four laws in
plain language, and an **honest boundaries** paragraph: closed
word-world; sources can be wrong but errors wear their provenance;
what Pat is not (not fluent, not general, not a chatbot). Gate: a
reader who runs the quickstart reproduces one receipt end-to-end.

## R-3 · License and attribution

- `LICENSE` (human's pick; MIT default), `NOTICE` for vendored data:
  CMUdict (its BSD-style license), UniMorph (CC-BY-SA, cited),
  Gutenberg (public domain, source list). Fetch scripts + pinned
  checksums for any artifact too large to ship; target repo ≤ 50 MB
  with everything else one pinned fetch away.
- `reports/pr_drafts/` ship in place; `PROPOSAL.md` ships (the
  authorship ledger is a feature); `.gitignore` for caches/outputs;
  `CHANGELOG.md` seeded from the sixteen Part titles.

## R-4 · The openness toggle

Default per the human's word: **full Pat public.** If the gate
elects staged openness instead, the shell subpackage moves to a
private overlay and the README says so plainly — one flag in the
spec, flipped only by the human, recorded in the HANDOFF.

## R-5 · Close-out

`HANDOFF.md` Part XVI: the release manifest (tree, artifact
checksums, README hash), the smoke-test transcript, deviations.
Frontier ranking (standing): the Fellows email (enclosures: repo
link, live transcript, PR drafts), then the stem-allomorphy lane,
the register-mixture corpus, the phrasing slot. **Stop.**

## Non-goals
New capabilities or verbs; CI pipelines (a note in the README
suffices); auto-publishing or auto-submitting anything; the Fellows
email itself — that send button has exactly one owner.
