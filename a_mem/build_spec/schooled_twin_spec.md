# mirror + agent — The Schooled Twin · Build Specification (probes 42–43)

**Location:** `~/alignment_field` (new `mirror/lessons.py` + `mirror/blimp.py`,
small extensions to `agreement.py` and `agent/reading.py`; gate untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part VIII → stop.
**Reference probes delivered earlier:** probe42 (harness + lesson line),
probe43 (the irregular page). BLiMP source: github.com/alexwarstadt/blimp.

**New laws this build codifies:**
1. **Pages are law-class artifacts.** A page is readable rows with
   provenance `lesson:<page-name>`, pinned as a data file with checksum
   (the artifact law applied to instruction). Placement in the ladder:
   pages override induced *classifications* (inferences — e.g. the number
   lexicon classing 'men' singular because men+s exists is derivation
   evidence misread as number evidence), and NEVER override attested
   *pairs* (observations). Every override is a ledgered conflict.
2. **Lessons never load silently.** Page-load reports its conflict ledger;
   an empty ledger on a page known to correct the lexicon (page #2) is
   itself a failure.
3. **Judgment stays selective.** Judges emit (verdict, judged?) so
   coverage is always visible; forced-choice fallback exists only inside
   benchmark mode, and selective accuracy (accuracy-at-coverage) is
   reported beside every forced number.

---

## L-1 · `mirror/lessons.py` — the LAW class

- `Page(name, rows, provenance)` — rows are readable (word → feature, or
  rule literals); `LawBook(pages)` with:
  - `number_of(word)` — page-first over `agreement.build_number_lexicon`
    output (wraps, does not modify, `agreement.number_of`);
  - `conflicts()` — every page entry whose induced classification
    disagrees, as (word, page-says, induced-says) triples;
  - `export()` — human-readable, mirroring `AllomorphTable.export`.
- **Ship two pinned pages** (data files + checksums):
  `data/page_demonstratives.txt` (the one-line lesson: this/that → sg,
  these/those → pl) and `data/page_irregular_plurals.txt` (~50 textbook
  pairs — transcribed from grammar knowledge, NOT mined from BLiMP; say
  so in the file header).
- **Tests:** conflict ledger contains ≥ 3 entries and names
  people/men/children among them, each verified against the induced
  lexicon (the lesson-corrects-induction canary); page checksums pinned;
  `LawBook.number_of` falls through to induced for unlisted words
  (regression: `agreement.number_of` results unchanged off-page).

## L-2 · `mirror/blimp.py` — the harness as a module

- Loader for BLiMP paradigm jsonl; `scripts/fetch_blimp.py` (shallow
  clone) + a pinned checksum manifest for all 67 files; the 14 agreement
  paradigms VENDORED under `tests/fixtures/blimp/` (artifact law — tests
  never fetch).
- Trigram scorer (stupid backoff, α = 0.4) built on the PINNED
  `corpus_big.txt` (checksum asserted at build).
- Judges: `demonstrative_judge` (LawBook-backed, adjective gap ≤ 3) and
  `sv_judge` v1 (single-token verb diff + det-N subject frame — its
  strictness is a known coverage gap, documented, not patched here).
- `run(paradigm) -> (forced_acc, judged_n, judged_acc)`;
  `run_all()` prints the probe-43-style table.

## L-3 · Batteries (pinned fixtures; probe-43 reference values)

- **Overall (67 paradigms, forced):** ≥ 59.5 (measured 60.5); trigram-only
  recorded in a band 56.8 ± 0.7 (it is the baseline row, not a gate).
- **Paradigm gates:** dn_agreement_1 ≥ 86 (88.6); dn_irregular_1 ≥ 88
  (91.6) with judged-accuracy ≥ 98% (100%); dn_irregular_2 ≥ 93 (96.0)
  with judged-accuracy ≥ 98% (100%); with_adj_irregular_1 ≥ 75 (79.3);
  irregular_SVA_1 ≥ 65 (70.1).
- **No-harm:** regular dn paradigms within 1.5 points of probe-43 values;
  every non-agreement paradigm's forced accuracy equals trigram-only
  (the judges must not leak outside their scope).
- **Seduction control:** distractor paradigms at trigram-only ≤ 50%
  (measured 46.5/47.7) — the control proving the attractors are real;
  message per house idiom if it drifts.
- **Coverage-gap flag:** irregular_SVA_2 recorded at trigram baseline
  with a named flag (subjects without determiners — frame lane), not
  asserted.

## L-4 · The schooled twin surface (`agent/reading.py`)

- `ReadingSession.study(page)` — ingests a Page; every listed word enters
  `known` with provenance `lesson:<page>`; conflicts ledgered exactly as
  reading's census is; provenance ledger gains its FOURTH class:
  birth / taught / read / **lesson**.
- **Test:** after `study(page_irregular_plurals)`, the session reports
  'men' as plural with lesson provenance AND the conflict against its
  induced classification in the same breath; `test_survives_restart`
  extended: lesson provenance survives death.
- Demo addition (one act in `demo_reading.py`): the creature studies the
  page aloud — "50 lines read; 4 conflicts with what I'd inferred;
  corrections ledgered" — then answers one number question citing the
  lesson.

## L-5 · Close-out

`HANDOFF.md` Part VIII: numbers, deviations, the conflict ledger printed
in full, and the next-frontier ranking (standing: the LESSON-LIBRARY
CURVE — pages vs paradigms conquered, the plot only this architecture
can draw; SVA frame widening for the last dead paradigm; 10M coherent
corpus; subject-ID at scale; WS-353/Morfessor; repos public + Fellows
email). **Stop.**

## Non-goals
GLUE/MSGS, leaderboard submission, judges beyond the two shipped, page
auto-extraction from prose (the "read a real grammar book" dream — a
future probe, not this build), gate changes, new REPL verbs.
