# CLAUDE.md — working instructions for this repo

You are continuing **ElfIX**: a phonology-first language model where units are
points and trajectories in a feature space that *sound already has*, higher units
**form themselves** from the geometry, and **every value traces back to a count you
can point at**. Read `SPEC.md` first — it is the contract. This file is how to work.
`SCORECARD.md` is the one-page competence map: what the gates decided (sound for
STRUCTURE, distribution for WHAT-COMES-NEXT), every win/null and every earned constant.

## The six laws (inviolable — `elfix/laws.py`)

1. **Earned geometry only.** No constant whose value comes from outside the data.
   If you add a threshold, it must be derived from a corpus measurement or an
   articulatory fact, and you must say which in a comment. Banned origins: φ,
   golden ratio, Mersenne, Ω/omega, pi2, "Dual-13", any cosmological number.
   (`laws.assert_earned` will trip on these.)
2. **Absence ≠ zero.** Unseen-enough stays *absent*, never present-at-zero.
3. **One source of truth.** Derived sets are *views* of one ground table,
   re-derived and asserted in test — never hand-listed.
4. **Never a centre without its width.** Any unit position carries a spread.
5. **Ternary evidence.** attested(+1) / silent(0) / evidenced-against(−1).
6. **Readable AND self-forming — no gradient black box in the core.** Higher rungs
   form from the geometry of the data (hashing, clustering, contour cues), not
   from an opaque optimiser. This is the research bet; protect it.

## What is built (and where)

| Tier | Module | Status | Provenance |
|---|---|---|---|
| 0 substrate | `substrate/features.py`, `substrate/vectors.py` | DONE; **injective as of the rhotic/offglide fix** (was 15 vowels → 10 points) | ELfIX phoneme_features; SPE, Feature Geometry |
| 1 unit-as-point | `units/unit_point.py` | DONE (`box_signature.py` RETIRED — no consumer, diagram constants) | ElfIX relational |
| 2 trajectory | `trajectory/trajectory.py` | DONE | ElfIX slope_source; Browman & Goldstein; Clements |
| 3 emergent units | `emergent/emergent_unit.py` | CORE DONE + gate; syllable F1≈0.93 | NEW→original; Kohonen, BPE contrast |
| 3 appendix units | `emergent/appendix.py` (additive) | DONE; morpheme F1 0.38→0.63 | NEW→original; Morfessor/BPE contrast |
| — syllable gold | `syllable.py` (Maximal Onset) | DONE (eval support) | ElfIX onset_legality; Kahn/Selkirk MOP |
| — earned sonority | `sonority.py` (phonotactic) | DONE | Sonority Sequencing; earned from clusters |
| 4 all-pairs | `compare/all_pairs.py` | DONE (counted) | Mind_Space EXAMINE; Vaswani et al. |
| 5 decaying carry | `carry/decaying_carry.py` | DONE; rate earned 0.67 | GCL relational_tension |
| 6 shape routing | `routing/shape_routing.py` | classes + ops EARNED (accumulate/boundary), falsified | GCL geometric_ops; MoE |
| 7 readout | `readout/recognition.py` | DONE (ported) | cleankit recognition+temperature |
| 4–7 + rung | `forward.py` (word + utterance pass + rung) | DONE; ops earned + gate carry (salience) | NEW→original; Law 4/6 |
| — generative floor | `predict.py` (counted next-word) | DONE; phono backoff (null), carry cache (+topical), acquired store, FACTORED base (+0.72, opt-in) | NEW→original; n-gram + recognition + Brown 1992 |
| — running text | `running_text.py`, `make_corpus.py`, `data/corpus.txt` | DONE; 1M Brown words, self-built lexicon | NEW→original; Brown via NLTK |
| — lexicon growth | `lexicon/` (4 stages) | v1 DONE; 95.8% regular, inferred store | NEW→original; Morfessor contrast |
| — I/O wrap | `session.py` (read<->respond loop) | DONE; learn+remember+respond, live locator, topic | NEW→original; Law 6 |
| — semantic layer | `semantic.py` (distributional classes + topical carry) | DONE; topic by class +0.39 bits; prev-class pooling null | NEW→established; Harris/Firth, Brown 1992 |
| — OOV closure | `oov.py` + `session._grow` | DONE; read pronounces new words live, context places them; morphology→class bridge weak | NEW→original; the two halves joined |
| — constituent layer | `syntax_tree.py` (parser + controllers) | DONE; brake reduces class-stall, parse-scoping ~= flat window | NEW→established; Magerman & Marcus + Tier-3 recursive |
| — POS induction | `syntax_tree.py` (`RoleTagger`) | DONE; earned verb/noun via functor context (verbs 0.80 vs nouns 0.13); types the locator | NEW→established; Schütze 1995 / Brown 1992 |
| — earned headhood | `syntax_tree.py` (`head_of`, `Node.head_word`) | DONE; heads NAME, edges BOND; compounds 90% right-headed (substitutability) | NEW→established; distributional headhood |
| — factored floor | `scripts/gradient_compartment.py` | MEASURED; class-factored counted model +0.81 bits over the word-bigram floor | NEW→established; Brown 1992 class LM |

## Run it

