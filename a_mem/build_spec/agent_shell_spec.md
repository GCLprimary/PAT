# agent — The Shell · Build Specification (probes 33–34)

**Location:** `~/agent` (working name; the builder of record calls it the
creature — rename at will). New repo; imports a_mem and mirror, owns neither.
**House rules unchanged:** tests before features; acceptance by inequality;
flag, don't reconcile; build → `HANDOFF.md` → stop.
**Reference probes delivered:** probe33 (the loop: learning gap 60 pts,
zero confabulation both arms), probe34 (input composition: flat complexity
curve, perfect alien containment).

**The job (ruled):** respond to user input. Responses are ORGANS-ONLY —
structured and honest, never fluent-for-fluency; the phrasing slot stays
open by design (D-5) and empty in v0. World: closed word-world.

**Laws carried into the shell:**
1. **The refusal spine is total.** Zero confabulation is a hard assert in
   every battery, both memory arms, all input shapes. A wrong assertion
   anywhere fails the build.
2. **Refusal is the teachable moment.** Learning is triggered BY refusal
   plus confirmation — never by silent inference. Every episode write logs
   its provenance (which input, which refusal, what confirmed it).
3. **Artifact over recipe.** Corpora and test fixtures are the pinned files
   (checksums recorded); thresholds ship with calibration provenance.
4. **One bad clause poisons nothing.** Containment is a hard assert.

---

## A-1 · `agent/loop.py` — the creature's heartbeat

`Agent(store_path)`: perceive (input string) → segment (clauses on
connectives) → per clause: recall (known-base library + bound proposals +
meaning vocabulary) → act (repertoire) → respond (structured record) →
write (only on law-2 teachable moments) → next. Sessions persist: the
episode store is a_mem's on-disk library; `Agent` restarted on the same
path knows everything it was ever taught.
- **test_survives_restart:** teach 5 bases, destroy the process, construct
  a new Agent on the same path, analyze relatives of the taught bases —
  ≥ 4/5 succeed, zero confabulation. (This is the original promise of the
  whole project — the agent that loses its context and recovers from
  memory — asserted at the creature level.)

## A-2 · `agent/repertoire.py` — five verbs and the alien law

- `analyze <w>` — mirror loop (bare / derived via SEAM proposals / refuse),
  θ = 0.98.
- `relates <w>` — meaning neighbors (top-3, dense, content-filtered);
  refuse off-vocabulary.
- `remember <b>` — law-2 write path; idempotent on known bases.
- `know <b>` — yes/no from the library, truthfully.
- `walk <a> to <b>` — the crown as a verb: workshop journey (itinerary,
  propose-time steering); returns legs + per-leg closure numbers; refuses
  unattested prompts and off-vocabulary endpoints exactly as V-3 gates.
- **The alien law:** any other verb → plain refusal naming the verb
  ("'translate' is not something I do"). Hard test with a verb list the
  repertoire has never seen.
Routing is exact-verb in the closed world; ship it behind a protocol class
(`Router`) so richer routing can attach later without touching the loop —
the decode-boundary pattern.

## A-3 · Batteries (the probes as regression suites)

- **test_learning_battery** (probe 33, pinned stream): memory-ON final-third
  minus memory-OFF final-third ≥ 40 points (measured 60); zero confab both
  arms; every ON gain traces to a logged write (assert the provenance log
  covers the accuracy delta's bases).
- **test_composition_battery** (probe 34, pinned inputs): per-clause
  accuracy ≥ 90% at every k in 1..6 (measured 92–100%); flatness
  regression: acc(k=6) ≥ acc(k=1) − 10 points; alien refusal 100% and
  clean-clause accuracy in alien-bearing inputs ≥ 95% (measured 100%);
  teach→use within-input ≥ 14/19 band; zero confab.
- **test_journey_verb:** two `walk` requests (one feasible → legs with
  rising centered closure; one unattested prompt → plain refusal).

## A-4 · `agent/cli.py` — talk to it

A REPL: prompt in, structured response out, one line per clause; `quit`
saves. The response format is honest by construction — every line is one
of: an analysis, a neighbor list, a learned/known acknowledgment, a
journey's legs with numbers, or a refusal that names its reason. No
padding, no pretense of chat.

## A-5 · `examples/demo_creature.py`

< 60 s, the life story in one run: fresh agent knows 15 bases → handles a
6-clause input (with one alien, contained) → refuses an unknown base →
is taught it → analyzes its relatives → walks a journey between two topics
→ process "dies" → a new Agent on the same store analyzes another relative
of the taught base correctly. Print the provenance log at the end: every
thing it knows, and how it came to know it.

## A-6 · Close-out

`HANDOFF.md`: numbers, deviations, and the next-frontier ranking
(standing: stage integration — multi-topic sessions with the dual-threshold
stage segmenting long inputs; richer routing behind the Router protocol;
the phrasing slot; open-world vocabulary growth). **Stop.** The creature
rests — and unlike every system before it in this project, it rests
*knowing things it was taught*, on disk, with receipts.

## Non-goals
Fluency and the phrasing slot, external LMs, stage/multi-topic sessions
(ranked, not built), open-world routing, tools beyond the five verbs,
performance work.
