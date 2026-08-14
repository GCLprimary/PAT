# mirror data — pinned artifacts (law 4: artifact over recipe)

Corpora here are ARTIFACTS, not recipes. They were built once on this
machine and are pinned; tests and modules read these files and never
rebuild them from NLTK. (The G-4 lesson: every number derived from the
pinned CMU file reproduced across machines to the decimal; every number
derived from per-machine NLTK rebuilds drifted.)

| file | provenance | contents |
|---|---|---|
| `corpus.txt` | **THE PROBE MACHINE'S artifact** (imported 2026-08-11 evening, replacing the local NLTK rebuild) — the file every probe number was measured on | 56,881 sentences, ~1.0M words |
| `corpus_big.txt` | **THE PROBE MACHINE'S stack** (same import); embeds `corpus.txt` as a verified prefix — the non-Brown remainder is derivable as `lines[56881:]` | 253,371 sentences, ~5M words |
| `corpus_gutenberg.txt` / `corpus_reuters.txt` / combinations | per-source registry builds | components of the stack |
| `svd_*.npz` | derived caches (SVD-300 of PPMI); safe to delete, rebuilt deterministically from the pinned corpora in ~17 s | dense meaning vectors |
| `fixtures/` | workshop-v1 pinned test fixtures (interruption battery, held sentences, category vectors, segmentation docs) generated once by `scripts/make_fixtures.py` | see fixtures/README |

If a corpus file is regenerated for any reason, every downstream measured
number in HANDOFF.md must be re-validated — treat that as a probe, not a
refresh. (This was done once, deliberately, when the probe machine's
corpora were imported: the convergence probe in HANDOFF Part IV. It
retired two environment bands and re-fit the stage thresholds.)