```bash
python scripts/milestone1.py     # Tier 3 gate on MORPHEME boundaries -> PASS/FAIL
python scripts/syllable_eval.py  # the geometry on SYLLABLES (its native job)
python -m elfix.forward        # Tiers 4-7 + the morpheme->word rung, on a word
python scripts/lexicon_gate.py   # dict-growth gate: compose OOV pronunciations
python -m elfix.running_text     # load corpus.txt, self-build lexicon, tag tokens
python -m elfix.predict          # inspectable next-word generation + the semantic locator
python -m elfix.session          # the I/O wrap: read (learn+remember) <-> respond, + the live locator
python scripts/predict_backoff.py   # phonological backoff, MEASURED: no lift vs unigram (the residual is semantic)
python scripts/carry_predict.py     # carry-conditioned prediction: +0.38 bits TOPICAL signal (accumulated context wins)
python scripts/acquire.py           # TRAIN THROUGH INPUT: +10% ppl on unseen text, governed (attested frozen, self quarantined)
python -m elfix.semantic            # earn distributional (MEANING) classes by co-occurrence clustering; show a few
python scripts/semantic_gate.py     # prev-class pooling MEASURED: null for sound AND meaning (next ~ marginal)
python scripts/semantic_carry.py    # TOPIC by class: +0.39 bits over word-carry -- the semantic layer's predictive home
python scripts/semantic_k.py        # earn K: distortion has NO clean elbow -> K is legitimately a resolution DIAL (a result, not a shortfall)
python scripts/modulus_probe.py     # earn the congruence modulus: base > alphabet or no modulus can help; no SMALL p is an identity key
python scripts/capacity_probe.py    # the +/-8 ternary accumulator claim, MEASURED: fits voicing/sonority, OVERFLOWS the Law-5 valence (7.17%)
python scripts/earned_capacity.py   # invert it: the corpus picks 3,4,5,6,9,11,14,27 -- never 8; and prime 2c+1 is the base rate, not evidence
python scripts/oov_gate.py          # morphology->class bridge MEASURED: weak (15% to ceiling) -> OOV placed by CONTEXT
python scripts/oov_grow.py          # OOV validated: a new word costs 33 bits cold, -9.5 bits on return (learned from one read)
python scripts/oov_place.py         # OOV re-placement crossover: context beats morphology after ~2 reads (->91% by 80)
python scripts/adaptive_topic.py    # entropy-adaptive topic weight: HURTS perplexity (the floor IS perplexity-optimal)
python scripts/generate_quality.py  # above the floor by the RIGHT metric: content 36->84%, on-topic 63->84%, repeat 11->1%
python scripts/syntax_scaffold.py   # the grammatical scaffold: class predicts next-CLASS (+0.53 bits) where IDENTITY was null
python scripts/grammar_quality.py   # the scaffold restores fn-rate 16->53% (real 49%), gram-cost 8.99->5.32 -- sentence-shaped
python scripts/sentence_arc.py      # subject->predicate ARC: nominative pronouns early, accusative late; boundaries on predicate tails
python scripts/sentence_quality.py  # bounded + arced generation: run-on 28->~12 words, subjects 0.32 before objects (real 0.28/0.61)
python scripts/ngram_ceiling.py     # the 1st-order ceiling: higher-order class n-grams add ~0 (it's HIERARCHY, not context-length)
python scripts/constituents.py      # constituent/stack PREP: recursive PMI bracketing builds real NPs/PPs (flat chunking failed)
python -m elfix.syntax_tree         # the BUILT bracketer: parse real sentences -> trees + tightest class-bonds (more->than, has->been)
python scripts/parse_guided.py      # gate the closure brake: reduces the class-stall, but parse-scoping ~= a flat class-window (trade-off)
python scripts/clause_guided.py     # head-AWARE clause brake (earned verb/noun): NULL for generation -- verb-rate already ~real, no deficit to fix
python scripts/gradient_compartment.py  # the ORACLE ablation (size the gradient compartment: 2.65 bits, 25%) + the FACTORED counted model (+0.81 bits over the floor)
python scripts/io_loops.py          # the deployed factored base on live read<->respond loops: floor vs factored surprisal, typed locator, where it helped
python scripts/converge_probe.py    # Mind_Space converge points, MEASURED: lexicon is anti-self-similar (OCP) -> shelved
python scripts/carry_revalidate.py  # re-validate the Tier-5 carry rate on running text
python scripts/routing_ops.py    # earn Tier-6 op semantics from running text (falsified)
python scripts/showcase.py          # the WHOLE system on real inputs: topic + typed locator + bounded arced response + data
python -m pytest -q              # tests + doctests, all green
```

**Two results, both on the full 135k corpus:**

- **Morphemes (`milestone1`): PASS.** Contour alone F1 **0.384** vs BPE **0.252**
  (126,052 words, 38,639 gold boundaries); contour recall is capped at **48%** —
  the other 52% of boundaries have *no* sonority seam (played=play+d). Two Tier-3
  moves tested: the **subtractive** `discover()` gate is a measured **no-op**
  (+0.00002 F1 — it can only withhold seams); the **additive** appendix units
  (`emergent/appendix.py`) **lift recall 0.48 → 0.97 and F1 0.384 → 0.626**,
  beating granularity-matched BPE (~0.33) decisively. The geometric move BPE
  cannot make: voicing-neutral shapes merge the -s/-z and -t/-d **allomorphs**
  into one appendix unit. Caveat: the positives-only gold can't count monomorphemic
  false positives, so 0.626 precision is optimistic (the BPE comparison is still
  fair — same gold). The exact productivity threshold stays an open question.
- **Syllables (`syllable_eval`): strong win.** On a corpus-earned Maximal-Onset
  gold the geometry recovers syllable boundaries at F1 **~0.93 vs BPE ~0.40** (with
  the earned phonotactic sonority; ~0.86 with the phonetic scale), and syllable
  *count* at **90.5%** exact. This is the geometry's strongest evidence: on the job
  it is built for (sonority → syllables), earned sound-shape clearly beats
  orthographic frequency. KEY: syllable boundaries use the maximal-onset
  convention (`syllable_boundaries`, seam *at* the trough, earned phonotactic
  sonority); morpheme boundaries use `geometry_boundaries` (seam at trough **+1**,
  phonetic sonority, + coda-reversal appendix seams). The two genuinely differ by
  the intervocalic-consonant ±1 (run·ing vs ru·ning); one contour yields both.

The loaders auto-detect the full `cmu_preprocessed.txt` when present in `data/`
and fall back to the bundled 25k sample otherwise (see `data/README.md`).

## The discipline (do not skip)

- **Never climb past a failed gate.** Tier 3's gate (`scripts/milestone1.py`) is
  the cheapest place to learn the thesis is wrong. If it fails on the full corpus,
  fix Tier 3 — do not build Tiers 4–7 on a hollow claim.
- **Assert, don't assume.** New invariants get a test that re-derives them
  independently (Law 3). Open questions stay *open in a docstring*, not silently
  closed.
- **Keep citing provenance.** Every module header tags where it came from
  (`[ElfIX]`, `[GCL]`, `[cleankit]`, `[Mind_Space]`, `[NEW→established: cite]`,
  `[NEW→original]`). Maintain this. It is how this project stays honest about what
  is reused vs new.

## The next tasks, in order

1. **~~Run the gate on the full corpus.~~ DONE.** PASS holds at 135k words and
   does not regress (geometry F1 0.384 vs BPE 0.252; sample was 0.371). Loaders
   now auto-detect the full file. The *next* task is where the real work is.
2. **~~Enrich Tier 3 with the recurrence signal.~~ DONE — with an honest
   negative, and a strong positive elsewhere.** Wired `discover()` into the seam
   via `geometry_boundaries_emergent` (keep a contour seam only where a confirmed
   emergent unit ends). Result: **no-op on morphemes** (+0.00002 F1) — the gate
   is *subtractive* and the morpheme error is recall, not precision. Then, per the
   "test on the job it's built for" reframe, built an earned Maximal-Onset
   syllable gold (`elfix/syllable.py`) and `scripts/syllable_eval.py`: the
   geometry recovers **syllables at F1 ~0.93 vs BPE ~0.40** — the real first
   evidence for the thesis. The SUBTRACTIVE gate stays a no-op, but the ADDITIVE
   form (task 4) succeeded.
3. **~~Earn the placeholder constants (Law 1).~~ DONE — all three.**
   - **Sonority** (`elfix/sonority.py`): earned a PHONOTACTIC scale from corpus
     cluster orderings (Sonority Sequencing, via non-circular MOP syllabification).
     Finding: it cleanly earns the sonorant hierarchy + the obstruent/sonorant gap,
     but puts fricative<stop (the /s/ appendix). Adopted as a **dual scale** —
     phonetic (`features.sonority`) for the morpheme cue, earned phonotactic for
     the syllable contour. Lifted syllable F1 0.86 → **0.93**; morpheme unchanged.
   - **Carry rate** (`carry/decaying_carry.py`): `measure_decay_rate` earns it from
     the half-life of phoneme contextual MI (~1.72 phonemes → r ≈ **0.67**, was a
     placeholder 0.6). Caveat: within-word dictionary measure; re-validate over
     running text at integration (task 4).
   - **Arc quantum** (`auto_quantum`): VALIDATION FAILED then fixed — the
     `max(0.15, …)` floor was binding (earned place width ~0.111 < 0.15), so the
     quantum was effectively magic. Removed the floor + sample cap + magic
     fallbacks. OPEN: place (~0.111) and manner (~0.222) want different widths;
     `describe` still uses one (flagged, per-axis quanta is the designated fix).
