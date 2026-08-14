# pat — Citizenship & The Compass · Build Spec (Part XVII; probes 59, 60, 61)

**Two halves and a half-dimension: the taught-word citizenship law
(the lantern finding) and the compass fold (the human's drawing —
`sequencing.drawio` ships in `docs/`, the second whiteboard square in
this project's history to become an organ).** **Location:** `~/pat`,
on the landed Part XVI. **House rules unchanged:** tests before
features; acceptance by inequality; flag, don't reconcile; build →
`HANDOFF.md` Part XVII → stop. **Reference probes:** probe59,
probe60, probe61 (this folder).

**Laws this build codifies:**
1. **Citizenship is decided by receipts.** A taught word with a
   pronunciation on file is a FULL citizen — it joins the derivation
   index and its family certifies through the standard double-lock.
   Without one it is a PARTIAL citizen — remembered with its taught
   receipt, inflections refusing with the reason named.
2. **The transform proposes; only attestation asserts.** A predicted
   pronunciation (stem + modal allomorph) may appear as a REPORT
   line — "derivable by rule; pronunciation predicted, not
   attested" — and may NEVER enter certification. No provenance
   class launders computed sounds into heard ones. Structural assert.
3. **Order is folded, not forgotten.** The compass fold stores a
   sequence as an order-free bag of dial-stations from which exact
   order is recoverable by theorem (CRT). The cone keeps its counts;
   it gains an annex; nothing is replaced.
4. **Tangency is an assert.** The dyadic dials nest with zero slack:
   residue mod 4 == (mod 8) reduced, mod 2 == (mod 4) reduced, at
   every position, checked at import.
5. **The ear extends to teaching.** 7.5% of teachable words collide
   by sound with a known spelling; the teach verb emits the
   homophone cross-reference at teach time.

---

## T-1 · Citizenship (`pat` teach path)

- `remember <w>`: consult the lexicon; pron found → full citizen
  (derivation index join, provenance `taught`; children certify via
  the existing double-lock, provenance `derivable:taught-stem`);
  pron absent → partial citizen.
- **Gates (measured, probe 59):** the LANTERN battery — teach
  lantern, `analyze lanterns` certifies with receipt, and the taught
  citizen SURVIVES RESTART with status intact; a 50-stem unlock
  sample — ≥ 95% of pron-on-file children certify (pool: 6,076
  stems / 7,005 children); the ear clause — teaching a colliding
  word (aalen vs alan pinned) emits the cross-ref line; the partial
  citizen — teach zorp, `analyze zorps` → "refuse: no pronunciation
  on file" verbatim; law 2's structural assert (no predicted pron in
  any certification path); no-harm ± 1.5 everywhere.

## T-2 · The compass organ (`mirror/compass.py`)

- `fold(phones)` → bag of (phone, i mod 8, i mod 7) with counts;
  `decode(bag, n)` → the sequence, CRT over the mod-56 window;
  equality on folds = order-sensitive exact match.
- **Gates (probe-exact, probe 60):** collision separation
  16,520/16,520 colliding pairs distinct (9,451 count-signatures,
  21,836 orderings); invertibility 135,166/135,166 lexicon words
  round-trip; headroom asserted against the artifact (longest pron
  28 < 56, margin reported).
- The drawing ships: `docs/sequencing.drawio`, with one HANDOFF
  paragraph naming the stations — cardinals on the circle exactly,
  corners overhanging by .414/2, the junction charge pricing the
  diagonal stations.

## T-3 · The dyadic reading (same module)

- Bit-plane accessors: dial level k reads bit k of position;
  tangency assert (law 4) at import over 0..maxlen; locality
  helper — equal full readings differ by exact multiples of 8,
  asserted zero violations (probe 61).
- Recorded, not gated: coarse-to-fine neighborhood queries; listed
  customers — a_mem addressing's order channel, the sensor lane's
  S3 phase ruler. Customers listed, NOT built.

## T-4 · First customers (minimal wiring)

- The homoshape ambiguity retires: the colliding-base families'
  pairwise confusability re-measured WITH the compass — report
  100% distinct beside the Part X canary's 0.9903 cosine (the scar
  and its healing printed together).
- `verify` gains the ANAGRAM GUARD: a proposal whose phones permute
  the surface's (counts match, order differs) refuses with "same
  sounds, different order — the compass tells them apart"; one
  constructed battery case pins it.
- Margin note: the forecast register grades S3 early — the phase
  ruler exists before its campaign did.

## T-5 · Close-out

`HANDOFF.md` Part XVII: the authorship line (drawn by the human,
probed, built), the three probes' numbers, deviations, no-harm.
Frontier ranking (standing): the stem-allomorphy lane, the
register-mixture corpus, the phrasing slot — and the three send
buttons that belong to exactly one person: the push, the PR
submissions, the email. **Stop.**

## Non-goals
Any certification of predicted pronunciations; replacing counts or
chapters anywhere (the compass is an annex); continuous-angle or
learned-frequency dials; building S3; teaching multi-word phrases;
taught stems seeding suffix discovery (second-order teaching — a
future probe's question).
