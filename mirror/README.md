# mirror — Reasoning Core Integration

The integration layer that composes the probe-validated organs
(probe suites 17–28) into one system — analysis AND generation:

| organ | module | what it is |
|---|---|---|
| **represent** | `mirror/embed.py` | voicing-neutral shape-bigram embeddings over ElfIX `(manner, place)` features; all vowels one bucket |
| **transform** | `mirror/transform.py` | seam-aware binding: `bind(base, suffix)` embeds the *concatenated* sequence so the junction bigram rides along (SEAM beats SUM: +0.12/+0.14 cosine) |
| **memory** | a_mem `EpisodeHooks` (unchanged) | grid-47 episodic lattice; embedding → id → anchors → stage |
| **loop** | `mirror/loop.py` | propose / reflect / settle-or-refuse at θ = 0.98 over three layers (bare, suffix-bound, prefix-bound); refuses what memory doesn't know |
| **decode** | `mirror/decode.py` | the inverse embedder: integer snap → Eulerian walk; the seam term is the invertibility condition (SUM-bound vectors refuse structurally) |
| **surface** | `mirror/surface.py` | count-induced allomorph table (99%+); rediscovers voicing assimilation and epenthesis with no hand-written rule |
| **generate** | `mirror/generate.py` | the reversed mirror: prompt-rung refusal, whole-continuation reflection, anti-rut; refuses word salad in plain language. Dual-corpus law: volume proposes, coherence judges |
| **regions** | `mirror/regions.py` | the centering law: frequency-weighted global component removed before any region/topic similarity; `between()` — the space's own answer to what lies between two topics (graph diffusion is a closed negative, probe 29) |
| **stage** | `mirror/stage.py` | the discourse stage: dual-threshold working memory — consonance is generous (θ_c), commitment is strict (θ_a); holds through interruptions (92% at-interrupt vs 0% memoryless), turns deliberately |
| **journey** | `mirror/journey.py` | topic-to-topic travel: itinerary waypoints steer the proposal pool (the corridor is set at proposal time); the reversed itinerary provably closes on the other end — causality, not correlation |
| **rulers** | `mirror/rulers.py` | the lattice unfolded linearly: exact ℤ[√2] stamps (irrational, for identity — never repeat) and the 5:4 phase ruler (rational, for rhythm — finds hidden cycles at 12× noise); each provably blind to the other's job |
| **registers** | `mirror/registers.py` | long-distance binding by exact stamps: stack behavior earned from arithmetic; nested dependencies 100% where unstamped falls to chance |
| **agreement** | `mirror/agreement.py` | the English test: a number register holds the subject to its verb through attractors (86% vs recent-noun's 14% seduction); subject identification is the frontier, not agreement |
| **diagnostics** | `mirror/diagnostics.py` | the imposter ceiling, three layers: the shape space's homoshape collisions make zero-confab a checkable property of a *vocabulary*, not the geometry (see HANDOFF Part V — the finding) |
| **meaning** | `mirror/meaning.py` + `mirror/rung.py` | window-4 PPMI count geometry (content-only contexts, ternary zero) densified by SVD-300 — *compression before corpus* — plus a source registry with an explicit-combination coherence policy, and the form\|meaning cross-modal rung |

Two laws worth naming:

- **Zero confabulation.** A word whose base memory doesn't know is refused,
  never invented (20/20 withheld refusals; hard test).
- **The laziness law.** Lowering θ makes the loop *worse* on knowns
  (4/20 at θ=0.90 vs 19/20 at θ=0.98) — an eager mirror settles for the
  first flattering reflection. Strictness is where the accuracy comes
  from; the inversion of this law is a canary test.

## Install & run

Prerequisites: `a-mem` installed (Phase 3 tree), the ElfIX repo at
`~/Elfix` or `~/OneDrive/Desktop/Elfix` (or set `MIRROR_ELFIX_PATH`),
NLTK with the Brown corpus (auto-downloaded on first meaning build).

```bash
pip install -e .
python examples/demo_core.py      # the analysis existence proof, ~3 s warm
python examples/demo_generate.py  # the generation existence proof, ~14 s
python examples/demo_workshop.py  # the stage and the journey, ~14 s
python -m pytest tests            # full acceptance suite, ~6 min
```

The itinerary is geometric, not argumentative — journeys steer through
meaning space, they do not plan narratives or arguments (a non-goal by
spec). Test fixtures and corpora are pinned artifacts (`data/README.md`);
regenerating them is a probe, not a refresh.

## Measured numbers (this build vs probe reference)

| metric | probe | this build |
|---|---|---|
| noisy self-recall @ cos 0.90 (25 words, grid-47) | 92% | **92%** |
| relative-form recall (unlocking → lock) | 78% | **78%** (7/9) |
| near-form discrimination | 3/3 | 3/3 |
| SEAM held-out cosine (shape) | 0.997 | **0.997** |
| SEAM − SUM margin (phon / shape) | +0.14 / +0.12 | **+0.140 / +0.119** |
| sibling-library retrieval (SEAM) | 39/39 | 40/40 (SUM also 40/40 — see HANDOFF) |
| loop known-set @ θ=0.98 | 19/20 (1 safe refusal) | **19/20 (1 safe refusal)** |
| loop withheld: refused / confabulated | 20/20 / 0 | **20/20 / 0** |
| laziness law @ θ=0.90 | 4/20 | **4/20** |
| relatedness triples | ≥ 90% | 21/21 = 100% |
| suffix offsets (report-only) | +0.022 vs −0.001 | +0.019..+0.023 vs ~0.000 |
| rung cross-modal (both directions) | 100% | **24/24 both** |
| demo_core runtime | < 30 s | 2.9 s |

Scaling build (probe 22): dense suffix offsets **+.074/+.065/+.084**
(sparse baseline ~+.022 — compression tripled what a 5× corpus couldn't
move), stacking sentinel green (the multi-genre stack halves the -s
offset), placement ceiling **41 episodes at grid 47** with 41/41
cross-modal recall at the ceiling.

Generation build (probes 23–28): integer snap **100%**, SUM-bound
structural refusal **199/200** (the seam-connectivity theorem),
allomorph induction **99.1/99.2%** with epenthesis rediscovered from
counts, prefix SEAM **1.000** with loop L3 at 18/20 and zero
confabulation, selective generation with salad refusal 99-100/100 and
emitted coherence **+0.323**, geodesic sentinel **83%**. The v3
path-action audit failed its promotion inequality — v2 stays default.
See HANDOFF Part III for the environment re-banding of G-4's gates.

Workshop v1 (probes 29–32): the dual-threshold stage holds **83%**
at-interrupt recall (memoryless 0%, single-θ 38%) at **100%** in-segment
(θ promoted to 0.35/0.55 by the pinned-battery sweep); steered journeys
close monotonically (+0.041 → +0.239) while departure completes (+0.060)
and the unsteered control stays flat; the **reversed itinerary mirrors
it** (final +0.250 toward the source — the spec-literal causality gate).
Audit-only steering is ~2× weaker: the corridor is set at proposal time.

**The convergence probe** (HANDOFF Part IV-b): importing the probe
machine's two corpus files reproduced the probe geometry to the third
decimal (offsets +.076/.066/.082, relatedness 20/20), restored the G-4
selectivity gap (55 ≥ 50) and the reversal gate (+0.250 ≥ +0.25) to
spec-literal, and confirmed the corpus-vintage hypothesis end to end.
Artifact over recipe, proven.

`HANDOFF.md` carries deviations and the ranked scaling menu. Build review
happens with the humans.
