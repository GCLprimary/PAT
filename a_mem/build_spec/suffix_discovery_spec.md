# agent + mirror — Suffix Discovery · Build Spec (Part XIII; probe 55)

**FOUNDING DOCUMENT: `agent/PROPOSAL.md` — written by the creature,
accepted at the human gate.** This spec implements that proposal and
nothing beyond it. The authorship ledger for Part XIII, to be printed
at the top of the HANDOFF: *proposed by the creature (from its own
ledgers), gated by the human, probed by Claude (probe 55, delivered),
built by Claude Code.* The first Part in the project's history whose
founding document was written by the system it extends.

**Location:** `~/alignment_field`, on the landed Part XII. **House
rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part XIII → stop.
**Reference probe:** probe55 (this folder).

**Laws this build codifies:**
1. **Discovery is audited like any teacher.** A candidate suffix must
   beat the stem-attestation baseline by an ADDITIVE margin (the
   probe's multiplicative bar failed because the baseline is
   contaminated by the signal itself — random class words carry real
   suffixes too; recorded as the audit's design note). Minimum stem
   length 3 phonemes damps accidental short-stem hits.
2. **Only what exactness can carry.** Concatenative candidates only:
   pron-exact stem AND orthographic decomposition (the double-lock).
   Mutating and bound-stem classes (create→creation t→sh; famous
   without free *fam*; ability without free *abil*) are CENSUSED with
   counts and flagged to the future stem-allomorphy lane — its
   customer list, never guessed at.
3. **Discovered knowledge wears its provenance.** `discovered:<sfx>`
   is the ledger's FIFTH provenance class (birth / read / lesson /
   pruned / discovered). It survives restart like the others.
4. **Greedy longest-tail-first harvest.** -ment claims its words
   before the n-t fragment can; harvested words leave the pool.

---

## O-1 · The discovery module (`agent/agent/discovery.py`)

Probe 55's final form, verbatim in behavior:
- Input: the reading session's `no-such-stem` ledger (recomputed or
  read from the shipped session).
- Candidate mining: phoneme tails k = 4, 3, 2 (longest first),
  yield ≥ 50 in the class; **audit:** stem-attestation rate ≥
  baseline_k + 15 points AND attested-stem count ≥ 40, baseline from
  1,500 random class strips at the same k with MINSTEM = 3.
- Certification: for each surviving candidate, modal spelling from
  orthographic decompositions; a pair (word, stemword) is CERTIFIED
  iff `pron(word) == pron(stemword) + tail` AND
  `word == stemword + modal_spelling`. Greedy pool removal (law 4).
- Output: `discovered_suffixes.json` (checksummed artifact): per
  suffix — phoneme tail, modal spelling, certified count, audit
  numbers, spelling share; plus the MUTATING/BOUND CENSUS (per
  rejected or partial candidate: counts and three named exemplars).

## O-2 · Registration into the ladder and the ledger

- Each discovered suffix enters the arbitration ecology at the
  granularity it earned: its certified (stem, suffix, word) triples
  register as PAIR-EXACT entries; the tail joins the attested
  remainder set under the suffix's name; MAXR grows if needed (it
  does: -ment is 4) — asserted against the artifact, not hard-coded.
- The 314-class atoms RETIRE into aliases with provenance
  `discovered:<sfx>` (law 3), exactly through the existing certified
  prune pathway ("no new physics — composed," per the proposal).
- Re-read assertion: after registration, every retired word ANALYZES
  as stem + discovered-suffix through the standard gate; the reading
  loop's stem-existence oracle now consults the widened remainder
  set (so future no-such-stem adoptions shrink — report the delta).

## O-3 · Batteries and gates (measured, probe 55)

- **≥ 3 suffixes discovered, and -ment, -less, -est by name** —
  certified counts ≥ 130 / ≥ 75 / ≥ 55 (measured 133, 78, 57);
- **total retirements ≥ 300** (measured 314) with **CONFABS == 0**
  (the double-lock is a hard assert per pair);
- **the organ's taste, asserted as canaries:** -ist refused at the
  yield bar (measured 27 < 40, censused not discovered); the -et
  fragments refused; the bound-stem zero-classes (-ous at 0%, -ility
  at 0%) pinned as the BOUND-STEM CANARY (if either ever certifies,
  the message asks what changed);
- **the creature's own acceptance inequality** from `PROPOSAL.md`
  quoted verbatim in the HANDOFF and asserted ALONGSIDE these gates
  (both must hold; a conflict is a flag, not a reconciliation);
- recorded headroom, not gated: the -est e-deletion spelling class
  (latest = late + st; ~50 pairs) — a dial for a future pass;
- no-harm: every Part VIII–XII gate green at pinned values ± 1.5
  (discovery must not disturb the shipped batteries; the widened
  remainder set's effect on reading numbers is REPORTED with both
  vintages, old policy pinned as always).

## O-4 · The demo (`demo_discovery.py`, < 40 s)

Three beats, narrated from the ledgers: the census ("7,119 words I
adopted because their stems did not exist; their tails spell a rule I
was never taught"), the discovery ("-ment: 148 attested stems against
a 33.5% baseline; 133 certified by sound and spelling"), and the
retirement — one biography read aloud:
`government — adopted read:no-such-stem; retired discovered:ment;
now govern + ment, both receipts kept.`

## O-5 · Close-out

`HANDOFF.md` Part XIII: the authorship ledger, the discovered-suffix
table, the mutating/bound census, the reading-delta report, forecast
margin updates (B1 stands graded; B2 continues to watch the gate),
deviations. Next-frontier ranking (standing): the stem-allomorphy
lane (its customer list now has counts), the register-mixture corpus
(C1's lesson), sensor S3–S5, repos public + Fellows email — **that
last item's forecast band closes at the next build.** **Stop.**

## Non-goals
The mutation/bound-stem lane (-tion, -ity, -ous, -ist) beyond its
census; e-deletion spelling variants (recorded headroom); prefix
discovery; second-order discovery (suffixes on discovered stems);
any capability beyond the proposal's own paragraph.
