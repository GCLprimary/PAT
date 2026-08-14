# agent + mirror — Case & Apostrophe · Build Spec (Part XV; probe 58)

**Founded on the human gate's precision ruling: 50/50.** The rows the
advisory marked incorrect were adjudicated TRUE morphology reported
by a system missing one orthographic receipt — capitalization. The
ruling is law 1 below, and this Part builds the missing channel.
**Location:** `~/alignment_field`, on the landed Part XIV. **House
rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part XV → stop.
**Reference probe:** probe58 (this folder).

**Laws this build codifies:**
1. **A hazard flag that traces to a representational gap founds a
   feature, not a filter.** (The gate's ruling, verbatim in the
   HANDOFF: the onomastic rows "need capitals and apostrophes
   anyways.") Flags are debts; this Part pays one.
2. **Case is a receipt, not styling.** Sentence-MEDIAL capitalization
   is the proper-noun signal; sentence-initial capitals are
   positionally ambiguous and counted separately. Position-conditioned
   counting, as always.
3. **New channels ride parallel artifacts.** The pinned lowercase
   corpora stay untouched at their checksums; case data is a new
   checksummed census derived from the raw cased sources.
4. **The clitic obeys the thirds.** Measured: possessive-'s
   remainders split z 392 / s 84 / IH-z 19 / AH-z 5 — voiced→z,
   voiceless→s, sibilant→IH-z, affricate→AH-z. The plural's ruler of
   thirds generalizes to its third morpheme, and the affricate
   epenthesis canary confirms itself a third time.

---

## K-1 · The case census (builder-measured; amendment pattern)

- From the RAW cased sources (retained downloads or re-fetched by the
  pinned manifests): `data/case_census.tsv` — per word type:
  medial-capitalized count, medial-lowercase count,
  sentence-initial-capitalized count. Checksummed.
- Classification {proper, common, dual} by a threshold DERIVED from
  the census (provenance in the docstring; no magic constants).
- **Gates:** census covers ≥ 95% of lexicon types by token mass;
  the four sample exemplars — pauling, jacobs, walters, adams —
  classify PROPER by medial-cap dominance; **dawning classifies
  COMMON** (the flag that fired and was rightly overruled becomes
  the battery's named case); names-pages vs census-proper overlap
  reported (agreement rate, disagreements listed).

## K-2 · The onomastic upgrade (`auditor.py`, reports)

- `audit unimorph` rows gain a `case_evidence` column; the 12
  shipped onomastic flags re-adjudicated by census; the addenda
  PR draft EXCLUDES census-proper rows — exclusion by MEASUREMENT,
  not page membership. **Gate:** zero census-proper rows in the
  draft; the reclassification delta reported.

## K-3 · The apostrophe organ (`mirror` tokenizer + pages + mining)

- **Contraction page** (~25 lines, transcribed textbook: can't →
  can+not, won't → will+not, n't/'ll/'ve/'re/'d/'m expansions),
  audited like any page; conflicts ledgered. The tiny classes
  (measured: n't 20, 'll 20, 'd 17, 've 14, 're 10, 'm 2 types)
  stay PAGE-TAUGHT, never mined.
- **The 's clitic** enters as a mined suffix family: double-locked
  pairs (measured 500 at attested ≥ 2; **gate ≥ 480**), allomorph
  table induced with the four rows of law 4 asserted (voiced→z,
  voiceless→s, sibilant→IH-z, affricate→AH-z); registration at
  pair-exact granularity with provenance `read:clitic`.
- Plural-possessive s' and the possessive-vs-is ambiguity ("the
  dog's barking") CENSUSED and flagged to the frames lane — never
  guessed. `analyze john's` → `john + 's (clitic)` with the receipt;
  `know o'clock` → atom, other-class, named.
- **No-harm:** apostrophe handling must not disturb any shipped
  battery (± 1.5); the 8,164 apostrophe types' class census
  (measured: 's 6,386; other 1,695) printed in the HANDOFF.

## K-4 · The PR drafts (unlocked by the precision grade)

- `reports/pr_drafts/cmudict_variants.md` and
  `reports/pr_drafts/unimorph_addenda.md`: contribution-ready
  documents — one-paragraph methodology, the receipted rows (top
  exemplars inline, full TSVs referenced), a reproduction command.
- **Gates:** every row carries its receipt (structural assert);
  the UniMorph draft is census-clean per K-2. **Submission is the
  human's act** — drafting only; a submit button is a non-goal.

## K-5 · Close-out

`HANDOFF.md` Part XV: the precision ruling (50/50) with the gate's
rationale quoted, the case census numbers, the clitic table, the
re-adjudicated flags, deviations, no-harm. Next-frontier ranking
(standing): the stem-allomorphy lane (census waiting), the
register-mixture corpus (C1's lesson), the phrasing slot, repos
public + Fellows email. **Stop.**

## Non-goals
Auto-submitting PRs; syntactic possessive disambiguation beyond the
census; rebuilding any pinned corpus in cased form; title-case or
acronym styling; second-order clitics (john's's); case-sensitive
BLiMP judges.
