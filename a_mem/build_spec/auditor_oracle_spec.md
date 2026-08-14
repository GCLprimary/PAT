# agent — The Auditor & The Oracle · Build Spec (Part XIV; probe 56)

**Pat's first job.** Two verbs enter the repertoire — `audit` and
`verify` — turning probe 56's sweeps into products: receipted
errata/addenda reports on the lexicons Pat was born from, and a
verification oracle that answers proposed derivations with
CERTIFY / REFUSE / HOMOPHONE and the receipt. **Location:**
`~/alignment_field`, on the landed Part XIII. **House rules
unchanged:** tests before features; acceptance by inequality; flag,
don't reconcile; build → `HANDOFF.md` Part XIV → stop.
**Reference probe:** probe56 (this folder).

**Laws this build codifies:**
1. **The verb five-tuple is the unit of feature.** Every repertoire
   addition ships as (name, trigger grammar, organ composition,
   refusal set, provenance line format) plus its battery. Printed in
   the HANDOFF for both new verbs. The phrasing slot stays a slot:
   template lines, never chat.
2. **A claim without its receipt is a confabulation, even in a
   report.** Every emitted row carries its machine-checkable receipt
   fields; a row with any receipt field empty fails a STRUCTURAL
   assert. Zero unreceipted claims is a gate, not a style.
3. **Phone case is asserted against the artifact.** The mixed-case
   vintage took its sixth scalp on probe 56 itself (lowercase ng vs
   NG, 1,858 phantom mutations). The auditor asserts its suffix-tail
   phone set ⊆ the lexicon's actual phone alphabet at import.
4. **Hazards are flagged, not filtered.** Onomastic pairs
   (gould→goulding) ride the report with an `onomastic?` column
   (stem ∈ names pages), never silently dropped; the precision
   battery measures with and without.
5. **The human gate holds the hand-check.** Precision is a human
   adjudication, formalized as the gate's own battery clause — the
   four-party loop with the human's rung written into a test file.

---

## J-1 · The auditor organ (`agent/agent/auditor.py`)

Probe 56's three sweeps, probe-exact:
- **A1 CMU variant candidates:** orthographic decomposition
  (stemword + suffix spelling, e-restoration candidate included)
  vs pron concatenation; mismatches classed **elision / mutation /
  insertion** via edit-distance-1, with the subfamily labels from
  the probe carried as annotations where computable (the -al+ly
  degemination family; voicing s↔z; noun-verb stress pairs;
  stress-shift reduction). Receipt per row: word, stem, suffix,
  expected phones, actual phones, class, altered phone.
- **A2 UniMorph addenda:** double-locked mined pairs (pron-exact +
  ortho-exact + attested ≥ 5) whose (lemma, form, tag) rows the
  vendored file lacks; TAGMAP as probed; onomastic column per law 4.
- **A3 homophone index:** the pron-group cross-reference table.
- Outputs: `reports/audit_cmu.tsv`, `reports/audit_unimorph.tsv`,
  `reports/homophone_index.tsv` + a one-paragraph organ-voice
  summary each. Checksums in the HANDOFF.

## J-2 · The verbs (`agent/agent/shell.py`)

- **`audit <target>`** — targets exactly {cmu, unimorph, homophones};
  runs the sweep, writes the report, answers in organ-voice with the
  yield line ("459 candidates; every row carries its receipt").
  Unknown target → `refuse: I can audit cmu, unimorph, homophones`.
- **`verify <word> = <base>+<suffix>`** — the oracle ladder verbatim
  from the probe: unknown base / unreadable word / pron-prefix
  failure / unattested remainder → named REFUSE with the receipt;
  pair-exact → CERTIFY; sound-identical sibling → HOMOPHONE ("I
  cannot tell them apart by ear"). Malformed input → named refusal.
- Both five-tuples printed in the HANDOFF (law 1). Multi-clause
  inputs compose with existing verbs under probe 34's containment —
  one battery case asserts `audit cmu and verify side = sigh+ed and
  translate hello` yields exactly report + HOMOPHONE + alien refusal.

## J-3 · The precision battery (the human's rung)

- Builder generates `reports/precision_sample.tsv`: 50 stratified
  rows (15 elision, 15 mutation, 10 UniMorph addenda, 5 insertion,
  5 onomastic-flagged), each with full receipts and an empty
  `verdict` column plus schema {correct, incorrect, unsure}.
- The battery asserts: sample exists, stratification exact, receipts
  complete, verdict schema valid. **The ≥ 90% precision clause
  (ex-onomastic; onastic subrate reported separately) is graded at
  the human gate, by the human, on this file** — per law 5. The
  build does not self-grade precision.

## J-4 · The demo (`demo_audit.py`, < 45 s)

Three beats: one audit line with its receipt read aloud
(*abnormally = abnormal + ly: the lexicon drops one /l/ — the
degemination family, 168 strong*); the government line (the refusal
that is also the finding); and the oracle transcript — the probe's
ten proposals pinned verbatim as a 10/10 regression.

## J-5 · Close-out

`HANDOFF.md` Part XIV: yields vs probe with drift bands (A1 total
459 ± 5%, elision ≥ 160, insertion ≤ 25, exact ≥ 2,900; A2 ≥ 1,950;
A3 13,982 ± 1%), the five-tuples, the shipped precision sample
awaiting gate adjudication, checksummed reports, deviations, no-harm
(every Part VIII–XIII gate ± 1.5). Next-frontier ranking (standing):
upstream PR drafting AFTER the precision grade passes; the
stem-allomorphy lane; the register-mixture corpus; repos public +
Fellows email. **Stop.**

## Non-goals
Submitting upstream PRs (next Part, gated on the precision grade);
the corpus-linter aperture; the terminology-compliance agent; new
suffix categories; stem-allomorphy fixes beyond the census; wrapping
`verify` as a service/API; any phrasing beyond template lines.