4. **~~Additive self-formation.~~ DONE — the thesis's strongest morpheme result.**
   `emergent/appendix.py`: self-forming appendix units, promoted by voicing-neutral
   shape recurrence across distinct stems (NOT dictionary lookup — that would be
   the gold's own criterion, circular). They PROPOSE the boundaries the contour
   misses → recall 0.48→0.97, F1 0.384→0.626, vs matched BPE ~0.33. The geometric
   novelty (merging -s/-z, -t/-d allomorphs by feature-shape) is what frequency
   cannot do. OPEN: (a) the productivity threshold (`frac=0.5`) is corpus-relative
   but not first-principles earned — robust but not closed; (b) precision is
   optimistic on the positives-only gold. A legal-coda stem gate was MEASURED and
   REJECTED (only ~11% FP cut for ~3% recall loss — most monomorphemic stems end in
   legal codas); the precision limit is structural (needs stem-distributional
   evidence, not geometry), so a richer gold is the real fix, not another gate.
5. **Tidy (DONE):** per-axis arc quanta — `describe` now takes `(place_q,
   manner_q)` = (0.111, 0.222) via `auto_quanta`, retiring the single-quantum
   approximation flagged in task 3.
6. **~~Wire Tiers 4–6 into a single forward pass + morpheme→word rung.~~ DONE.**
   `elfix/forward.py`: one readable pass over a word — syllable units (centre+
   width), Tier 4 all-pairs attention over them sharpened by Tier 7 recognition,
   Tier 5 leaky-integrator carry, Tier 6 shape routes, then the **rung**: `compose`
   lifts child units → a word unit (centre = reliability-weighted blend, width =
   within+between dispersion). Level-agnostic — the same rung does syllable→word
   AND morpheme→word. Demo (`python -m elfix.forward`) shows the segmentations
   genuinely differ (running = ru·ning syllabic vs run+ing morphemic) and the full
   pass (attention, carry, recognition→T, routes). Tier 6 was tightened: routing
   classes are now EARNED by recurrence (min_count, no magic top-k), readable
   (`class_shape`/`class_position`), and a NOVEL arc routes to -1 — the same
   novelty Tier 7 reads as low recognition (routing and readout agree). (SUPERSEDED:
   running text is now acquired and loaded, the carry rate re-validated, the word
   rung runs across sentences, and the Tier-6 op SEMANTICS are earned + falsified —
   all in "Next directions" below. This task's within-word / single-word-utterance
   caveats no longer hold.)

## Next directions (running text now in place)

> **>> ~~THE CONGRUENCE / CAPACITY PROBES.~~ RUN — two retirements, one real Tier-0 bug.**
> Three probes (`modulus_probe.py`, `capacity_probe.py`, `earned_capacity.py`), all in
> `converge_probe.py` style — report, don't assert. What they settled:
> - **`box_signature.py` RETIRED, and the reason is the interesting part.** Its SPEC gate
>   ("does it earn its keep once Tier 2 exists?") had never been run because it had **zero
>   consumers** — imported by nothing, tested by nothing, exported by nothing. With no
>   downstream metric there was nothing to gate against, so the open question was not open,
>   it was *unasked*. Its marker sets came off a 4×4 diagram (Law 1's banned species). Deleted,
>   scorecarded, SPEC Tier 1 closed. A congruence signature replaces it ONLY if a real
>   identity-key need appears; none does.
> - **The modulus is earned, and the BASE matters more than the modulus.** Feature codes run
>   0..35, so the polynomial is injective only for base x ≥ 36; below that the collision rate
>   plateaus (x=2 → 92.5%) *no matter how large p grows*, because it collides before the mod is
>   applied. Primality of x buys nothing. With x=36 and p from the birthday rule at a STATED
>   0.2% tolerance (p = 31,513,003), the measured rate decomposes cleanly:
>   **24.91% true homophones (English, irreducible) + 2.76pp bundle merge (substrate) +
>   0.25pp hash (tunable)**. And no SMALL modulus is an identity key: 126k words into 17
>   buckets is 100% collision. The mod-6 CRT packing and a ℤ/17 accumulator are **two
>   different objects**; treating them as one was the error.
> - **±8 IS NOT EARNED — by any valence.** Three Law-5-shaped ternary valences measured:
>   voicing and sonority fit ±8, but **attestation — the valence Law 5 literally describes —
>   overflows on 7.17% of words**. Inverting the question, the corpus picks c ∈ {3,4,5,6,9,11,
>   14,27}; never 8. The "17 is forced because neighbours 33 and 9 are composite" argument was
>   reasoning from a *proposed* capacity. And primality is not evidence: **56% of the odd
>   numbers in that range are prime**, so prime hits are the base rate. Two further corrections,
>   both computed: at budget 0 the attestation valence earns **55, composite — no field, no
>   transform at all**; and shift-only NTT twiddles are **not** a Fermat-prime property —
>   2 is a PRIMITIVE ROOT mod 11, 13 and 19 but **not** mod 17 (order 8). What Fermat primes
>   buy is cheap modular *reduction*, a different saving. The whole 17 → Fermat → 17-gon chain
>   is decoration; it fails the "load-bearing?" test that keeps φ-chains out.
> - **THE BUG THE PROBES FOUND BY ACCIDENT (Tier 0, now FIXED).** The feature bundles could not
>   distinguish `EH`/`EY`, `AH`/`ER`, `AO`/`OW` — and in the ℝᵈ encoding it was worse, because
>   `_HEIGHT` mapped `"diphthong"` to 0.5 (= mid), erasing the diphthong exactly where it entered
>   the geometry: **15 vowels landed on 10 distinct points**, with EY/EH/AY on one and OW/AO/OY
>   on another. Tier-2 trajectories through *bet* and *bait* were the same path. FIX: two
>   articulatory features, `rhotic` (ER) and `offglide` (front/back/None), retiring the
>   category error of `height="diphthong"` — a diphthong's glide is a DIRECTION, which is the
>   trajectory-shaped reading Tier 2 already assumes. DIM 8 → 10. **Now injective: 15 → 15.**
>   Gates held EXACTLY (syllable F1 0.9325, morpheme contour 0.3837, +appendix 0.6256, quanta
>   (0.111, 0.222) — all unchanged to 4 dp), because the sonority contour reads only `sonority`,
>   which is 5.0 for every vowel. So the fix is free where the gates look and repairs the
>   representation everywhere else reads. Four tests that hardcoded `8` now import `DIM`
>   (Law 3). OPEN: nothing downstream yet *exploits* the two new axes — the gain is
>   representational, and a probe that measures it is the natural follow-up.

> **>> ~~NEXT BUILD: the CONSTITUENT / STACK mechanism.~~ DONE — BUILT, gated, honest
> (two measured findings, neither a clean win).** `elfix/syntax_tree.py`: a `SyntaxTree`
> recursive agglomerative bracketer (merge the strongest-binding adjacent span FIRST —
> the Tier-3 emergent move lifted to syntax, producing NESTING = a tree = a stack; binding
> = earned class-pair PMI, boundary at the PMI=0 chance line, mean constituent length
> earned analytically from `p_bond`), plus a `ConstituentController` for parse-guided
> generation. The findings:
> - **The parser WORKS on the extreme bonds, ~chance on ordinary ones** (`python -m
>   elfix.syntax_tree`): it brackets real Brown sentences into readable trees and merges
>   the tightest grammatical collocations FIRST (`more→than`, `has/have/had→been`,
>   `does→not`, `(blue eyes)`, `(one week)`, `((how much) ((they knew) (about her)))`).
>   But a right-attachment proxy (does it merge det/prep onto their right complement?) is
>   AT/BELOW chance (52% vs 58% random) — the greedy class-PMI binder nails high-PMI
>   collocations but not average det/prep attachment. A STARTING parser, not a strong one
>   (head-awareness the flagged fix), exactly as the scout predicted — now MEASURED.
> - **The closure BRAKE reduces the class-STALL, but the PARSE-SCOPING is not yet
>   load-bearing** (`scripts/parse_guided.py`). The controller penalises re-entering the
>   OPEN constituent with a repeated head-class — the CLASS stall (different words, same
>   classes: 'president kennedy senator johnson …') that `no_repeat` (exact words) and
>   `grammar` (next class) cannot catch. It moves class-2cycle 18%→15% and class-run
>   1.34→1.12 toward real text (0% / 1.01). BUT the decisive control — a FLAT class-window,
>   no phrase-scoping — does the same job slightly harder (2cycle →11%) at a small on-topic
>   cost; the constituent scoping is GENTLER (it resets at phrase boundaries, so a class may
>   RECUR across phrases → on-topic 77% vs the window's 74%) but does NOT dominate. A real
>   trade-off, not a clean win: the greedy class-PMI binder is too coarse for the
>   phrase-scoping to beat a flat window. So the brake is a usable OPT-IN lever
>   (`Session.respond(constituency=…)`, default OFF) and the PARSE is not yet earning its
>   keep for generation — kept like the phono-backoff / adaptive-topic negative controls.
> THE REMAINING FRONTIER (unchanged in direction, SHARPENED by the measurement): a
> HEAD-AWARE binding signal (the class-PMI v1 has no notion of head/projection, which BOTH
> findings fingered) + a real evaluation (a treebank, not a proxy). With a stronger parser,
> the predicate-owed half of parse-guided generation ('don't run past a closed subject-NP
> until a verb is emitted') becomes testable; the v1's closure brake already proves the
> wiring.

> **>> ~~HEAD-AWARE binding.~~ PROTOTYPED — one clean WIN, one informative NULL, one meta-
> finding.** Followed the frontier above. Three results:
> - **`RoleTagger` (the WIN): earned PREDICATE/ARGUMENT (verb/noun) POS from FUNCTOR
>   context.** The topical distributional classes do NOT carry POS (verbs/nouns cluster by
>   topic; a class-level N-V 2-colouring washes out, measured). A 2-hop bridge from the
>   single most-frequent word ('the', a determiner) earns it cleanly: `the → nouns →
>   functors-that-precede-verbs → verbs`. Verbs score 0.80 vs nouns 0.13; the functor split
>   is textbook (nominal: the/a/this/his; verbal: has/had/he/she/i/they). Counted, one
>   anchor, no gradient. NOW TYPES THE LOCATOR (`Session.locator_typed` → 4-tuple with the
>   POS role): an unexpected ARGUMENT is a new entity, an unexpected PREDICATE a new relation.
> - **`ClauseController` (the NULL): clause-completion tracking does nothing for generation**
>   (`scripts/clause_guided.py`). Built to brake argument-stacking while a verb is OWED ('don't
>   run past an open subject until a verb arrives'). But VERB-RATE IS ALREADY ~REAL (~58% =
>   real text) in every config, even verb-starved ones — the grammar+topic levers already
>   produce realistic verb rates, so there is no verb-deficit stall to fix. The residual stall
>   is surface CLASS-recurrence, and a flat class-window handles it best (2cycle →6% vs the
>   structural brakes' ~10-15%). Kept opt-in, the apparatus + measured null.
> - **THE META-FINDING: structural generation-control loses to a flat class-window.** Two
>   natural structural controllers were now gated — phrase-saturation (`parse_guided`) and
>   clause-completion (`clause_guided`) — and NEITHER beats a dumb flat class-window on the
>   stall. The earned signals are real (the head rule is right for det/prep; the RoleTagger
>   is clean), but they are NOT load-bearing for generation, because the failures they target
>   (mis-attachment, verb-less clauses) are already handled by the local levers. With 'grammar
>   overshoots / the floor is perplexity-optimal', the honest verdict: WITHIN the counted/
>   no-gradient constraint, structural generation-control is largely exhausted — the simple
>   window wins and the residual is the irreducible semantic gap. The durable win is the
>   RoleTagger (its home is ANALYSIS, not generation). The one open structural fork is a
>   genuinely stronger parser (treebank-supervised or non-greedy), which strains the
>   no-gradient bet — see SCORECARD 'Compartmentalizing the gradient'.

> **>> ~~COMPARTMENTALIZE step 1 (the oracle ablation).~~ RUN — and it found UNCLAIMED
> COUNTED TERRITORY.** `scripts/gradient_compartment.py`, two parts, both leak-audited:
> - **The DECOMPOSITION (size + locate the compartment):** the floor's 10.44 bits/word =
>   **6.99 category** (which KIND of word — 67%) + **3.45 within-class**, of which the topic
>   carry recovers 0.80, leaving a **2.65-bit (25%) residual** irreducible by class+topic —
>   spread across BOTH open-class channels (predicates 3.28 / arguments 3.45), NOT just new
>   entities. That is the honest size-and-shape of anything a walled gradient would earn.
> - **The FACTORED COUNTED MODEL (the surprise):** P(w|prev) = P(class(w)|class(prev)) x
>   P(w|class(w),prev) — category by the class-bigram, word by its within-class share —
>   **beats the word-bigram floor by +0.81 bits (~1.7x perplexity)**, unk-leak PAID, sb/lambda
>   dev-earned. The win is pure GENERALIZATION: sparse contexts +1.78 bits, dense −0.25
>   (hence the earned lambda=0.3 interpolation). RECONCILIATION: the old prev-class-pooling
>   NULL (semantic_gate) stands — pooling throws away word identity; the FACTORED form keeps
>   it (Brown 1992's actual class LM). The mechanism was wrong, not the classes. So "the
>   floor" was the WORD-BIGRAM ceiling, not the counted ceiling. **~~NEXT BUILD: wire the
>   factored model into `Predictor`.~~ DONE — deployed opt-in.** `Predictor.attach_factored`
>   (+ `FactoredBase`) interpolates the floor with the factored model at the dev-earned
>   lambda in BOTH `prob` (scoring) and `predict` (ranking); `Session(factored=True)` turns
>   it on. OFF by default, so every existing gate is unchanged; deployed it reproduces the
>   win through the real path: **+0.72 bits/word via `Predictor.prob`** on 22,755 held-out
>   tokens (the topic-within-class path adds the rest through the existing `sem_carry`).
> - **HEADHOOD EARNED (the same session, the analysis side):** the head of a phrase, by the
>   SYMMETRIC substitutability test (which child accepts the pair's outer context on the far
>   side): nominal compounds **90% right-headed** ('(white house)'->house at 0.94 vs 0.04),
>   the exceptions themselves correct ('(president kennedy)'->president, a title
>   construction). Verb-headed pairs FAIL the substitution test (34%/58%) for a principled
>   reason: arguments SATURATE — '(took place)' continues like 'place', not like bare 'took'
>   — modification is distribution-preserving, argument-filling is distribution-TRANSFORMING.
>   Resolution of the head-aware puzzle: **heads NAME (category), edges BOND (distribution)**
>   — the v1's two-edge representation was operationally right; head-to-head binding measured
>   worse and stays a prototype. `head_of` now uses three earned rules (content-over-functor /
>   predicate-over-argument via RoleTagger class scores / right-headed default), every parse
>   carries categorial heads (`Node.head_word`: '((how much) ((they knew) (about her)))' ->
>   knew), and the entropy tiebreak that got '(blue eyes)' wrong is retired to a diagnostic.
> Everything else below is DONE; the system is green at 114 tests + doctests.

> **>> ~~IMMEDIATE NEXT BUILD: phonological backoff for `elfix/predict.py`.~~ DONE —
> a robust, INFORMATIVE NEGATIVE.** Built the sound-class backoff (`PhonoBackoff` in
> `predict.py`): when the lexical bigram is sparse, pool the continuations of the
> context word's earned arc-shape class (router route, keyed on the morphologically-
> loaded final arc) — class-based smoothing (Brown 1992) with EARNED phonological
> classes. Falsification gate `scripts/predict_backoff.py`: on held-out sparse
> contexts the sound-class does **NOT** beat the sound-blind unigram — it is ~0.3–0.5
> bits/word **worse**, in every regime (context never seen / seen <5×) and under both
> keys (`final` dense, `route` 77% singletons → collapses), robust to token- vs
> type-weighted pooling. WHY (the finding): a final-arc class mixes syntactic
> categories (the same vowel+nasal coda ends `-ing`, `in`, `sun`), so its pooled
> continuation collapses to the global marginal — the content→function transition
> the unigram already captures. **Next-word identity is governed by SYNTAX/SEMANTICS,
> which the previous word's SOUND does not encode.** This is the semantic-locator
> thesis from the negative side: the ~10 bits/word residual is irreducible by
> phonology — that residual IS the semantic layer's job, now *measured* not assumed.
> So the phono tier is OPT-IN and OFF by default; it is kept as the inspectable
> apparatus + the negative control that produced the measurement. The generator fails
> readably, exactly where the design said it would.

The ladder is complete and green end-to-end. The **running text is acquired and
loaded**: `make_corpus.py` built `data/corpus.txt` from the Brown corpus (54,756
sentences, 1.0M words, 98.4% CMU coverage, ElfIX contract — one sentence/line,
lowercased, `[a-z' space]`, internal apostrophes kept, hyphens split).

- **~~Running-text loader.~~ DONE.** `elfix/running_text.py`: `load_utterances`
  (corpus → sentence-delimited word lists), `tag_utterances` (each token →
  phonemes + tag attested/inferred/oov), and `grow_store` — the self-building
  lexicon over OOV, weighted by running-text **frequency** (the corroboration the
  holdout gate lacked; `FREQ_CONFIRM` promotes a recurring OOV to confirmed). On
  the full corpus: 98.42% attested → **98.62% with the inferred tail** (1,434 OOV
  recovered, 257 confirmed, 15 rejected). `python -m elfix.running_text` to see it.
- **~~Carry rate re-validation (Tier 5).~~ DONE — 0.67 VALIDATED.**
  `scripts/carry_revalidate.py` measured contextual-MI half-life over the corpus
  (cross-word phoneme streams + syllable + word granularity) with a SHUFFLE control
  for finite-sample bias. Debiased rate ≈ **0.67 at every granularity** — the
  within-word proxy was sound. KEY methodological catch: the RAW curves (syllables
  0.75, words 'no halving') falsely suggested long lexical memory, but that was
  bias (floors 1.04 / 3.06); the shuffle control corrected it. A small REAL
  long-range word residual (~0.2 bits topical context) remains — the designated
  next refinement is a second, slower carry for it. `EARNED_RATE` unchanged (now
  validated, not a proxy).
- **~~Word rung across sentences + Tier-4/5 between words.~~ DONE.**
  `forward.forward_utterance(tokens)`: the SAME level-agnostic machinery one level
  up — each in-vocab word is a unit (itself a syllable→word rung), Tier-4 attention
  runs BETWEEN words, Tier-5 carry runs ACROSS them at the validated 0.67 (reset per
  utterance), Tier-7 recognition = fraction of words attested, and the rung composes
  the words into an UTTERANCE unit. The full phonemes→syllables→words→utterance
  hierarchy now runs on real Brown sentences (`python -m elfix.forward`).
- **~~Tier-6 op semantics.~~ DONE — the spec's last open question, RESOLVED.**
  `ShapeRouter.learn_ops` reads each class's operation off running-text behaviour
  (`scripts/routing_ops.py`): H(next | class). Predictive shapes (low entropy)
  ACCUMULATE; shapes whose continuation is as uncertain as the global baseline are
  BOUNDARY (reset). The two regimes are DISCOVERED by 2-means on the entropy (no
  magic threshold). FALSIFIED: the dispositions align with real structure —
  boundary-op classes are **59% word-final**, accumulate-op **9%** (50-pt gap);
  the boundary shapes are word-final open syllables, the accumulators word-internal
  predictive arcs. So the op SET is discovered AND its SEMANTICS are earned, exactly
  as the spec said they would be once a downstream task existed.
- **~~Gate the carry by shape (the Tier-6 wiring).~~ DONE — with an honest fix.**
  `forward_utterance(tokens, router=...)`: shape selects the op as a SALIENCE on the
  carry update — a word folds in weighted by its mean arc predictiveness (content/
  multi-syllabic words carry strongly, short/function words little). NOTE: the naive
  hard-reset-at-boundary was MEASURED and REJECTED — word-final arcs are nearly all
  boundary-disposition, so it flushed every word (22/22) and destroyed the cross-word
  memory; lexical context persists at 0.67 across boundaries (carry_revalidate), so
  the op modulates WEIGHT, not reset. Honest caveat: the salience spread is modest
  and tracks predictiveness (≈ multi-syllabic content). The ladder is now closed:
  every tier 0–7 done, self-forming on running text, every constant earned or flagged.
- **Generative floor (`elfix/predict.py`) — analyzer → GENERATOR, the start of the
  semantics phase.** v1: a COUNTED next-word model (bigram + unigram backoff) over the
  sound-represented words; `predict` returns ranked candidates with prob/count, the
  continuation ENTROPY (confidence), and provenance (lexical/backoff); `generate`
  continues a seed, every step inspectable (Law 6 — no gradient). THE POINT (the
  author's reason for being off the gradient): the generator's own uncertainty is the
  **semantic locator**. `context_uncertainty` shows where counted context CAN decide
  the next word (collocations: los→angeles H=0, according→to) vs CANNOT (the H=11.8 /
  11,693 next words, a, and, his) — the high-entropy contexts are exactly where MEANING
  must attach. The system tells us where to build semantics, by failing readably.
  **~~(a) PHONOLOGICAL backoff.~~ DONE — NO LIFT (a robust, informative negative).**
  `PhonoBackoff` pools the bigram continuations of a context word's earned sound-class
  (router final-arc route); this equals `Σ_c' P(next|c') P(c'|c)`, the class-bigram
  marginalised — i.e. the `P(next-class|class)` signal folded into one counted dist.
  `scripts/predict_backoff.py` (held-out, train/test split): the sound-class is **~0.3–0.5
  bits/word WORSE** than the unigram on sparse contexts, in EVERY regime, robust to
  pooling scheme. The sound-class mixes syntactic categories, so it can't beat the
  function-word marginal the unigram already holds — next-word identity is SYNTAX/
  SEMANTICS, not encoded by the previous word's sound. Kept OPT-IN/off-by-default as the
  apparatus + negative control; it MEASURES the irreducible-by-sound residual (the
  semantic layer's job) and SHARPENS the locator from the negative side (`locator`).
  Tests in `tests/test_predict.py` cover the mechanism (pooling generalises across
  class-mates) independent of the real-data null.
  **~~(b) Carry-conditioned prediction.~~ MEASURED — the first POSITIVE in this arc.**
  `scripts/carry_predict.py`: the Tier-5 leaky integrator applied to WORD IDENTITY —
  a decaying cache of recent words, interpolated with the bigram, scored on a
  CONTIGUOUS held-out tail (cache needs running text). Result: **−0.888 bits/word
  (~46% perplexity)** at a slow timescale (rate ~0.995, the "second, slower carry"
  carry_revalidate flagged). RIGOUR: a sentence-order-shuffle control (keeps every
  within-sentence bigram + word frequency, base identical, kills only cross-sentence
  topical adjacency) decomposes the gain into **+0.510 non-topical** (local-frequency/
  domain adaptation) and **+0.378 genuine TOPICAL** persistence (survives only with
  real sentence order). So where the last word's SOUND failed (phono), ACCUMULATED
  word-memory over time SUCCEEDS — the predictive signal is topical, exactly where the
  locator pointed. **~~Wire it into `Predictor`.~~ DONE.** `CarryCache` (decaying
  word-memory, Tier-5 over identity, with a doctest); `predict(prev, cache=...)`
  interpolates the base distribution with the cache at the EARNED params (rate 0.997,
  beta 0.4, earned on a DEV split, reported on test — never tuned on test). Demo:
  after 'the', a cache holding {new, york, city} pulls 'york/city' to the FRONT of the
  prediction. HONEST CAVEAT (caught in the demo): carry is a PREDICTION win
  (conditioning on REAL context); in FREE generation the cache feeds on the model's own
  output and self-reinforces ('the the the ...', the cache-LM pathology), so
  `generate(use_carry=...)` defaults OFF — carry is for CONTINUING real text, not
  free-running. Tests cover the cache mechanics + the re-ranking.
  **~~(c) Train through input.~~ DONE — the model learns from what it reads.**
  `AcquiredContext` (in predict.py) is the DISTRIBUTIONAL sibling of
  `lexicon.InferredStore`: `Predictor.ingest(utterance, source)` folds (prev->next)
  transitions + word frequencies into a store SEPARATE from the frozen attested base.
  Prediction reads the attested+acquired VIEW via a Dirichlet backoff (`prob`,
  `_eff_bigram`, `_p_uni`) — low-count acquired evidence leans on the unigram, so it
  can only help. `scripts/acquire.py` (train/input/test, contiguous): reading a held-
  out input stream cuts surprisal on a FURTHER unseen test stream by **+0.157 bits
  (~10% ppl)**, with the online gap vs the frozen base WIDENING as it reads (chunk 1
  +0.00 -> chunk 5 +0.19). The three guarantees hold and are MEASURED: never OVERWRITE
  (Law 3 — the attested store is byte-identical after learning; all learning lives in
  the separate, re-derivable view), never COMPOUND (self-generated text, source='self',
  is QUARANTINED — recorded as malleable for audit but never predicted from and never
  self-confirming; feeding 5,000 self-transitions changes test surprisal by exactly 0),
  ternary evidence (confirmed >= ACQUIRE_CONFIRM external / malleable / absent, Law 2/5).
  So the model accumulates knowledge from input, governed against the contamination
  trap — the floor a semantic layer can stand on. NOTE: this is the LONG-TERM memory
  tier; the carry cache is WORKING memory; the attested base is ground knowledge — three
  timescales.
  **~~(d) The input/output wrap.~~ DONE — the capstone loop.** `elfix/session.py`:
  `Session` is a stateful read<->respond loop. `read(text)` tags each word
  (attested/inferred/oov), measures per-word SURPRISAL, updates WORKING memory (carry)
  and LONG-TERM memory (`ingest`, source='input' — it trains), records history.
  `respond(n)` continues CARRY-CONDITIONED on the real read context (the carry in its
  productive regime, not the free-run 'the the' loop; gentler gen-beta 0.2 + a no-
  ADJACENT-repeat rule earned from the converge probe's dissimilation finding), and is
  remembered as source='self' — QUARANTINED (the read/write asymmetry: learn from
  OTHERS, never from yourself). `locator()` surfaces the highest-surprisal words read —
  where counted/sound context could NOT predict, so MEANING carried it; on real Brown
  text it cleanly picks content words (drawer 31 bits, angrily, pawing, queer) over the
  predictable function words. Generation is honestly bigram-floor; the deliverable is
  the WRAP + governance + the live locator. Tests in `tests/test_session.py`.
  **~~OOV/vocab growth.~~ DONE — the loop closes (see "Closing the loop" below).**
- **~~THE SEMANTIC LAYER.~~ DONE — counted distributional meaning, and it EARNS its
  place.** `elfix/semantic.py`: a word's meaning is the company it keeps (Firth/Harris),
  counted directly — NO gradients (Law 6). `SemanticSpace` earns distributional classes:
  PPMI co-occurrence over frequency ANCHORS -> sparse-cosine k-means (geometric
  clustering of COUNTED vectors, the Tier-3 family, not backprop) -> 150 readable,
  coherent classes (ran~{took,run,went}, three~{two,five,years}, {c,mrs,dr}=names),
  each with centre+width (Law 4) and absence!=zero (Law 2). TWO mechanisms MEASURED:
  (1) **prev-class POOLING is a NULL** (`scripts/semantic_gate.py`) — deeper than the
  phono null: pooling continuations by prev's class beats neither the unigram for SOUND
  (−0.35) nor MEANING (−0.67), because next-word identity is the function-word marginal
  regardless of prev's category, and the unigram already holds it. So prev-class pooling
  is simply the wrong mechanism (for both). (2) **Topical CLASS memory WINS**
  (`scripts/semantic_carry.py`): `SemanticCarry` is the carry generalised from exact
  WORDS to distributional CLASSES — reading 'president' primes 'senate, congress' (its
  class). It adds **+0.527 bits/word OVER the word-cache alone** (base 10.76 -> word
  10.37 -> +class 9.84). That is the semantic layer's predictive home: it primes
  on-topic words the exact-word cache never saw — meaning attaching where the locator
  points, via TOPIC not category. WIRED: `predict(..., sem_cache=, sem_beta=)` blends
  the topical prior and SURFACES on-topic candidates (level '+topic'); `Session(space=)`
  reads classes, names the live TOPIC (`topics()`), and responds topic-aware. The
  closing symmetry: SOUND classes (phono) and prev-class pooling both null; MEANING as
  accumulated TOPIC is the signal — exactly where the whole arc pointed. Tests:
  `tests/test_semantic.py`.
  **~~SHARPENED.~~ DONE — the sticky-class fix.** The first classes had a 'sticky'
  class ({east,river,north}) that fired on every input because it held FUNCTION words.
  Two root-cause fixes: (1) the function-word SKELETON (top-80 frequent) is excluded
  from class MEMBERSHIP — anchors are the context AXES, only CONTENT words get classes
  (a class can't be sticky if it holds no function words); (2) `SemanticCarry` activation
  is CONTENT-WEIGHTED by self-information (-log2 P(w)) — reading 'senate' drives the
  topic, 'the' barely nudges it. Result (demo): topics are now sharp and distinct —
  'president/senate' -> {union,state,company},{washington,committee,office}; 'three
  million dollars' -> {million,hundred,twenty},{feet,years,miles}; 'mother/father' ->
  {her,my},{room,pay}, priming father/mother/wife/child. K: tried to EARN it from the
  distortion elbow (`scripts/semantic_k`) but there is NO clean knee (distortion ~linear
  in K) — word distribution is a CONTINUUM, so K is honestly a RESOLUTION DIAL (finer ->
  sharper topics, coarser -> more lift), flagged tunable not pretended-earned (k=300).
  The carry gate re-confirms the signal HOLDS at the sharper config: **+0.39 bits over
  the word-cache** (vs +0.53 at the old coarse/uniform config — the honest sharpness vs
  lift trade). OPEN: topic-typed locator, richer generation than the bigram floor.
- **~~CLOSING THE LOOP: OOV / new words.~~ DONE — and an honest negative inside it.**
  The two halves (sound-geometry vs distributional prediction) barely touched; the only
  place they MUST connect is a brand-new word (no distribution -> its first handle is its
  SOUND). `elfix/oov.py` + `Session._grow`: reading an unknown word PRONOUNCES it live
  from its shape (decompose -> known stem + suffix -> compose with the earned allomorphy,
  Half A's validated job), registers it (InferredStore), adds it to the predictable
  vocab, and the word then participates via CONTEXT (the acquired store). Demo: 'bloging'
  (never in CMU) is read once -> pronounced (6 phonemes, blog+ing) -> in vocab ->
  predictable. THE BRIDGE I HOPED FOR IS WEAK (`scripts/oov_gate.py`, the crux
  falsification): does a word's MORPHOLOGY place it in its true distributional CLASS,
  sight unseen? Measured **WEAK** — stem-inheritance lands only **0.10 cosine** from the
  true class vs 0.07 random (15% of the way to the ceiling; exact-match 3% ≈ the 3%
  majority guess; suffix slightly better at 26%). WHY: inflection SHIFTS a word's
  distribution off its stem ('kayaking' is not distributed like 'kayak'), and at 300 fine
  classes the syntactic signal is too fragmented for the suffix to pin. So the halves
  connect at PRONUNCIATION (sound's validated job), NOT at distributional placement —
  exactly consistent with the whole arc (sound governs STRUCTURE, distribution governs
  WHAT-COMES-NEXT). A new word is pronounced from its shape and placed by its context;
  the morphology->class shortcut is kept only as a flagged weak cold-start. Tests in
  `tests/test_session.py`. **~~Confirm OOV growth helps.~~ DONE (`scripts/oov_grow.py`):**
  on held-out text the grow mechanism pronounces+adopts **17% of OOV tokens** (the
  decomposable ones; the rest are proper nouns / novel roots — no known stem, by
  design no opaque G2P), and a grown word that RECURS drops from **33.1 bits cold to
  23.6 on return (−9.5 bits)** — reading it once makes it predictable. Small recurrence
  sample (OOV ~1% of tokens, mostly singletons) so the magnitude is modest; the
  CAPABILITY (the system no longer chokes on the new, and learns it, governed) is the
  point. **~~Richer placement once a word has accrued context.~~ DONE — the crossover.**
  `scripts/oov_place.py` measures placement quality vs how many times a word has been
  READ: the morphological cold-start is 0.19 cosine to the true class, but the word's
  own accumulated CONTEXT overtakes it after just **~2 occurrences** (0.20), climbing to
  0.49 / **91% exact-match by 80** (ceiling 0.475). So `SemanticSpace.place(cooc)` does
  distributional placement, and `Session._replace_grown` cold-starts a new word from
  morphology then RE-PLACES it by accumulated context once read >= `REPLACE_AT`=2 (the
  earned crossover): SOUND for the very first sighting, DISTRIBUTION once there is
  evidence — the competence map applied to the new word itself. Tests in
  `tests/test_session.py`. Root-novel OOV (names) stays out of scope (Law 6 — no opaque
  grapheme->phoneme).
- **Mind_Space converge points (`scripts/converge_probe.py`) — MEASURED, SHELVED.**
  Tested the `[Mind_Space]` "converge point" idea (a word's full-ℝ^d path folding back
  on itself — the spec's open Tier-2 question, full path vs 1-D contour) by pointing
  the Tier-4 comparator INWARD: non-adjacent phoneme self-returns (exact, threshold-
  free; + a near-return feature-distance sweep), vs a frequency-matched i.i.d. null and
  a within-word shuffle null. FINDING: the folding hypothesis is FALSIFIED — words
  self-encounter **0.86× frequency-chance** (repeat similar sounds LESS than chance):
  the dominant structure is DISSIMILATION (the OCP), not reduplication/harmony. The one
  above-chance effect (1.34× vs shuffle) is just "English has ~no geminates," largely
  consonant with the alternating contour. Shelved as a feature — but the SIGN is itself
  a finding worth recording (the lexicon is anti-self-similar). The 1-D contour keeps
  the load-bearing geometry; the full path's self-returns add no positive cue.
- **ABOVE THE BIGRAM FLOOR — a reframing, then a win on the RIGHT axis.** A live
  generation diagnostic showed the topic layer surfaces the right content words but they
  LOSE at the high-entropy decision points (every prompt's worst spot was 'after the',
  H=11.8) to the function-word marginal. The first fix tried — ENTROPY-ADAPTIVE topic
  weight (`scripts/adaptive_topic.py`, lean on topic when the bigram is blind) — was a
  perplexity NEGATIVE: −0.12 bits vs a fixed weight. The reason is the reframing: **the
  function-word salad IS the perplexity-optimal output** — at a blind spot the true next
  word usually IS a function word, so over-weighting topic misses. You cannot
  perplexity-optimise above the floor; lifting generation is a DIFFERENT objective
  (content, diversity, coherence) that explicitly TRADES perplexity. Measured by the
  right metrics (`scripts/generate_quality.py`): three earned-from-the-diagnostic levers
  in `Session.respond` — `sem_adapt` (topic at blind spots), `no_repeat` (break the
  carry's cycles), `fn_penalty` (down-weight the earned function-word SKELETON) — lift
  **content 36%→84%, on-topic 63%→84%, repeat 11%→1%, distinct 0.66→0.73**. Output goes
  from 'the connivance man's even more than man's control of the to the' to 'even taste
  callous exploitation beyond even taste man's open to returned with' — content-rich and
  on-topic, though still NOT grammatical (syntax is the next, harder layer). The levers
  are the respond DEFAULTS now, flagged as tunable knobs (like temperature), NOT earned
  constants — the perplexity trade is explicit, not hidden. Tests in `tests/test_session.py`.
  **~~Grammaticality: the syntactic scaffold.~~ DONE — STRUCTURE where IDENTITY was null.**
  The diagnostic named the missing piece: a class-level scaffold (what KIND of word
  follows what). `scripts/syntax_scaffold.py` builds a SYNTACTIC classing (each function
  word its OWN class — function words ARE the syntax — + content distributional classes)
  and measures the class-BIGRAM: prev's class predicts the NEXT class with **+0.53
  bits/class (MI ~0.57)** of grammatical structure ('of'->determiner 27%, 'to'->verb/be,
  noun->preposition), CONFIRMING the data's identity-vs-structure split (prev-class
  pooling was NULL for word IDENTITY, STRONG for class STRUCTURE). Wired: `SyntaxScaffold`
  (semantic.py) + `Session(scaffold=)` + a `grammar` lever in respond that biases each
  candidate by P(class(w)|class(prev))**grammar — putting function words back WHERE
  grammar wants them. Measured (`scripts/grammar_quality.py`, vs a REAL-TEXT reference of
  fn-rate 49% / gram-cost 7.24): the scaffold moves fn-rate **16%->53%** and gram-cost
  **8.99->5.32** while content/on-topic hold (47% / 81%). Output goes from
  'praised well as the understood island praised' to 'to be understood that the great
  deal of the nation' — sentence-SHAPED. `grammar=1.0` is the respond default (with a
  scaffold attached). HONEST CEILING: a 1st-order class-bigram is the FLOOR of syntax,
  not the ceiling — locally grammatical, not yet parseable (phrase structure + agreement
  are higher-order, the next layer). Tests in `tests/test_semantic.py`.
  **~~The SUBJECT->PREDICATE arc + sentence boundaries.~~ DONE — partial, honest.**
  Following the data toward 'subject vs predicate': `scripts/sentence_arc.py` measures
  each syntactic class's mean SENTENCE POSITION and end-rate. The arc is REAL and
  grammatically precise — NOMINATIVE pronouns cluster early ('i','we','he','she' ~0.28),
  ACCUSATIVE late ('him','them' ~0.62): the system recovered SUBJECT vs OBJECT case BY
  POSITION. Sentences COMPLETE on predicate tails ('him' 22%, 'said' 22%, 'them' 21%).
  HONEST: position does NOT improve next-CLASS prediction (−0.44 bits — it fragments the
  bigram), so this is a STRUCTURE signal, not perplexity — consistent with the floor.
  `SyntaxScaffold` now also holds the arc (meanpos/endrate/mean_len + `pos_fit`/`end_prob`);
  `respond(position_bias=, boundaries=)` biases candidates by sentence position (subjects
  early, objects late) and ends sentences by the end-model. Measured
  (`scripts/sentence_quality.py` vs real text sent-len 15.7, subj 0.28, obj 0.61):
  boundaries bound the run-on **28->~12 words**, position_bias places **subjects 0.32
  before objects 0.41** — the subject->predicate SHAPE, content/fn-rate held. PARTIAL:
  object placement reaches only mid (0.41 vs 0.61) and multi-sentence output still has
  residual topic repetition, so the levers are OPT-IN (default off), measured + wired +
  demonstrated, not forced. Tests in `tests/test_semantic.py`.
  **~~Residual repetition.~~ FIXED by an EXISTING knob, not new machinery.** The showcase
  (`scripts/showcase.py`) surfaced longer-range repetition ('three years ago men three
  years ...') in 26-token responses. A sweep showed the cause was simply `no_repeat`=4
  being too short a WINDOW (the topic re-primes the same word at distance ~6); lowering
  the topic weight did NOTHING extra (it is the window). Default `no_repeat` 4->8 lifts
  content-diversity 0.62->0.71 and on-topic 75->80% with content held — discipline over
  engineering: turn the knob, don't build a new mechanism.
  **~~The 1st-order ceiling, CHARACTERISED.~~ DONE — it is HIERARCHY, not context-length.**
  A ceiling diagnostic (annotated class-paths) showed the dominant failure is CLASS-
  STALLING — the output gets stuck inside one content class ('president kennedy president
  kennedy ...') because the bigram has no notion of phrase CLOSURE. The obvious cheap fix
  (a higher-order class n-gram) was PROBED (`scripts/ngram_ceiling.py`): a fine-class
  trigram is data-starved (381^3, hurts by +2.1 bits), but SWEEPING coarseness K shows the
  trigram crosses to helping around K~32-64 — yet the gain there is NEGLIGIBLE (+0.02-0.03
  bits/class, a tenth of the bigram's own gain). So higher-order class n-grams add ~nothing
  at ANY granularity: the bigram already captures the LINEAR class-sequence structure, and
  the structure the output LACKS (constituent closure, long-range subject->verb) is
  HIERARCHICAL — no flat n-gram captures it. The honest verdict: the 1st-order ceiling is
  the FLAT-MODEL ceiling; crossing it needs constituent/phrase structure (a recursive/stack
  mechanism), a different model class — not more context. A measured fork-decision: do NOT
  build a trigram (negligible payoff); the real frontier is hierarchy. OPEN accordingly.
- **Lexicon growth** (`spec_lexicon_growth.md`) — **v1 Stages 1–2 + gate DONE,
  PASS, self-contained on CMU (no running text needed).** `elfix/lexicon/`:
  `ortho_affix` (earned orthographic affixes + spelling-restoration decompose) →
  `compose_pron` (the **already-earned** -s/-z, -t/-d voicing allomorphy from
  `appendix.py`). `scripts/lexicon_gate.py` reconstructs inflected pronunciations
  from the in-CMU stem: **82.7% exact vs 57.4% no-allomorphy baseline (+25.3%)** on
  28,342 words, and **95.8% on regular (stem-preserved) decompositions** — the
  geometry that SEGMENTS allomorphs GENERATES them. Findings: (a) orthographic
  productivity is single-letter-skewed, so affixes emerge at frac~0.1 (vs appendix
  0.5); (b) **Stage 3 (phonotactic critic) was MEASURED and REJECTED** — recognition
  & coda-legality are no-ops (78.9% of errors are `thing→the+ing` false splits whose
  pronunciations are well-formed; phonotactics can't reject a legal-but-wrong
  analysis). The precision lever is OOV-only scoping (the 82.7→95.8 gap is in-vocab
  look-alikes deployment looks up) + Stage 4 corroboration, NOT a critic. **Stage 4
  (`inferred_store.py`) DONE:** `InferredStore` governs generated prons SEPARATE from
  the attested core — ternary evidence (attested+1 / inferred 0 / rejected −1 / absent
  None, Law 2/5), malleable→confirmed at ≥2 agreeing sources, and the three guarantees
  (never shadow attested; never compound — `grow` reads attested stems only; never
  collapse — `confirmed_view` is a re-derivable view), all tested. Holdout grow:
  1,413/6,303 OOV recovered at 84% precision, 141 confirmed, 19 rejected, most
  malleable (confirmation awaits running-text frequency). REMAINING: OOV-only scoping,
  derivational/-est, running-text corroboration. Root-novel (names) out of scope — no
  opaque G2P (Law 6).

## What was deliberately dropped (do not re-add)

The 3-6-9 axis flips (Mind_Space), the φ-chain / Mersenne / Ω_m / Dual-13
derivations and the Möbius relabeling (GCL), and `pi2_sphere`. They failed the
"is this load-bearing or decoration?" test (the one you wrote yourself in GCL's
`cubic_nearmiss`). Law 1 exists to keep them out.
