# mirror — Frame Tiers & The Phon Gate · Build Specification (probes 38–39)

**Location:** `~/alignment_field/mirror` (+ agent battery re-runs).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` Part VI → stop.
**Reference probes delivered:** probe38 (widened frame, coordination
amendment), probe39 (two-mechanism gate: kill 0/120, tax 100% vs 88.5%,
disambiguation 120/120, arbitration 150/150).

**New laws this build codifies:**
1. **Scope frames, don't replace them.** Shape keeps families/binding
   (collapse is a feature there); phon gets stem identity (collapse is a
   bug there); the induced table gets suffixes. No blunt thresholds.
2. **Coverage is bought bucket by bucket, and every bucket wears its
   price.** The frame ships as confidence tiers with per-tier measured
   precision; consumers choose tiers by number.
3. **Ties are broken by evidence, never by order.** Any argmax whose
   candidates can score identically must either consult a
   finer-frame measurement or refuse. Dict-order survival is the failure
   mode this build retires.

---

## F-1 · Tiered frame (`mirror/agreement.py` upgrade; probe 38)

- v2 frame: adjunct-skip (leading PP chains), subject-relative inner
  registers (relativizer opens; verb-ish closes innermost-first — the
  RegisterBank discipline applied to clause structure), and FRAME REFUSAL
  with a named taxonomy: no-det-n-subject, no-verb-in-window,
  coordination (and/or/nor/but between subject and verb), adjunct-
  unparsed, object-relative.
- Tier tags on every accepted case: tier-1 strict / tier-2 adjunct-led /
  tier-3 relative (experimental).
- **Fixture:** regenerate once from the pinned corpus (seed 5), pin the
  case list; record exact counts (probe measured 431 cases / 26
  attractors / buckets 408·16·7 / refusal counts 9790·302·299·131).
- **Tests (pinned fixture):** tier-1 subset reproduces the strict-frame
  regression (REGISTER no-attractor ≥ 90%, attractor ≥ recent-noun + 30);
  full-frame attractor REGISTER ≥ 70% (measured 77%) with recent-noun
  ≤ 40% (seduction control) — attractor n must be ≥ 2× strict's 12;
  tier-2 precision recorded in a band (measured 75%, n = 16 — report,
  don't over-assert); tier-3 REPORT-ONLY with experimental flag (57%,
  n = 7 — asserting it would be pretending); coordination refusal count
  > 0 asserted (the category must stay live).

## F-2 · The phon gate (`mirror/gate.py`, wired into `analyze`; probe 39)

Two mechanisms, applied AFTER the shape loop proposes (b, sfx):
1. **Stem-scoped identity:** cos(phon(obs[:len(b)]), phon(b)) ≥ θ_p =
   0.77 (window-derived: cross-stem cap 0.7526 < true p5 0.7778;
   provenance comment with the window numbers and corpus checksums).
2. **Suffix arbitration:** the observed remainder must be in the attested
   allomorph set of the PROPOSED suffix (built from training pairs at
   build time, pinned).
Refusal reasons distinguish the two ("stem mismatch" vs "remainder not
an attested <sfx> form"). Bare-base acceptance gets the stem check with
L = full length (exact-phon identity for ties).
- **Tests (pinned attack/true fixtures from the collision census):**
  - kill: gated false-accepts **0** on the attack set (probe: 0/120) —
    hard assert, this is the safety number now;
  - no-tax inequality: stem-gate true accepts ≥ blunt-gate true accepts
    AND ≥ 99% on pinned trues (measured 100% vs 88.5%); epenthesis
    subfamily asserted separately (39/39);
  - disambiguation: both-known colliding pairs attribute by stem-phon
    ≥ 95% (measured 120/120);
  - arbitration: wrong-suffix proposals rejected ≥ 98% (measured
    150/150).
- **The canaries stay.** The census, cell/seal collision, and open-split
  ceiling == 1.0 describe the SHAPE space, which is unchanged and still
  true. Add one new canary: the gated pipeline's false-accept count on
  the attack fixture == 0, with a message pointing at Part V's finding.

## F-3 · Batteries re-run under the gate (the point of the build)

- Learning battery: **teach-order sweep** — run with cell/seal (and two
  more pinned colliding pairs) taught in BOTH orders; zero confabulation
  asserted in every order. This retires the tie-order luck explicitly:
  the assertion that used to pass by accident now passes by measurement.
- Composition battery, agent 7-suite, and the full mirror suite: green
  with the gate wired in; record any true-accept change (expected: none).
- HANDOFF headline: whether the result is the project's first
  **unconditional zero-confabulation** claim — stated in the three-layer
  language (property of the gated pipeline over the open vocabulary,
  attack-fixture-checked), not the old geometry language.

## F-4 · Close-out

`HANDOFF.md` Part VI: numbers, deviations, fixture counts, before/after
battery table, and the next-frontier ranking (standing: tier-3 relative
heuristic + subject-ID at scale; tense register; schooled twin / BLiMP;
WS-353 / Morfessor rows; sensor-alphabet world; repos public + Fellows
email). **Stop.**

## Non-goals
Stem allomorphy (run/ran — out of scope as always), parsing beyond the
tiers, phrasing slot, open-world routing, performance work, new verbs.
