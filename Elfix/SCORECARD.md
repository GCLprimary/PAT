# ElfIX — the competence map

*A scorecard of what the system's own falsification gates decided. The project began
with an inherited ambition — "sound forms the shapes that drive the model" — and
refused to assume it. Every place sound was pushed past its competence, a gate came
back null; every place it was suited, a gate came back strong. The architecture did
not decide where sound belongs; the **measurements** did. This is that map.*

## The one-line finding

> **Sound governs STRUCTURE; distribution governs WHAT-COMES-NEXT.**
> A word is *pronounced and segmented* from its sound, and *predicted and placed* by
> its distribution. The two halves connect at **pronunciation** (a new word's first
> handle is its shape), not at prediction (its behaviour is its company).

## SOUND — where it WINS (structure: segment, inflect, pronounce)

| mechanism | result | vs baseline | script |
|---|---|---|---|
| Syllable segmentation (sonority contour) | **F1 ≈ 0.93** | BPE ≈ 0.40 | `syllable_eval.py` |
| Morpheme boundaries (+ additive appendix units) | recall 0.48→**0.97**, F1 →0.63 | BPE ≈ 0.33 | `milestone1.py` |
| Allomorphy generation (compose -s/-z, -t/-d) | **95.8%** regular / 82.7% all | 57.4% no-allomorphy | `lexicon_gate.py` |
| OOV pronunciation (decompose → compose) | **17%** of OOV grown from shape | (was: choke) | `oov_grow.py` |

## SOUND — where it's NULL or WEAK (prediction / placement)

