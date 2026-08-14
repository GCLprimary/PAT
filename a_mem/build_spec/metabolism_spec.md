# agent + a_mem + mirror — The Metabolism · Build Spec (probes 48, 48b, 49, 49b)

**Location:** `~/alignment_field` (new `agent/agent/chapters.py`; small
adapters in a_mem usage and `mirror/meaning_rows.py`; gate untouched).
**House rules unchanged:** tests before features; acceptance by
inequality; flag, don't reconcile; build → `HANDOFF.md` Part X → stop.
**Reference probes delivered:** probe48 (the fold refused), probe48b
(anchor+ledger spends), probe49 (raw circulation + drift, the honest
negatives), probe49b (gated circulation + the count fold).

**New laws this build codifies:**
1. **A chapter is an anchor plus a ledger — never a centroid.** The
   base's vector proposes; the exact gate identifies; the content is
   merged receipted structure. Geometric chapter identity is FORBIDDEN
   by canary: the 46 colliding-base families fold to cos 0.9912
   (probe 48) — pinned, so the collapse's recursion can't be unlearned.
2. **Synthesis conserves receipts by construction.** Ledger-merge is
   the only composition; receipts in == receipts out, asserted;
   chapters serialize and survive restart identically.
3. **a_mem proposes; the gate identifies.** Memory recall is a ranked
   proposal (`r.scores`), never an identity claim; every proposed
   anchor passes the sequence-exact stem check or the walk continues;
   exhausted proposals REFUSE, and refusals fall back to direct
   addressing. (Raw similarity measured 34.8% with 391 wrong-chapter
   claims; gated, 84.3% with 2 — the law is a 195× lie-reduction.)
4. **Fold the counts, not the vectors.** Meaning is computed over
   anchors: the creature lemmatizes the corpus with its own addressing
   and the dense space is built on folded counts. Member-level vectors
   are context-genre noise (34.3% coherence, probe 49B) — the drift
   census records them, the anchor carries the meaning.

---

## M-1 · `agent/agent/chapters.py` — the chapter class

- `Chapter(anchor)` with `ledger` (word → provenance), homophone-anchor
  cross-refs (hall ⇄ haul), dual-membership entries (master: member of
  mast's chapter AND its own — the listing pattern made structural),
  and a `drift` slot (members whose folded-space margin < 0, receipt
  only, no action).
- `synthesize(session) -> chapters` — ledger-merge over a
  ReadingSession's known/retired/census state; MAXR = the longest
  attested remainder (currently 3; asserted against the artifact, not
  hard-coded).
- **Tests (probe-48b gates):** anchor addressing ≥ 99% (measured 99.6)
  with REAL confabs == 0 after homophone/dual-membership adjudication
  (the 8 residual classes asserted BY NAME); colliding-group crucible
  ≥ 95% (measured 96.6); frontier addressing (pair scrubbed) ≥ 95%
  (measured 97.2) with coos-class abstentions counted honest;
  conservation: receipts before == after, exact class counts, and
  serialize → reload identical (law 2, hard).

## M-2 · Gated circulation (law 3; a_mem adapter)

- `cells_of(vec, grid, k=24)` adapter pinned; chapters written as
  anchor patterns with anchor meta; `recall_chapter(member_vec)` ranks
  `r.scores`, verifies candidates with the exact stem gate (the
  SHIPPED ladder, not the probe's loose set), refuses on exhaustion,
  falls back to direct addressing.
- **Tests:** gated wrong-chapter ≤ 2 at N=300 with each residual
  adjudicated by verdict class (measured 2 under loose licensing —
  expected 0–2 under the ladder; a 0 is welcome, a 3 is a finding);
  end-to-end (proposal + fallback) ≥ 99%; the raw-similarity number
  recorded as the law's justification, not gated.

## M-3 · The count fold (law 4; `mirror/meaning_rows.py` extension)

- `fold_corpus(addressing)` — every token mapped to its anchor via the
  dict-exact engine (measured: 17,958 surface types fold); the dense
  space (window-4 PPMI + SVD-300, frequency-weighted centering)
  rebuilt on folded counts.
- **Sentinel rows move:** WS353-rel ≥ 0.30 (measured **0.328**, from
  0.244 — the fold's headline), WS353-sim ≥ 0.43 (0.452),
  SimLex band 0.16 ± 0.03 (0.168, flat as forecast). Unfolded rows
  KEPT as the reference column; drift in either column names the
  meaning organ.
- The drift census (M-1's receipt) computed here, count-floor ≥ 20,
  stored on chapters; size recorded, not gated.

## M-4 · Batteries & demo

- Full suites green; a two-act `demo_chapters.py` (< 45 s): a mini
  world synthesizes ("1,094 receipts in, 1,094 out, 4 provenance
  classes conserved"), one member-cued circulation with the gate
  narrating ("a_mem proposed 3; the first to pass the stem check was
  'sigh'; 'side' lives in its chapter as a certified alias"), and one
  drift line ("'outing' was born of 'out'; its meaning has moved —
  receipt attached, nothing pruned").

## M-5 · Close-out

`HANDOFF.md` Part X: numbers, the four laws with their measured
justifications, deviations, and the next-frontier ranking (standing:
frame depth-2 — clause segmentation, now six customers; the folded
10M corpus — the fold and the volume should compound on WS-rel;
lesson library continued; repos public + Fellows email). **Stop.**

## Non-goals
Geometric chapter identity (canary-forbidden), region- and
feature-chapters beyond noting the LawBook as the existing prototype,
drift interpretation or action (receipt only), a_mem internals,
gate changes.
