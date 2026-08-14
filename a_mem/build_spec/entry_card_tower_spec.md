# mirror + agent — The Entry Card & The Tower · Build Spec (Part XI; probes 50–53)

**This spec SUPERSEDES `benchmarks_addendum.md` and
`tower_housekeeping_addendum.md`.** If either file reached the repo or
the task queue, discard it — everything they contained is here, once,
renumbered. Nothing in this spec re-touches Part X's modules except
the named extensions to `blimp.py` and the harness output.

**Location:** `~/alignment_field`, on top of the landed Part X
(chapters, gated circulation, count fold all assumed present and
green). **House rules unchanged:** tests before features; acceptance
by inequality; flag, don't reconcile; build → `HANDOFF.md` Part XI →
stop. **Reference probes delivered:** probe50 (the tower), probe51
(UniMorph inflection), probe52 (the wug battery), probe53 (pages 6–7,
diff-judges, the selective aggregate).

**Laws and pinned findings this build codifies:**
1. **The mining projection has a shadow.** String-concatenation mining
   structurally cannot see non-concatenative orthography (moved,
   making, stopped, carries); a table induced from mined pairs
   inherits the blindness (measured 22–30% on exactly those classes).
   When a ruler's own attested pairs exist, induce from them.
2. **The armchair is not a gold standard.** Twice the artifacts
   out-graded my hand rules: affricate finals take epenthesis (the
   table was right, the hand sibilant set was wrong), and kn-/vl-/ts-
   onsets are attested (Knupp, Vlad, Tsang — the attestation gate
   refused the "illegal" label). Both pinned as label-noise canaries.
3. **The specific judge outranks the general lane.** Measured failure:
   anaphor_gender sat inside the reflexive lane and was silently
   absorbed (0 judged) until direct judges were routed first. Encode
   the order in `route()`; assert the gender paradigm reports > 0
   judged.
4. **The tower** (doctrine with numbers): sequence → cone → sphere →
   angle, each floor a projection forgetting one thing (order,
   magnitude, direction). The system already staffs the floors —
   gate at sequence, decoder at cone, proposer at sphere.
   "Exactness beats similarity" restated as geometry: work as high up
   the tower as the artifacts allow.

---

## E-1 · Inflection module (`mirror/inflect.py`)

- Orthographic rule induction, the same organ as the phon table:
  `classify(base, form)` into {s, es, ies, ed, d, ied, Ced, ing,
  e_ing, Cing}; signature = (CV-pattern of the penultimate two,
  final letter); table = argmax counts. ~298 rows, printed in FULL in
  the HANDOFF — the model is the page.
- Induced from the **UniMorph English train split** (vendor the file
  with checksum + source attribution; lemma-disjoint 80/20 split
  pinned by seed 7), NOT from mined pairs (law 1). Target tags:
  V;PST, V;PRS;3;SG, V;V.PTCP;PRS, N;PL.
