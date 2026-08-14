# mirror — Generation Build Specification (probes 23–28)

**Location:** `~/mirror` (extends the accepted scaling build; a_mem untouched).
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` → stop.
**Reference probes delivered:** probe23 (decoder + allomorphs), probe23b
(inversion accounting), probe24 (v1 failure, kept as evidence), probe25
(prefixes), probe26 (rule induction), probe27 (generator v2), probe28
(geodesics).

**Pending amendment to apply first:** W-3 loop acceptance becomes a band —
known-set accuracy ≥ 16/20 across sampling protocols (shuffled canonical
19/20; raw-order 16/20 documented). Zero-confabulation and the laziness
inversion (θ=0.90 accuracy < θ=0.98 accuracy) remain absolute. One-line
change plus a protocol note in the existing test.

---

## What this build adds

The generation half of the core. Analysis (built) runs observation → parts →
refuse-if-unknown. Generation runs intent → bound form → surface phonemes,
and prompt → audited continuation → refuse-if-unattested. Every arrow below
carries a probe number.

## G-1 · `mirror/decode.py` — the inverse embedder (probes 23, 23b)

From a bound (or stored) shape vector to a shape sequence:
1. **Integer snap:** unit vector → integer counts by λ-sweep (smallest
   nonzero entry scaled by k = 1..5; accept when all entries land within
   1e-6 of integers). Measured: 100% exact recovery.
2. **Eulerian validity:** degree accounting infers the start (out−in = +1);
   balanced graphs enumerate active starts. Unbalanced/disconnected graphs
   → structural REFUSE. Measured: 0% of real words refused (theory: all
   sequence-derived graphs are valid); SUM-bound vectors refuse 168/200
   (the seam-connectivity theorem — the seam term is the invertibility
   condition; document this in the module docstring).
3. **Walk enumeration** (cap 64) + tie-break. Lexicographic baseline
   measured 68% exact / 48% unique / 100% reconstructable-among-walks.
   Implement the **attested-trigram tie-break** (score walks by corpus
   shape-trigram counts) as the default candidate — UNPROBED, so it ships
   behind a promotion inequality: adopt iff exact ≥ 68% (the lex baseline)
   on the 500-word bank; otherwise lex stays default and HANDOFF records
   both numbers.
- **Tests:** snap 100% on 200 words; real-word refusal 0%; SUM-refusal
  ≥ 80% on 200 mined pairs; reconstructable 100%; unique ≥ 45%.

## G-2 · `mirror/surface.py` — induced allomorph table (probes 23, 26)

Learn the allomorph decision table from counts at build time (60/40 split):
final-segment signature (kind, manner, place, voiced) → allomorph class,
argmax per signature, modal fallback for unseen signatures. NO hand-written
rule anywhere. Export the table human-readable (it rediscovers voicing
assimilation and epenthesis; probe 26 prints the expected shape).
- **Tests:** induced accuracy ≥ 98.5% for -s and -ed (measured 99.1 / 99.2);
  the six showpieces (dog+z, cat+s, horse+IH z, play+d, help+t, want+IH d)
  as literal assertions; table export exists and lists ≥ 15 signatures.

## G-3 · prefix breadth — transform + loop L3 (probe 25; the old S-4, now unlocked)

Miner gains the prefix side (derived pron ENDS with base pron; prefixes
un/re/dis/mis/pre/over/out, 2,583 pairs measured). Transform learns modal
prefix forms; loop gains L3 (prefix-bound proposals after L1 bare and L2
suffix-bound).
- **Tests:** prefix SEAM held-out cosine ≥ 0.99 (measured 1.000) and
  SEAM > SUM (measured 1.000 vs 0.956); L3 known-set ≥ 16/20 (band rule);
  withheld refusal 20/20 with zero confabulation (absolute).

## G-4 · `mirror/generate.py` — selective generator v2 (probes 24, 27)

The reversed loop with probe-24's three lessons built in:
1. **Prompt-rung refusal:** an unattested prompt (no trigram context with
   support ≥ 2 AND broken internal bigram chain) refuses before emitting.
   Silent backoff past an unattested prompt is forbidden — probe 24's v1
   failure (selectivity gap −5) stays in the repo as evidence.
2. **Whole-continuation reflection:** beam over trigram continuations
   (depth 6, width 8, backoff to bigram only mid-walk), score each WHOLE
   continuation by topical coherence to the prompt (mean dense cosine of
   content words).
3. **Anti-rut:** any continuation reusing a bigram is discarded (the flood
   check). Best survivor must clear θ_m = 0.15 or refuse.

**Dual-corpus wiring (codify as a law in the module docstring):** the
PROPOSER volume-scales — its counts come from the largest registered corpus
stack (5M measured). The MEANING geometry coherence-scales — it stays on the
coherent default (Brown dense). Probes 22 + 27 measured the two scaling laws;
the S-2 registry makes the wiring natural.
- **Tests:** word-salad refusal = 100/100 (hard assert — the confabulation
  count is this module's zero-confab analog); selectivity gap ≥ 50 points
  with the 5M proposer (measured 65: in-domain 35% vs salad 100%);
  emitted-continuation coherence ≥ +0.30 (measured +0.325); regression:
  v1-policy generation on the three probe-24 salad showpieces must refuse.

## G-5 · v3 path-action audit — GATED forward item (probe 28)

Probe 28 measured the geodesic structure: real sentences beat their own
shuffles on path action in 81% of cases (1.443 vs 1.520; random 1.766).
Implement `path_action(continuation)` and the composite score
coherence − λ·action behind a flag, λ default from a small sweep.
- **Promotion inequality only:** v3 becomes default iff selectivity gap AND
  emitted coherence are both ≥ v2's, with salad refusal still 100%.
  Otherwise v2 stays default and HANDOFF records the sweep.
- **Sentinel test:** real-beats-own-shuffle ≥ 75% on 300 sentences (the
  probe-28 structure must keep existing under any meaning-geometry change).

## G-6 · `examples/demo_generate.py`

< 30 s, the generative existence proof: produce novel derived surfaces with
correct allomorphs (including one epenthesis case); decode a bound vector
back to its sequence; refuse a SUM-bound vector structurally; continue an
attested prompt; refuse a word-salad prompt in plain language.

## G-7 · Close-out

`HANDOFF.md`: measured numbers, deviations, tie-break and λ sweep results,
and the next-frontier ranking (standing: word-field workshop — a_mem at the
word rung, probe-28's brick; dense-space crowding at grid > 47; local
Wikipedia corpus for the registry; Morfessor/SIGMORPHON benchmark as the
parallel credibility run). **Stop.**

## Non-goals
Fluent-prose pursuit (wrong rung for count machinery — decided), the
word-field workshop (future project, not a module), agent shell, external
LM integration, performance work.
