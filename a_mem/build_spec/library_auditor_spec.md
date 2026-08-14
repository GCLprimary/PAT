# mirror + agent — The Library & The Auditor · Build Spec (probes 44–47)

**Location:** `~/alignment_field` (extends `lessons.py`, `blimp.py`,
`reading.py`; new consonance auditor; gate untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part IX → stop.
**Reference probes delivered:** probe44 (10× reading + deferral policy),
probe45 (pages 3–5 + library curve, frame-fixed reflexive judge baked in),
probe46 (tense audit — the parked feature and the new organ),
probe47 (WS-353 / SimLex rows).

**New laws this build codifies:**
1. **A page without structure is seduction with extra steps.** Rules
   about structure consult the FRAME or abstain. The proof is pinned:
   nearest-prior-noun antecedents scored 20% judged on
   principle_A_c_command (the recent-noun baseline in a page's costume);
   the strict-frame antecedent scores 87%.
2. **Pages must pass the counts.** Before a page ships, its rule faces a
   consonance audit against the pinned corpus. Founding precedent: the
   textbook class BE→ing was REFUTED at 20.2% (be takes a disjunction —
   progressive/passive/predication); MODAL→bare is a law (98.4%);
   PERF→ed strong (88.4%). Attestation examines the teacher too.
3. **Adoption needs a reason.** A deferred word resolves only by
   evidence: `unlocked by <stem>`, `read:no-such-stem` (the derived
   reading is impossible — no lexicon word has the stem's pron), or
   `read: stem <w> exists unread` (staleness, the unmet stem named).
   Never by silence, never forever.
4. **Judges abstain outside their rule.** Leak-proof by construction:
   the NPI *scope* paradigms (licensor present in both sentences) must
   report zero judged pairs, asserted.

---

## X-1 · Pages 3–5 (pinned artifacts, `data/`)

- `page_reflexives.txt` — himself/herself/itself/oneself → sg,
  themselves → pl (feature rows; existing parser).
- `page_quantifiers_existential.txt` — the rule line (existential
  *there* forbids strong quantifiers) + the strong list:
  each/every/all/most/both. Extend the page format minimally: a
  `# rule:` header line the judge reads; word rows classify
  (`each -> strong_quant`).
- `page_npi.txt` — the NPI list (ever/any/anybody/anyone/anything) +
  the licensor list (not/no/never/only/nobody/none/nothing/neither/
  whether/hardly/rarely/seldom/without + n't-suffix + sentence-initial
  aux = question). Headers carry provenance ("transcribed from grammar
  knowledge, NOT mined from BLiMP") and, where audited, the consonance
  number.
- Checksums pinned beside the existing two; the `page_checksums.json`
  fixture grows to five.

## X-2 · Judges (`blimp.py`)

- `reflexive_judge(lawbook)` — antecedent = STRICT-FRAME subject
  (sentence-initial DET/quantifier + number-known noun; each/every
  force sg) or ABSTAIN (law 1). Probe 45's fixed version is the
  reference implementation.
- `existential_quant_judge(lawbook)` — there + BE + (optional 'only') +
  quantifier; strong ⇒ violation.
- `npi_judge(lawbook)` — NPI present without licensor ⇒ violation;
  both-licensed or both-violating ⇒ abstain.
- `route()` extended: principle_A*/anaphor* → reflexive lane;
  existential_there_quantifiers* → quant lane; *npi* → npi lane.
  The no-leak law re-asserted over all 67 with the three new lanes.

## X-3 · The consonance auditor (law 2; `lessons.py` or `audit.py`)

- `audit_rule(corpus_sentences, opener_set, required_class, forms) ->
  consonance %` — the probe-46 machinery generalized.
- **Tests:** MODAL→bare ≥ 97 (measured 98.4) and PERF→ed in a band
  87 ± 2 recorded as audit references; **the BE canary**: auditing a
  hypothetical BE→ing page must come back < 30% and the LawBook must
  REFUSE to load a page whose audited rule scores below the audit
  floor (message names the number). The refutation is the fixture.

## X-4 · Deferral policy P2 (`reading.py`; probe 44)

- Pron-index over the full lexicon at session construction
  (stem-existence oracle). At defer time: no stem pron exists →
  adopt immediately, `read:no-such-stem`. At revisit: stem exists but
  unmet after 3 epochs → adopt, `read: stem <w> exists unread`.
- `looks_derived`'s len ≥ 5 guard documented as the dial (4-phoneme
  derived words become early atoms; the prune pass retires them into
  aliases once stems arrive — probe 44's seven, listed in the test's
  docstring, are truths not confabs).
- **Battery (pinned full-vocabulary stream, 37,109 words):** known ≥
  22,000 (measured 22,571); deferred-final ≤ 2,000 (measured 1,402);
  the P0 comparison recorded (14,286 stranded — the catastrophe the
  policy retires); REAL confabs 0 with the atoms-before-stems class
  counted as truthful; the trio canary asserted BY PROVENANCE:
  government/nothing = no-such-stem, market = stem-exists-unread.

## X-5 · Library-curve gates (probe 45; vendored paradigms grow to
cover the three new lanes)

- **Overall (67, forced): ≥ 64.0** (measured 64.78); the curve
  56.8 → 60.5 → 64.78 printed in Part IX.
- npi_present_1 ≥ 97 (99.0), npi_present_2 ≥ 97 (99.4),
  matrix_question ≥ 96 (98.3), only_npi_licensor ≥ 98 (99.9) — each
  with judged-accuracy ≥ 99;
- principle_A_c_command ≥ 60 (64.9) with judged ≥ 85 (87);
  anaphor_number ≥ 63 (66.8);
- existential_there_quantifiers_1 ≥ 89 (91.0), judged-acc ≥ 98 (100);
- **abstention asserted:** only_npi_scope, sentential_negation_npi_scope,
  quantifiers_2, and the principle_A paradigms outside the frame's
  reach report judged == 0 or their measured slice; principle_A_domain_2
  FLAGGED not asserted (clause-local binding — frame lane depth-2);
- no-harm: every Part VIII gate stays green at its pinned values ± 1.5.

## X-6 · Sentinel rows (probe 47) + the tense scope-note

- Vendor the three benchmark CSVs (WS353-sim/rel, SimLex-999) under
  `tests/fixtures/` with checksums and source attribution; a
  `meaning_rows` runner (window-4 PPMI + SVD-300 on pinned corpus_big,
  frequency-weighted centering) printing ρ at coverage.
- **Recorded bands, not gates:** WS353-sim 0.433 ± 0.03,
  WS353-rel 0.244 ± 0.03, SimLex 0.160 ± 0.03 — sentinels; a drift
  message names the meaning organ. The 10M-corpus frontier inherits
  these as its targets.
- HANDOFF scope-note: the tense REGISTER is parked by measurement
  (baseline unseduced at natural gaps ≤ 2; register adds nothing where
  the corpus tests it) — the audit numbers stay as law-2 references.

## X-7 · Close-out

`HANDOFF.md` Part IX: the curve, the audit table, the deferral
ledger, the sentinel rows, deviations. Next-frontier ranking
(standing): **frame depth-2** — clause segmentation (domain paradigms +
irregular_SVA_2 + SVA widening all live there) — then 10M coherent
corpus (WS-rel target attached), the lesson library continued, repos
public + Fellows email. **Stop.**

## Non-goals
Tense-register build (parked by probe), clause segmentation itself
(next campaign), GLUE/MSGS, leaderboard submission, gate changes,
gender features (anaphor_gender needs a name-gender page — future
library item, noted).
