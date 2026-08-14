# agent — The Shell

The creature. It perceives input, recalls against what it actually
knows, acts from a five-verb repertoire, refuses everything else by
name, and learns only at teachable moments — refusal plus confirmation,
with receipts. Composed entirely from probe-validated organs
(`a_mem` + `mirror`); the shell adds no new physics.

```
perceive → segment → recall → act → respond → write* → next
                                        (*only on teachable moments)
```

## The laws (all hard asserts)

1. **The refusal spine is total.** Zero confabulation in every battery,
   both memory arms, all input shapes. A wrong assertion anywhere fails
   the build.
2. **Refusal is the teachable moment.** Learning is triggered by refusal
   plus confirmation — never by silent inference. Every episode write
   logs its provenance: which input, which refusal, what confirmed it.
3. **Artifact over recipe.** Fixtures and corpora are pinned files with
   recorded checksums; the batteries run on them or not at all.
4. **One bad clause poisons nothing.** An alien verb is refused by name
   and its neighbors are unharmed.

## The five verbs

| verb | what happens | refuses when |
|---|---|---|
| `analyze <w>` | mirror loop: bare / derived via SEAM / refuse (θ = 0.98) | no analysis stands |
| `relates <w>` | top-3 dense meaning neighbors, content-filtered | off-vocabulary |
| `remember <b>` | the law-2 write path; idempotent | unlearnable form |
| `know <b>` | yes/no from the library, truthfully | never — it always answers |
| `walk <a> to <b>` | a workshop journey: itinerary, propose-time steering, per-leg closure | unattested prompt, off-vocabulary endpoint |

Anything else: `'translate' is not something I do.`

## Run it

```bash
pip install -e .            # needs a-mem and mirror installed (local editables)
python -m agent.cli         # talk to it; 'quit' saves
python examples/demo_creature.py   # the life story, ~26 s
python -m pytest tests      # the batteries, ~80 s
```

## Measured numbers (this build vs probe reference)

| metric | probe | this build |
|---|---|---|
| learning gap (ON − OFF, final third) | 60 pts (gate ≥ 40) | **60 pts** (75% vs 15%) |
| confabulations, all arms and batteries | 0 | **0** |
| per-clause accuracy, k = 1..6 | 92–100% | **92–100%** |
| flatness (k=6 vs k=1) | flat | 97% vs 100% |
| alien refusal / clean-clause containment | 100% / 100% | **16/16 / 100%** |
| teach→use within input | 14/19 | **15/19** |
| survives restart (relatives of taught bases) | ≥ 4/5 | **5/5** |
| demo_creature runtime | < 60 s | 26 s |

`HANDOFF.md` carries deviations and the next-frontier ranking. The
creature rests — and unlike every system before it in this project, it
rests *knowing things it was taught*, on disk, with receipts.
