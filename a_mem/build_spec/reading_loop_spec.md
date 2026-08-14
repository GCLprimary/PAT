# agent + mirror — The Reading Loop · Build Specification (probes 40–41)

**Location:** `~/alignment_field` (mirror gate refinement + new agent
capability; a_mem untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part VII → stop.
**Reference probes delivered:** probe40 (reading v1 + anagram-stem finding),
probe41 (metabolism: revisit, prune, the set-vs-table hole, and the
hand-rule drift that closed it).

**New laws this build codifies:**
1. **Exactness beats similarity wherever exactness is available.** Stem
   identity in the closed world is sequence equality, not count-cosine —
   the anagram leak (melted→metal+ed at cos 0.78) is the proof. The
   θ_p = 0.77 cosine path stays in `gate.py` as a documented, dormant
   fallback for future noisy-input worlds; it is not consulted in the
   closed world.
2. **Arbitrate with the artifact, never a re-derivation.** The suffix-wide
   attested SET admitted place→play+s (vowel-final licenses z, not s); a
   hand-rederived rule then over-refused truth (coverage 11% vs 24% —
   drift quantified). The arbiter is the INDUCED TABLE (the surface
   module's pinned artifact, 99.1%), consulted by import, checksummed.
3. **Prunes must be homophone-certified.** A self-taught atom may be
   retired only when its pronunciation is IDENTICAL to its derivation's
   surface (find = fined). Non-identical prons (place ≠ plays) must never
   prune — asserted as a canary.
4. **The censuses are organs.** Imposter census, homophone census, and the
   prune ledger are first-class diagnostics with their own tests, not
   debug printouts.

---

## W-1 · Gate refinement (`mirror/gate.py`)

- Stem check becomes sequence-exact (`obs[:L] == base_pron`); bare-base
  acceptance requires full-sequence equality, with same-pron different-
  orthography results returned as `HOMOPHONE(analysis)` — a distinct,
  honest verdict class, never a confab.
- Arbitration: replace attested-set membership with the induced allomorph
  table (law 2). The gate imports the table from `surface`; a test asserts
  the consulted table's checksum equals the pinned artifact's.
- **Canaries (pinned):** melted-vs-metal must REFUSE (anagram stems);
  place-as-play+s must REFUSE (table catches unlicensed allomorph);
  find-as-fine+ed must return HOMOPHONE class (genuine sound identity).
- **Regression:** all frame_gate Part VI tests stay green (120/120 kill,
  200/200 trues, 18/18 teach-order, batteries unchanged).

## W-2 · The reading loop (`agent/reading.py` + `read` capability)

- `Agent.read(stream, epochs)` — frequency-ordered word stream; per word:
  analyze (gated). REFUSED + attested (count ≥ 5, in lexicon, len ≥ 4):
  - **defer** if derived-looking (final 1–2 phonemes match an attested
    remainder) — the wait-for-the-stem instinct;
  - else **self-teach** with provenance `read: attested <n>`, checking the
    shape census at write time (self-census entry when colliding).
- Per epoch: **revisit** deferred (resolutions ledgered
  `unlocked by <stem>`); **prune** read-taught atoms that became
  derivable — retire the row but keep a ledger alias so `know` and
  `analyze` still answer truthfully (provenance:
  `derivable: fine+ed; read-taught epoch j, pruned epoch k`). Law 3
  certification on every prune.
- Provenance ledger grows a third class: birth / taught / **read**.

## W-3 · Batteries (pinned 6,000-word stream fixture, seeded)

- **Growth:** known ≥ 1,500 by epoch 6 (measured 1,786); coverage on the
  aligned derived-form test ≥ 60% final (measured 67.0%), monotone
  nondecreasing across epochs.
- **Honesty invariant:** REAL confabs == 0 at EVERY epoch (hard);
  homophone verdicts all same-pron-verified (each ledgered entry's prons
  compared in the test itself).
- **Metabolism:** unlocked ≥ 10 (measured 18); prune ledger nonempty and
  100% homophone-certified; the place canary standing guard.
- **Self-census:** nonempty, entries verified same-shape; census size
  recorded per epoch (the curve is data, not a gate).
- Agent suite + full mirror suite green with the refined gate.

## W-4 · `examples/demo_reading.py`

< 60 s: born with 15 bases, reads a pinned 1,000-word stream aloud in
summary (taught n, deferred n, unlocked n, pruned n with one certified
example, census n with one example), then answers: `know <read-taught
base>` (yes, with read provenance), `analyze <unlocked word>` (derived,
crediting the stem), one homophone verdict stated in plain language
("sounds identical to fine+ed — I cannot tell them apart by ear"), and
one refusal. End with the provenance ledger totals.

## W-5 · Close-out

`HANDOFF.md` Part VII: numbers, deviations, before/after gate table, and
the next-frontier ranking (standing: reading at 10× scale + census
curves; subject-ID at scale; tense register; schooled twin / BLiMP;
WS-353 / Morfessor; sensor-alphabet world; repos public + Fellows email).
**Stop.**

## Non-goals
Noisy/real-world input (the cosine path sleeps until then), orthographic
disambiguation, stem allomorphy, streams beyond the pinned fixture,
new alphabets, new verbs beyond `read`, performance work.
