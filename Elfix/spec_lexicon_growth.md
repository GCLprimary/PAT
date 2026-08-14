# Spec — Growing the lexicon by morphological composition (ElfIX)

**Purpose.** Running text contains words not in the CMU dictionary (OOV). Instead of
dropping every OOV (losing data), *generate* pronunciations for the **productive**
OOV — inflected/derived forms of words ElfIX already knows — using ElfIX's own
earned machinery, and grow a separate **inferred lexicon** that never contaminates
the attested CMU core.

This is grapheme→phoneme done the ElfIX way: not an opaque seq2seq model, but
**compose-from-known-parts + phonotactic critic + confidence-gated promotion**.

> **STATUS — v1 Stages 1–2 + the gate are BUILT and PASS** (`elfix/lexicon/`,
> `scripts/lexicon_gate.py`), self-contained on CMU, no running text required.
> Earned allomorphy reconstructs **82.7%** of inflected pronunciations exactly vs a
> **57.4%** no-allomorphy baseline (+25.3%) on 28,342 words — and **95.8%** on
> regular (stem-preserved) decompositions. Findings: orthographic productivity is
> single-letter-skewed (affixes emerge at `frac~0.1`, not the appendix's 0.5); and
> **Stage 3 (phonotactic critic) was measured and rejected** — it is a no-op
> (false decompositions are well-formed). **Stage 4 (inferred store) is BUILT**
> (`elfix/lexicon/inferred_store.py`): a holdout grow recovers OOV pronunciations
> into a SEPARATE store (84% precision, 141 confirmed via multi-decomposition,
> most malleable pending text), with the law guarantees tested. REMAINING:
> OOV-only scoping, derivational/-est, running-text corroboration.

---

## The honest boundary (state it first, it's the whole design)

ElfIX has **no grapheme model**. It cannot invent the pronunciation of a novel
*root* from its spelling — that is an orthographic fact no phonotactics recovers.
So the task splits, and the split is the spec:

| OOV type | example | ElfIX can… |
|---|---|---|
| **Derived / productive** | googled, refactors, unfriending | **generate** (compose from known stem + known affix) |
| **Root-novel** | proper nouns, foreign names, new roots | **only validate** an externally-sourced pronunciation, never invent it |

v1 targets the productive class — which is the bulk of non-name OOV in running text.
Root-novel is **out of scope for generation**, and the falsification gate must
*show* that honestly (≈0 accuracy on held-out names), not hide it.

**Why this is NOT circular** (a subtlety that bit the segmentation work): the
appendix morpheme-gold was *defined* as "stem is a CMU word," so using stem-
membership to predict it was circular. Here the gold is the held-out word's actual
**pronunciation string** — independent of decomposability. Using "stem ∈ CMU" to
*find* the decomposition is a legitimate generation input, not the gold's own rule.

---

## The mechanism — four stages, each tied to a law and an existing piece

### Stage 1 · `ortho_affix` — earn the orthographic affix inventory
- **Guarantee:** a set of productive word-final (and word-initial) LETTER-shapes,
  earned by recurrence across many distinct stems — the *orthographic twin* of
  `emergent/appendix.py`'s phoneme-shape discovery.
- **How:** count word-final letter sequences (len 1–3) over the CMU vocabulary;
  promote those attaching to ≥ `frac` of the most-productive ending's distinct
  stems. Yields `-s, -es, -ed, -ing, -er, -ly, -ness, …` without hand-listing.
- **Decompose an OOV:** strip a candidate affix, apply regular English spelling-
  restoration (e-insert `googl→google`, undouble `stopp→stop`, `i→y` `studi→study`),
  and accept the split if a restored stem is a CMU word.
- **Provenance:** `[NEW→original]`, mirrors `discover_appendices`. Contrast baseline:
  Morfessor (Creutz & Lagus 2007).
- **Law 1/3:** the affix set is an earned, re-derivable view of the vocabulary.
- **Open:** the productivity `frac` (same open question as the appendix threshold);
  the spelling-change rule set (handle the regulars, log the irregulars).

### Stage 2 · `compose_pron` — compose the pronunciation with EARNED allomorphy
- **Guarantee:** `pron(OOV) = pron(stem) ⊕ allomorph(affix | final phoneme of stem)`,
  a stressless ARPABET sequence matching `cmu_preprocessed` format.
- **The key move — ElfIX already earned the rule:** the appendix work's voicing-
  neutral merge *discovered* that `-s/-z` and `-t/-d` are one morpheme with voicing-
  conditioned allomorphs. That **is** the selection rule:
  - stem ends voiceless obstruent → `/s/`, `/t/`   (cats, walked)
  - stem ends voiced → `/z/`, `/d/`               (dogs, played)
  - stem ends sibilant / coronal stop → `/ɪz/`, `/ɪd/`  (buses, wanted)
- **Stress is out of scope:** the corpus is stressless ARPABET (stress lives in a
  separate `stress.txt`), so composition is phoneme concatenation + allomorph
  pick — no stress-shift problem. (Derivational stress shift, e.g. PHOto→photoGRAphy,
  is deferred with the derivational affixes.)
- **Provenance:** allomorphy from `emergent/appendix.py` (earned); the voicing/
  sibilant conditioning is `[NEW→established]` English inflectional phonology.
- **Law 1/6:** a readable, earned phonological rule — not a learned mapping.

### Stage 3 · phonotactic critic — MEASURED, and an honest no-op (not built)
- **The hypothesis:** score a composed pronunciation for well-formedness (legal
  onsets/codas, recognized emergent units, recognition temperature) and reject the
  implausible, to catch bad decompositions.
- **The measurement (the discipline, before building):** it does NOT separate
  correct from incorrect. Mean recognition is **1.000 for both**; illegal-coda rate
  is **0.0% vs 0.1%**. Reason: **78.9% of errors are `thing→the+ing`-style false
  decompositions whose pronunciations are perfectly well-formed** — phonotactics
  cannot reject a wrong analysis that happens to be legal. So no critic module is
  built (it would be decoration, like the rejected legal-coda segmentation gate).
- **What the measurement DID reveal — the real precision picture:** on REGULAR
  decompositions (stem pronunciation preserved — v1's actual scope) compose is
  **95.8%** exact; the 82.7% overall is dragged down by monomorphemic *in-vocab*
  look-alikes (`thing`, `boss`) that the gate force-decomposes but **deployment
  looks up rather than decomposes**. So the precision lever is not a critic but
  **(a) OOV-only scoping** (only decompose genuine OOV) and **(b) Stage 4
  corroboration** (independent evidence / running-text frequency).

### Stage 4 · `inferred_store` — malleable → confirmed, kept SEPARATE  **(BUILT)**
- **Guarantee:** inferred pronunciations live in their own table, tagged
  `inferred`, **never merged into the attested CMU core**.
- **How (built):** `InferredStore(attested)` with `propose / lookup / evidence /
  confirmed_view / grow`. Ternary evidence — `attested(+1)` / `inferred(0)` /
  `rejected(−1)` — AND `absent(None)` distinct from zero (Law 2). An entry is
  *malleable* until `CONFIRM_AT` independent agreeing sources promote it to
  *confirmed* (available now: multiple decompositions composing to the same pron;
  PRIMARY source awaits the corpus: running-text frequency). A conflicting pron is
  a contradiction → `rejected`.
- **The three guarantees, tested:** never SHADOW attested (lookup prefers ground
  truth); never COMPOUND (`grow` decomposes against the attested core ONLY — a stem
  is never an inferred word, so the bootstrap loop cannot cascade its errors); never
  COLLAPSE (`confirmed_view` = attested + confirmed-inferred is a re-derivable VIEW,
  not a write-back). Holdout grow: 1,413/6,303 OOV recovered at 84% precision, 141
  confirmed via multi-decomposition, 19 rejected as contradictions, most malleable.
- **Provenance:** `[GCL]` malleable_library (malleable→confirmed) + `[ElfIX]`
  ternary_valence — the *same* promotion machinery as Tier 3.
- **Law 2/3/5:** absence ≠ zero; one source of truth; ternary evidence. Inferred and
  attested are different evidential facts and never collapse.

---

## The falsification gate (mandatory — `scripts/lexicon_gate.py`)

Don't claim it works; gate it, milestone1-style.

1. **Hold out** a slice of CMU words; treat them as OOV (remove from the lookup).
2. **Reconstruct** each via Stages 1–3 from the *remaining* CMU.
3. **Score** exact-match of composed vs real (stressless) CMU pronunciation.
4. **Stratify the gold** so the boundary is visible, not averaged away:
   - inflectional holdouts (-s/-ed/-ing/…) → expect **high** exact-match
   - derivational holdouts (-ly/-ness/…) → expect **moderate**
   - root/name holdouts → expect **≈0** (correct — and the gate should show it)
5. **Also report:** coverage gain on a running-text sample (OOV% before/after), and
   the phonotactic-rejection rate (how often Stage 3 catches a bad composition).
- **PASS:** beats two baselines on the productive class — (a) dropping (0 recovery),
  and (b) naive "stem + single most-common affix pron, no allomorphy" — so the
  *earned allomorphy* is shown to be load-bearing, not decoration.

---

## Scope of v1, and what it will NOT do

- **In:** inflectional, stress-preserving affixes on single known stems; regular
  spelling restoration; phonotactic validation; separate inferred store with the
  holdout gate.
- **Deferred:** derivational + stress-shifting affixes; recursive/multi-affix
  decomposition (un·friend·ly); irregular spelling changes (wife→wives) — log them.
- **Never (the laws):** no opaque G2P in the core (Law 6); no root-novel generation
  (validate-only); no inferred entry leaking into the attested gold (Law 3).

---

## Proposed layout

```
elfix/lexicon/
  ortho_affix.py     Stage 1 — earned orthographic affix inventory + OOV decompose
  compose_pron.py    Stage 2 — pronunciation composition via earned allomorphy
  validate.py        Stage 3 — phonotactic critic (wraps existing pieces)
  inferred_store.py  Stage 4 — malleable→confirmed inferred table (ternary, separate)
scripts/lexicon_gate.py   the holdout falsification gate (stratified)
```

Sequencing note: pairs with the running-text loader — that loader tags each token
`attested / inferred / oov`; this piece is what later *moves* tokens from `oov`
toward `inferred`, recovering the productive tail the loader would otherwise drop.

---

*Format follows the ElfIX `spec_piece` convention: each stage guarantees one thing,
cites its origin, and carries its open question forward unresolved rather than
pretending it is closed.*