- Irregulars ride pages only (page 2 plurals, E-4's page 7 pasts);
  UniMorph is data, never a lesson source — no page may be authored
  from it. Residue REFUSED or wrong, never silently patched.
- **Gates (measured):** held-out forced ≥ 95.5 (96.54); coverage ≥ 99
  (100); per-tag floors V;PST ≥ 89 (90.6), V;PRS;3;SG ≥ 96 (97.0),
  V;V.PTCP;PRS ≥ 96 (97.0), N;PL ≥ 97 (97.6); the printed table must
  contain a doubling row, an e-deletion row, and a y-replacement row
  (readability asserted by inspection).
- Honest note for the HANDOFF: with page 7 riding first, held-out
  V;PST moves only 90.6 → 91.1 (the common irregulars live in train);
  the page's real payoff is E-4's two perfect BLiMP paradigms.

## E-2 · The wug battery (`demo_wug.py` + test)

- Novel stems = attested-onset × attested-nucleus × attested-coda from
  monosyllables, verified absent from the lexicon; legality IS
  attestation. Inflection by the shipped induced PHON table;
  selective: unseen final signature → REFUSE, counted.
- **Gates (measured):** agreement with the corrected textbook rule on
  answered ≥ 99 for both suffixes (past 285/285 with 15 refusals;
  plural 296/296 once affricate epenthesis is in the gold — law 2's
  first canary); truly-unattested onsets refused 100% (21/21), with
  the kn-/vl-/ts- attested exemplars named in the test docstring
  (law 2's second canary).
- Demo line, mandatory: `"this is a wug; now there are two ..." →
  wug+z: w AH g z` — with the table row cited.

## E-3 · The tower (`mirror/geometry.py` + battery)

- `counts_of(phones)` (raw cone embedder, unigram + bigram integer
  counts) exposed beside the unit embedder; radius accessor `mass(w)`
  (L1 norm) exposed, deliberately unused, noted.
- **Battery:** the cone identity — counts(p+b+s) == Σ part counts +
  junction bigrams — asserted as EXACT integer equality on every
  phonologically-faithful prefix+base+suffix triple (measured
  164/164); the unfaithful remainder (36) is the VOWEL-REDUCTION
  CENSUS (English declining to concatenate), counted and named,
  never scored as error.
- **Recorded bands, not gates:** tilt 22.5° ± 3 per junction (45° is
  the orthogonal ideal; base mass leans the ray); junction cost
  ‖a+b‖ − 1 = 0.535 ± 0.03, with the ad-quadratum √2 − 1 = 0.414
  recorded as the measured FLOOR; and the DILUTION LAW — relative
  curvature ∝ junctions/mass, so the 3-morpheme SUM-cosine (0.919)
  EXCEEDS the 2-morpheme (0.883): the sphere flattens as words grow,
  and the seam matters most for short words.

## E-4 · Pages 6–7 and the diff-judges (`data/`, `blimp.py`)

- `page_gender_names.txt` (~160 textbook first names → f/m) and
  `page_past_irregulars.txt` (~49 base→past; ~26 with distinct
  participles as base→(past, participle)). Headers: transcribed,
  NOT mined, NOT peeked. Checksums pinned; the page count grows to 7.
- **Diff-position judges** (new reusable judge shape): align the pair;
  require exactly ONE differing token; act only when the diff is the
  page's business; tokens normalized lowercase with punctuation
  stripped. `gender_pick`: diff = {himself, herself}, gender from any
  listed name in the sentence, else abstain. `ppart_pick`: diff =
  (past, participle) of one listed verb; prenominal (determiner
  immediately before) ⇒ participle; bare-verbal (no aux within 3
  tokens before) ⇒ past; else abstain.
- **Routing law (law 3) implemented in `route()`** — direct
  diff-judges take their paradigms BEFORE the general reflexive lane;
  asserted: anaphor_gender_agreement reports > 0 judged.
- **Gates (measured):** anaphor_gender_agreement ≥ 77 forced with
  judged accuracy 100% (79.3; 247 judged — coverage is the name-list
  dial, documented, not grown); irregular_past_participle_verbs
  == 100.0 with ≥ 850 judged (864 @ 100%);
  irregular_past_participle_adjectives == 100.0 with 1000 judged
  (@ 100%); FORCED overall ≥ 65.5 (65.92); the library curve printed
  in Part XI: **56.79 → 60.52 → 64.79 → 65.92** (0, 2, 5, 7 pages).
- No-harm: every Part VIII–X gate stays green at its pinned values
  ± 1.5.

## E-5 · The selective aggregate + certifications (`blimp.py` output)

- The harness prints the entry-card number EVERY run: judged coverage
  and judged accuracy over all 67, beside the forced overall.
  **Recorded band, not a gate:** 24.2% coverage @ 93.81% judged
  (forecast L3 targets 35–45% @ ≥ 95 as the library grows).
- `existential_there_quantifiers_2` CERTIFIED: quantifier-inversion
  structure ("All convertibles weren't there existing") — abstention
  is correct, no cheap page exists; flagged to the frame lane and
  asserted at 0 judged.

## E-6 · The entry card (HANDOFF Part XI appendix)

One page assembled from gated numbers — the card we enter the scene
with, **one sentence under each number naming the mechanism that
bought it**:
- BLiMP 67: forced 65.92, the per-paradigm table, and the selective
  row (24.2% @ 93.81%);
- Meaning (folded): WS353-sim / WS353-rel / SimLex at the shipped
  Part X values, unfolded reference column beside;
- Inflection: UniMorph held-out 96.5 forced / 100% coverage, 298
  readable rows;
- Wug: ≥ 99 on answered with refusal; illegal-onset containment with
  the Knupp/Vlad/Tsang story;
- Safety: unconditional zero-confab, the censuses, conservation
  ("3,473 in, 3,473 out"), and the two provenance showpieces —
  `read: stem markka exists unread` and `'side' lives in sigh's
  chapter with its entire history in one line`.

## E-7 · Close-out

`HANDOFF.md` Part XI: numbers, the four laws with their measured
justifications, deviations, next-frontier ranking (standing:
**frame depth-2** — clause segmentation, six customers — then the
folded 10M corpus with WS-rel targets, the lesson library continued,
repos public + Fellows email). **Stop.**

## Non-goals
EWoK, reading-time correlation, GLUE (future rulers — fetch/licensing
noted); leaderboard submission mechanics; name-list growth or gender
inference beyond the listed names; quantifier-inversion pages;
radius-channel use; log-cone exploration; pages authored from
benchmark data; any re-touching of Part X modules beyond the named
`blimp.py`/harness extensions.