| mechanism | result | why | script |
|---|---|---|---|
| Phono backoff (last word's sound → next word) | **NULL**, −0.3…−0.5 bits vs unigram | sound-class mixes syntactic categories → collapses to the function-word marginal | `predict_backoff.py` |
| Converge points (within-word path folds back) | **FALSIFIED**, 0.86× chance | lexicon is anti-self-similar (OCP/dissimilation), not reduplicative | `converge_probe.py` |
| Box signature (4×4 grid positional key) | **RETIRED, unasked** | zero consumers, so its own SPEC gate ("earns its keep once Tier 2 exists?") could never run; marker sets `{4,10}`/`{6,8,12,14}`/`{15}` were read off a diagram | — |
| ±8 → ℤ/17 ternary accumulator | **NOT EARNED** | no valence picks 8; the Law-5 valence (attestation) overflows on 7.17% of words and earns c=11→23 | `earned_capacity.py` |
| Small modulus as an identity key | **FALSIFIED**, 100% collision | 126k words cannot enter 17 (or 2707) buckets; base matters more than modulus | `modulus_probe.py` |
| Morphology → distributional class (place from shape) | **WEAK**, 0.10 cosine (15% to ceiling) | inflection shifts a word off its stem's distribution | `oov_gate.py` |

## DISTRIBUTION — where it WINS (what-comes-next / placement)

| mechanism | result | control | script |
|---|---|---|---|
| Carry: word-identity over time (working memory) | **+0.42 bits** genuine topical | sentence-shuffle isolates it | `carry_predict.py` |
| Acquired store: train through input (long-term memory) | **+10% ppl** on unseen text | attested frozen, self quarantined | `acquire.py` |
| Semantic topic: class memory (the semantic layer) | **+0.39 bits** over the word-cache | primes on-topic words never seen | `semantic_carry.py` |
| prev-class pooling (by SOUND *or* MEANING) | **NULL** for both | next-word ≈ the marginal regardless of prev's class | `semantic_gate.py` |
| OOV placement: context vs shape | **context wins at ~2 reads** → 91% by 80 | morphology cold-start 0.19 | `oov_place.py` |
| **Factored counted model** (class-bigram × within-class) | **+0.81 bits** vs the word-bigram floor (~1.7× ppl) | sparse +1.78 / dense −0.25: pure generalization; unk-leak paid | `gradient_compartment.py` |

## The constants — every one earned or honestly flagged (Law 1)

| constant | value | status |
|---|---|---|
| carry retention rate | 0.67 | EARNED: phoneme-context MI half-life, shuffle-debiased (`carry_revalidate.py`) |
| topical carry rate / mix | 0.997 / 0.4 | EARNED on a DEV split, reported on test (`carry_predict.py`) |
| semantic class count K | 300 | **A DIAL, and that is the result** — not a shortfall. Rate-distortion is smooth by construction; an elbow appears only where the data has a preferred resolution. `semantic_k.py` measured distortion ≈ linear in K, so there is no elbow *to* find: word distribution is a continuum, and K legitimately sets resolution (finer → sharper topics, coarser → more lift). Law 1 is satisfied by naming it a dial, not by inventing a number. |
| OOV re-placement threshold | 2 reads | EARNED: the context-beats-shape crossover (`oov_place.py`) |
| acquired confirmation | 2 occurrences | corroboration count (cf. InferredStore CONFIRM_AT) |
| arc quanta (place/manner) | 0.111 / 0.222 | EARNED: per-axis MAD of arc means (`auto_quanta`) |

No magic constant survives unflagged. The φ-chain, Mersenne, Ω_m, Dual-13 and 3-6-9
axis flips of the GCL/Mind_Space lineage were dropped (SPEC.md / CLAUDE.md) — Law 1
exists to keep them out, and it did.

## Governance (the contamination trap, measured)

- **Never overwrite:** after learning 66k transitions, the attested store is byte-identical (`acquire.py`).
- **Never compound:** 5,000 self-generated transitions change held-out surprisal by exactly 0 — the model learns from OTHERS, never from itself (`acquire.py`, `Session.respond`).
- **Ternary evidence, absence ≠ zero:** attested / inferred-malleable / confirmed / rejected, throughout (`InferredStore`, `AcquiredContext`).

## The system, end to end

Reads text → tags + **pronounces** new words from shape → **learns** across three
memory timescales (attested base · carry working-memory · acquired long-term) →
**predicts** with word + topic context → **localizes** where meaning attached and
**types** it by class AND **part of speech** (predicate/argument, RoleTagger) → **responds**
(counted floor, now with an opt-in class-FACTORED base) — every value a count you can point at,
no gradient anywhere. 116 tests + doctests green.

## Generation — a reframing (the floor is perplexity-optimal)

The biggest surprise of the build: you **cannot perplexity-optimize above the bigram
floor with generation levers.** The function-word salad ("the X the X") is what *minimizing
next-word surprise* looks like — at a high-entropy blind spot the true next word usually *is* a
function word, so leaning on the topic there *hurts* perplexity (`adaptive_topic.py`: −0.12 bits).
(LATER REFINEMENT, `gradient_compartment.py`: the *base model itself* was improvable — the
class-FACTORED counted model beats the word-bigram floor by +0.81 bits. The lever claim stands;
"the floor" turned out to be the word-bigram's ceiling, not counting's.)
Lifting generation is a **different objective** (content, diversity, coherence) that
explicitly **trades** perplexity. Measured on those axes (`generate_quality.py`), three
earned-from-diagnostic levers in `Session.respond` deliver:

| axis | baseline | + all levers |
|---|---|---|
| content-word rate | 36% | **84%** |
| on-topic rate | 63% | **84%** |
| 2-cycle repeats | 11% | **1%** |
| distinct | 0.66 | **0.73** |

Content-rich and on-topic, but the salad still wasn't grammatical. The fix was a
**syntactic scaffold**: prev's class is null for the next word's IDENTITY, but a
class-bigram (function words as their own classes + content classes) predicts the next
CLASS with **+0.53 bits** of structure (`syntax_scaffold.py`: 'of'→determiner,
'to'→verb, noun→preposition). Biasing generation by it (`grammar` lever) restores
function words where grammar wants them — vs a real-text reference (fn-rate 49%,
gram-cost 7.24):

| | content | fn-rate | on-topic | gram-cost |
|---|---|---|---|---|
| content-only | 84% | 16% | 81% | 8.99 |
| **+ scaffold** | 47% | **53%** | 81% | **5.32** |

`praised well as the understood island` → `to be understood that the great deal of the
nation` — sentence-SHAPED. The honest ceiling: a 1st-order class-bigram is the FLOOR of
syntax (locally grammatical), not full parseability.

**The subject→predicate arc** (`sentence_arc.py`) goes one level up: classes carry a real
SENTENCE-POSITION structure — nominative pronouns (`i, we, he, she`) cluster early (~0.28),
accusative (`him, them`) late (~0.62), so SUBJECT vs OBJECT case falls out of POSITION
alone; sentences end on predicate tails (`him, said, them`). Position does NOT help
next-class prediction (structure ≠ identity, again), so it's a STRUCTURE lever:
`respond(boundaries=, position_bias=)` bounds the run-on (28→~12 words) and orders
subjects (0.32) before objects (0.41) — the subject→predicate shape, counted. Partial
(object placement reaches only mid; opt-in by default).

## The 1st-order ceiling — characterised (it's hierarchy, not context-length)

The class-bigram + arc give the SHAPE of syntax (bounded, role-ordered, locally
grammatical) but the output stalls inside a constituent (`president kennedy president
kennedy …`) — no phrase CLOSURE. The cheap fix (a higher-order class n-gram) was probed
and ruled out (`ngram_ceiling.py`): fine-class trigrams are data-starved (hurt by +2.1
bits); coarse-class trigrams are well-estimated but add only **+0.02–0.03 bits** — a
tenth of the bigram's gain. Higher-order class n-grams add ~nothing at any granularity:
the bigram already holds the LINEAR class structure, and the missing structure
(constituent closure, long-range subject→verb) is **HIERARCHICAL** — no flat n-gram
captures it. The 1st-order ceiling is the **flat-model ceiling**; crossing it needs
constituent/phrase structure (a recursive/stack mechanism), a different model class.

## Constituent structure — BUILT and gated (counted, recursive; two honest findings)

`elfix/syntax_tree.py` is the mechanism the n-gram ceiling said was needed: a `SyntaxTree`
recursive agglomerative bracketer — merge the strongest-binding adjacent span first (the
Tier-3 emergent-unit move lifted to syntax, producing NESTING = a tree = a stack; binding =
earned class-pair PMI, boundary at the PMI=0 chance line, mean constituent length earned
from `p_bond`) — plus a `ConstituentController` for parse-guided generation. Two measured
findings, both honest, neither a clean win:

| question | result | script |
|---|---|---|
| Does the parser recover grammar? | **extreme bonds YES, ordinary ~chance** | `python -m elfix.syntax_tree` |
| Does the closure brake fix the class-stall? | **YES**, class-2cycle 18→15%, run 1.34→1.12 (real 0% / 1.01) | `parse_guided.py` |
| Does the PARSE-SCOPING earn its keep? | **NO — a trade-off** vs a flat class-window | `parse_guided.py` |

The parser brackets real sentences into readable trees and merges the tightest collocations
first (`more→than`, `has/have/had→been`, `does→not`, `(blue eyes)`, `(one week)`), but a
right-attachment proxy is at/below chance (52% vs 58% random) — the greedy class-PMI binder
nails high-PMI collocations, not average det/prep attachment. The controller penalises
re-entering the OPEN constituent with a repeated head-class — the CLASS stall (different
words, same classes) that `no_repeat` and `grammar` cannot catch — and reduces it toward
real text. But a FLAT class-window control (no phrase-scoping) does the same job slightly
harder at a small on-topic cost; the constituent scoping is gentler (it resets at phrase
boundaries, so a class may recur across phrases → on-topic 77% vs 74%) but does **not
dominate**. So the brake is a usable OPT-IN lever (`Session.respond(constituency=…)`, default
OFF); the greedy class-PMI parse is **not yet load-bearing** for generation. The remaining
frontier, sharpened by both findings: a **head-aware** binding signal + a real (treebank)
evaluation. The mechanism is built and the wiring proven; the v1 binder is the bottleneck.

## Head-awareness — one WIN, one NULL, one meta-finding

Followed the frontier above. `RoleTagger` + `ClauseController` in `syntax_tree.py`:

| mechanism | result | script |
|---|---|---|
| **`RoleTagger`: earned verb/noun (POS) from functor context** | **WIN** — verbs 0.80 vs nouns 0.13 | `clause_guided.py` |
| `ClauseController`: brake args while a verb is owed | **NULL** for generation | `clause_guided.py` |
| structural generation-control (phrase **or** clause) vs flat window | **loses** — the window wins | `parse_guided` / `clause_guided` |

The topical distributional classes do **not** carry POS (verb/noun is orthogonal to topic; a
class-level N-V 2-colouring washes out). But a 2-hop bridge from the single most-frequent word
(`the` → nouns → functors-that-precede-verbs → verbs) earns it cleanly and counted — the
functor split is textbook (nominal `the/a/this/his`, verbal `has/had/he/she/i`). It now **types
the locator** (predicate vs argument: an unexpected *argument* is a new entity, an unexpected
*predicate* a new relation). The `ClauseController` built on it is a **measured null**: verb-rate
is already ~real (~58%) in every config, so there is no verb-deficit stall to fix — the residual
stall is surface class-recurrence, best handled by a flat class-window. **The meta-finding:**
two natural structural controllers were gated and neither beats a dumb flat window — within the
counted/no-gradient constraint, structural *generation*-control is largely exhausted. The
durable win is the RoleTagger, and its home is **analysis** (typing the locator), not generation.

**Headhood, earned** (the follow-up analysis win). By the SYMMETRIC substitutability test — the
head is the child that accepts the phrase's outer context on its far side — nominal compounds
are **90% right-headed** (`(white house)`→house at 0.94 vs 0.04), and the exceptions are
themselves correct (`(president kennedy)`→president: title constructions ARE left-headed). Verb
pairs *fail* substitution (34%/58%) for a principled reason: **modification preserves a
distribution, argument-filling transforms it** (`(took place)` continues like `place`, not bare
`took`). That resolves the head-aware puzzle: **heads NAME (category); edges BOND
(distribution)** — the parser binds by edges (measured better) and annotates every constituent
with its earned categorial head (`head_of`: content-over-functor → predicate-over-argument →
right-headed; `Node.head_word`: `((how much) ((they knew) (about her)))` → *knew*). The entropy
tiebreak that made *blue* head `(blue eyes)` is retired to a diagnostic.

## Compartmentalizing the gradient — the stance the competence map points to

The project began as *replace* the gradient (Law 6: no gradient black box, higher units form
from geometry). The competence map it produced suggests a sharper stance: **compartmentalize**
it. The falsification gates drew a real boundary — counting/geometry wins decisively on
STRUCTURE (segment, pronounce, inflect; syllables F1 0.93, allomorphy 95.8%) and hits a measured
FLOOR on WHAT-COMES-NEXT (the phono null, the perplexity-optimal floor, structural
generation-control losing to a flat window). That boundary is not a failure to push harder; it
is *where the irreducible-by-counting residual lives*. Read that way, Law 6 becomes a design
principle rather than a prohibition: the gradient, if admitted at all, must be **walled into the
measured residual** (the semantic / long-range what-comes-next), never load-bearing for
structure, and its boundary must be *earned by a gate* — the same discipline that kept φ-chains
out. The honest tension: this trades thesis-boldness ("no gradient") for thesis-correctness ("a
measured map of where each tool belongs, and the minimal gradient that respects it"). The map is
the contribution.

**Step 1 — the oracle ablation — is RUN** (`gradient_compartment.py`), and it cut both ways:

| quantity | measured | meaning |
|---|---|---|
| the floor, decomposed | 10.44 = **6.99 category + 3.45 within-class** | 67% of the bits are "which KIND of word" |
| topic recovers (counted) | 0.80 of the within-class | the semantic carry's within-class share |
| **the gradient compartment** | **2.65 bits/word (25%)** | irreducible by class+topic; spread across BOTH pred/arg channels, not just new entities |
| the surprise | **factored counted model +0.81 bits over the floor** | the counted side was NOT exhausted — claim it before walling in any gradient |

The factored model — `P(class(w)|class(prev)) × P(w|class(w), prev)` — is Brown (1992)'s class
LM done with the earned classes; the old prev-class-pooling NULL was the wrong *mechanism*
(pooling discards word identity), not wrong classes. Its win is pure generalization (sparse
contexts +1.78, dense −0.25 → dev-earned λ=0.3 interpolation). So the discipline held exactly as
designed: the probe meant to size the gradient compartment first *shrank* it honestly (2.65
bits, located) and *postponed* the gradient (counted territory remained). Step 2 — the walled
small-head test on the 2.65-bit residual — stays open, and now has a sharper null hypothesis to
beat: the factored counted base at 9.63 bits/word, not the 10.44 floor.

## Honestly open

- **~~Wire the FACTORED counted model into `Predictor`.~~ DONE + gated live** (`attach_factored` /
  `FactoredBase`; `Session(factored=True)`; `scripts/io_loops.py`): opt-in, off by default. On live
  read↔respond loops it reproduces the win **turn by turn (+1.19 bits/word** on a topical Brown run,
  bigger than held-out because the run is name/content-dense — where class generalization bites), and
  the per-transition breakdown is exactly the designed mechanism (`not→attending` +5.9, `this→trouble`
  +6.9: unseen bigrams whose CLASS transition is predictable). The two other surfaces, gated: the
  **locator sharpens** (its top surprisals are all proper names — the referential/gradient compartment
  made visible), and **generation is unchanged** (still lever-dominated name-salad — the factored base
  is a PREDICTION win, not a generation one, as the floor-is-ppl-optimal framing predicts).
- **The compartmentalize probe, step 2** (step 1 is RUN, above): does earned-features + a small
  walled learned head beat the *factored* base (9.63 bits) on the located 2.65-bit residual?
  Requires admitting a (walled) learned head — a real architectural commitment.
- **A stronger parser** (the one structural fork left). The greedy class-PMI binder is
  head-unaware (parser ~chance on ordinary attachment; parse-scoping ties a flat window). A
  treebank-supervised or non-greedy binder *might* make structure load-bearing, but it strains
  the no-gradient bet — hence the compartmentalize stance above. (The `head_aware` parse path
  and the `RoleTagger` are the down-payment: heads for det/prep, earned POS in hand.)
- Root-novel OOV — proper names — stay out of scope by design (Law 6: no opaque G2P).
- K as a continuum dial rather than a discovered number (no natural elbow exists).
