# mirror + agent — Depth-2 & The Compressed Frontier · Build Spec (Part XII; probe 54)

**Location:** `~/alignment_field`, on the landed Part XI. **House rules
unchanged:** tests before features; acceptance by inequality; flag,
don't reconcile; build → `HANDOFF.md` Part XII → stop.
**Reference probes:** probe54 (delivered, this folder). Probes 38 and
22-style machinery are already archived in-repo and are cited below.

**PROCESS AMENDMENT (the ladder recedes one rung, deliberately):**
items C-1 and S-0 are builder-executed measurements against
acceptance inequalities written here. The probe design is fully
specified; the builder runs it, reports the numbers, and flags —
never reconciles — anything outside a band. Judgment stays at the
gate; execution moves down one rung. This is the receding-ladder
invariant operating as designed, and the HANDOFF should say so.

**Laws this build codifies:**
1. **Judges are assigned per-paradigm by measured precision.**
   Bucket-pricing recursed to judge-assignment: for every paradigm
   where two judges compete, both are measured and the assignment
   table prints in the HANDOFF — winner by forced accuracy with a
   judged-accuracy floor of 85%. Pinned by measurement already:
   c_command stays with the strict-frame judge (64.9 @ 87 beats
   depth-2's 53.9 @ 62.7 — c_command's antecedent IS the strict-frame
   subject; it was never depth-2's customer).
2. **The verb inventory is an artifact.** Subject/predication
   detection consults a checksummed verb list exported from the mined
   pairs (bases taking -ed/-ing, their -s forms, the irregulars page)
   — never a hand list. The session's noun-verb ambiguity failures
   (upset, sounds — mined as nouns) are the justification.
3. **A proposal is not an implementation.** The self-proposal ritual
   (B-0) emits evidence-cited proposals only; the proposed organ is
   never built in the same Part it is proposed. The human gate reads
   the proposal in the HANDOFF.

---

## D-1 · The depth-2 resolver (`mirror/frames.py` or beside agreement)

Probe 54's final form, verbatim in behavior:
- **Relativizer-head override:** an NP ending exactly at that/who/which
  left of the reflexive IS the matrix antecedent (this is what
  c_command-shaped sentences test; the override serves the domain
  family's relative-headed variants).
- **Walk-left-from-the-reflexive** through the verb cluster otherwise:
  nearest NP-tail whose noun is det/of/noun-preceded, or a listed or
  capitalized name, or a subject pronoun; verbish-ness by the law-2
  artifact; abstain when unresolvable.
- NP machinery: last-noun-of-run heads, **of-passthrough partitives**
  ("a lot of patients" → patients, pl), capitalization as the name
  signal (case preserved into the resolver).
- φ-check: number always; gender when known; himself/herself against
  gender-unknown subjects ABSTAINS (never guessed).

## D-2 · Assignment table + gates (`blimp.py`)

- `route()` extended with the depth-2 lane; the per-paradigm
  assignment table measured at build and printed (law 1). Expected
  assignments from probe 54: domains 1/2/3 + irregular_SVA_2 (+
  anaphor_number if it wins both clauses) → depth-2; c_command →
  strict-frame (pinned).
- **Gates (measured):** principle_A_domain_2 ≥ 61 forced with judged
  ≥ 73 (62.1 @ 74.3); domain_1 ≥ 98 @ 100 (98.6); domain_3 ≥ 85 @
  ≥ 93 (86.3 @ 94.8); irregular_plural_SVA_2 ≥ 89 @ ≥ 96
  (90.8 @ 97.4); anaphor_number ≥ 66.8 (whichever judge wins);
  c_command ≥ 63 (the strict-frame value restored); **FORCED overall
  ≥ 66.4** (measured 66.61 with the c_command regression still in;
  projected ≈ 66.8 with it restored — report the realized value);
  selective row printed; no-harm on every prior gate ± 1.5.
- **Canaries (the session's four broken rulers, pinned as tests):**
  partitive heads resolve plural ("a lot of patients" → pl); upset/
  sounds resolve as predications in walk-left; a relative-headed
  subject is found despite the relativizer blocking its next-token;
  and the F3 margin note (clause-boundary mislabel family confirmed;
  reduced relatives specifically unobserved in BLiMP — recorded).

## D-3 · F4/F5 — the real-text remine + the canary watch

- Rerun the probe-38 mined agreement battery (in-repo archive) with
  depth-2 inner-register handling on the tier-3 (relative) bucket.
  **Report-only bands:** tier-3 accuracy and n; the forecast's F4
  conjecture (75–85) is GRADED in the HANDOFF margin, hit or miss,
  with the number. F5 likewise: any canary that fires during this
  build is named in the deviations section (a fired canary is a
  finding, not a failure).

## C-1 · The folded 10M corpus (builder-executed measurement)

- **Sourcing policy:** single-register coherent text (the Gutenberg
  finding governs), assembled LOCALLY to 10.0M ± 0.2M words,
  BabyLM-legal, pinned as `corpus_10m.txt` with md5/sha256 in a
  manifest. The 5.2M `corpus_big` stays pinned and untouched — every
  existing battery keeps its vintage (artifact law; nothing swaps).
- Fold via the creature's addressing; PPMI + SVD-300,
  frequency-weighted centering; **the sentinel table gains a third
  column:** 5.2M-unfolded / 5.2M-folded / 10M-folded.
- **Recorded bands, graded at gate (forecast C1–C3):** WS353-rel on
  10M-folded vs 5.2M-folded (C1 predicted the volume move lands
  +0.05..+0.12 on relatedness; report Δ); SimLex Δ ≤ +0.05 (C2);
  a PARALLEL 10M trigram BLiMP baseline (report-only, shipped
  baselines untouched): overall Δ vs 56.79 with the distractor
  paradigms asserted still ≤ 55 (C3).
- **C4 canary procedure:** the first 10M build re-runs the 5.2M
  sentinel columns FIRST; any regression there is an instrument
  alarm naming the meaning organ before any 10M number is read.

## S-0 · Sensor world v0 (builder-executed measurement; grades S1/S2)

- `sensor/` — one synthetic alphabet (e.g., 12 discretized channels;
  patterns as episodes through the SAME organs: embed, gate, a_mem,
  refuse). Two batteries: **recognition** (known patterns ≥ 95%) and
  **refusal** (unknown ≥ 98%, confabulations == 0).
- **S2 assertion:** every threshold is re-swept from a measured
  window on the sensor data, with provenance in the docstring; the
  test asserts the sensor θs are derived values, not language
  constants (no threshold transfers — the forecast's strongest
  claim, 95%, graded here).
- Non-goals within S-0: the phase ruler (S3), continuous cosine
  paths (S4), the attack set (S5) — next campaign.

## B-0 · The proposal ritual (`agent/propose_organ.py`)

- The creature scans its OWN ledgers — deferral, censuses,
  prune/alias, drift — and emits exactly ONE organ proposal as
  `PROPOSAL.md`: the highest-evidence hygiene item, citing ≥ 25
  ledger entries by count and class, with a one-paragraph mechanism
  sketch and a proposed acceptance inequality.
- **Law 3 is hard:** the mechanism is built; the PROPOSED ORGAN IS
  NOT. The proposal ships verbatim in the HANDOFF for the human gate.
  This is the first formal self-proposed organ (the register's B1
  grades on what it nominates; the stem-existence check was the
  dress rehearsal).

## Close-out

`HANDOFF.md` Part XII: the assignment table, the gates, the sentinel
table with its new column, the S-0 numbers, the PROPOSAL verbatim,
forecast grades (F4, F5, C1–C3, S1, S2, B1) in the margin, deviations.
Next-frontier ranking (standing): the library's hard families
(islands/ellipsis — L2's bet), sensor S3–S5, repos public + Fellows
email. **Stop.**

## Non-goals
Implementing the proposed organ; islands/ellipsis/scope pages;
sensor S3–S5; corpus beyond 10M; swapping any pinned baseline or
vintage; leaderboard mechanics; gate changes.
