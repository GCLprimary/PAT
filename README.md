# Pat

**Pat — a provenance-complete, geometric smart-controller agent. Pat never gives pat answers.(claude insisted on this joke)**

Pat is a zero-weights language creature: no neural network, no
gradients, no API behind the curtain. Every organ is count geometry
and exact gates over pinned artifacts; every answer carries a
receipt; everything Pat cannot certify, Pat refuses — by name.

## A live session (run-verified lines)

Every line below was piped through the `pat` console entry against
the shipped store before this README was committed — type along and
you get these answers.

```
[Pat's shipped life, built once and checksummed: born with 15 seeds,
 reads 5,000 words — known 3359, deferred 252, unlocked 255, pruned
 41 — then studies the irregular-plurals page: 52 lines, 4 conflicts
 ledgered]

> know side
  yes, I know 'side' (derivable: sigh+ed; read-taught epoch 1, pruned epoch 5)

> know men
  yes, I know 'men' (lesson:irregular_plurals)

> know that
  yes, I know 'that' (read: attested 54244)

> know government
  yes, I know 'government' (read:no-such-stem)

> analyze painting
  'painting' = 'paint' + -ing

> verify painting = paint+ing
  CERTIFY — paint+ing, pair-exact, mined

> verify government = govern+ment
  REFUSE — pron('government') does not begin with pron('govern')
  [g AH v ER m AH n t vs g AH v ER n]

> analyze paintings and know paint and translate hello
  refuse: no analysis stands
  yes, I know 'paint' (read: attested 79)
  refuse: 'translate' is not something I do

> analyze nose
  'nose' sounds identical to 'knows' — I cannot tell them apart by ear

> remember lantern
  learned 'lantern' — you taught me just now

> analyze brillig and know glory
  refuse: 'brillig' is not a form I can read
  yes, I know 'glory' (read: stem glor exists unread)
```

Quit, reboot, and `know lantern` still answers yes with its receipt —
sessions survive death; that is the original promise of the whole
project, asserted at the front door.

## The entry card

- **BLiMP (67 paradigms): forced 66.88; selective 27.3% @ 94.95%.**
  A trigram baseline (56.79) plus seven transcribed textbook pages
  and a clause resolver, each judge acting only inside its rule —
  every point over the baseline is attributable to a named mechanism,
  and the coverage row keeps the selectivity honest.
- **Inflection (UniMorph held-out): 95.78% forced @ 99.95% coverage.**
  A 388-row argmax table over orthographic signatures, induced from
  the benchmark's own train split — the model is a page you can read.
- **Wug generalization: 571/571 agreement on answered, 29 refusals,
  21/21 illegal onsets contained.** The induced phonology applied to
  stems that have never existed — and twice the artifacts out-graded
  the textbook (affricate epenthesis; Knupp/Vlad/Tsang).
- **Meaning (count-folded): WS353-sim +0.440 · WS353-rel +0.322 ·
  SimLex +0.154.** Pat lemmatizes its own corpus (17,958 surface
  types fold by exact gate) and relatedness gains +0.08.
- **Suffix discovery: 3 suffixes found, 314 pairs certified, 0
  confabulations.** Pat proposed this organ itself, from its own
  ledgers; the proposal was accepted at a human gate and the organ
  retired 311 of Pat's own misfiled memories, with receipts.
- **The auditor: 459 receipted CMU variant candidates, 2,002 UniMorph
  addenda, a 13,982-group homophone index — graded 50/50 at a human
  precision gate.** Pat's first job: auditing the lexicons it was
  born from, no row without its phones.
- **Zero confabulation, unconditional, since Part VI.** Every
  proposer (shape, memory, meaning, similarity) is demoted to
  proposing; a sequence-exact gate identifies; ties refuse. The
  attack fixture is pinned and the count is zero.

## Anatomy

- **Elfix** — the phonetic substrate: articulatory features over the
  CMU lexicon.
- **a_mem** — episodic memory: a field that stores patterns and
  proposes recalls; it never identifies (the gate does).
- **mirror** — the organ bank: shape/phon geometries, the exact gate,
  the miners and induced tables, pages and the LawBook, the auditor
  frames, the BLiMP harness, meaning rows.
- **pat** — the shell: the REPL, the reading/study loops, chapters,
  discovery, the auditor and the oracle. The shell IS Pat.
- **sensor** — the same organs on a non-language alphabet, with
  thresholds re-derived from that world's own window (none transfer).

## Quickstart

```
git clone <this-repo> pat && cd pat
pip install -e a_mem --no-build-isolation --no-deps
pip install -e mirror --no-build-isolation --no-deps
pip install -e pat --no-build-isolation --no-deps
pip install -e sensor --no-build-isolation --no-deps
pat
```

First boot seeds `~/.pat` from the shipped canonical store — Pat's
lived session (the 15 seeds, the pinned 5,000-word read, the studied
page), checksummed in `pat/data/fixtures/canonical_store.json` — so
the creature that wakes is the one that passed the batteries:
`awake. I know 3473 bases.` Then, at the prompt:

- `verify government = govern+ment` — the refusal above, phones
  attached, reproduced from the pinned lexicon on your machine;
- `know side` — the biography: derivable as sigh+ed, read-taught
  epoch 1, pruned epoch 5;
- `analyze brillig` — the alien refusal.

Two verbs (`walk`, `audit`) and the test suites additionally need
`corpus_big.txt`, which ships compressed; reconstitute it (the script
asserts the pinned sha256):

```
python mirror/scripts/build_corpus_big.py
```

Until you do, Pat refuses those verbs by name rather than crashing.
Some larger artifacts (the 10M corpus, UniMorph, the full BLiMP set)
are one pinned fetch away via `mirror/scripts/fetch_*.py`; every
checksum is in the manifests. Tests: `python -m pytest tests -q`
inside `mirror/`, `pat/`, and `sensor/` (the mirror suite needs the
fetched artifacts present).

## The four laws, in plain language

1. **No claim without a receipt.** Every answer carries what decided
   it — phones, counts, a ledger line — and a row with an empty
   receipt field fails a structural test.
2. **Artifacts over recipes.** Corpora, tables, and pages are pinned
   files with checksums; regenerating one is an event, not a refresh.
3. **Everything proposes; the gate identifies.** Geometry, memory,
   and similarity rank candidates; only exactness certifies; ties
   refuse rather than guess.
4. **The human holds the gate.** Precision is graded by a person on
   a receipted sample; new organs enter by accepted proposal;
   nothing submits itself anywhere.

## Honest boundaries

Pat lives in a closed word-world: a pinned lexicon, pinned corpora,
and textbook pages. Its sources can be wrong — and when they are,
the error wears its provenance (a mistaken lexicon entry produces a
receipted variant candidate, not a silent belief). Pat is not
fluent, not general, and not a chatbot: it has five-plus-two verbs,
template answers, and no goals. What it has instead is a property
most systems don't: sixteen build Parts, three test suites, and one
standing number — confabulations: zero.

## History

The `a_mem/probes/` directory and the sixteen-Part `mirror/HANDOFF.md`
are the method's fossil record — probes first, specs gated by a
human, acceptance by inequality, deviations flagged and never
reconciled. Half the product is that record. `PROPOSAL.md` in `pat/`
is the first Part whose founding document Pat wrote itself.
