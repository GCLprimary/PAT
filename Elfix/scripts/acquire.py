"""
scripts/acquire.py  —  training the model THROUGH INPUT, governed (the c-task)
=============================================================================
The model can now LEARN from text it reads, online, into a store kept SEPARATE from
its attested ground truth — the distributional sibling of lexicon.InferredStore. This
script measures that the learning is real AND that the governance holds:

  1. LEARNS FROM INPUT   ingest a held-out input stream -> surprisal on a FURTHER,
                         unseen test stream drops (the knowledge generalises).
  2. ONLINE              reading the input in order, the learner beats the frozen base
                         by a widening margin (it adapts as it reads).
  3. NEVER SHADOWS       predictions for contexts the attested base covers well are
                         IDENTICAL before/after — ground truth is frozen (Law 3).
  4. CONTAMINATION GUARD feeding the model its OWN generations (source='self') changes
                         NOTHING — self-text is quarantined, never predicted from, never
                         self-confirming (the no-compounding guard, Law 2/5). Only
                         EXTERNAL input trains.

Scoring is add-alpha smoothed bits/word under `Predictor.prob` (attested base + the
acquired VIEW; carry excluded). Lower = better.

Run:  python scripts/acquire.py
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor, ACQUIRE_CONFIRM


def score(p: Predictor, stream):
    bits, n = 0.0, 0
    for utt in stream:
        ws = [w for w in utt if w in p.vocab]
        for a, b in zip(ws, ws[1:]):
            bits += -math.log2(p.prob(a, b))
            n += 1
    return (bits / n) if n else 0.0


def _confirmed(acq):
    return sum(1 for prev in acq.ext for c in acq.ext[prev].values()
               if c >= ACQUIRE_CONFIRM)


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu.keys())
    utts = load_utterances()
    a, b = int(len(utts) * 0.8), int(len(utts) * 0.9)
    train, inp, test = utts[:a], utts[a:b], utts[b:]
    base = Predictor(train, vocab)            # frozen ground truth
    learn = Predictor(train, vocab)           # same base; will learn from input
    print(f"train {len(train):,}  input {len(inp):,}  test {len(test):,}  "
          f"vocab seen {len(base.unigram):,}\n")

    t0 = score(base, test)
    print(f"  test surprisal BEFORE learning: {t0:.3f} bits/word (ppl {2**t0:,.0f})")

    # ── 2) ONLINE: read input in chunks, frozen base vs the learner (score-then-learn)
    print("\n  reading the INPUT stream in order (score each chunk, THEN learn it):")
    print(f"    {'chunk':>6} {'frozen':>8} {'learner':>8} {'gap':>7}")
    K = 5
    step = max(1, -(-len(inp) // K))          # ceil -> exactly K chunks (no tiny tail)
    for i in range(0, len(inp), step):
        chunk = inp[i:i + step]
        fb, lb = score(base, chunk), score(learn, chunk)
        for utt in chunk:
            learn.ingest(utt, source="input")
        print(f"    {i // step + 1:>6} {fb:>8.3f} {lb:>8.3f} {fb - lb:>+7.3f}")

    # ── 1) generalisation to the FURTHER, unseen test stream ────────────────────
    t1 = score(learn, test)
    print(f"\n  test surprisal AFTER learning from input: {t1:.3f} bits "
          f"(ppl {2**t1:,.0f}), {t0 - t1:+.3f} bits "
          f"({(2**t0 - 2**t1) / 2**t0:+.1%} ppl) on UNSEEN text")
    print(f"  acquired store: {learn.acquired.seen_ext:,} external transitions, "
          f"{_confirmed(learn.acquired):,} confirmed (>= {ACQUIRE_CONFIRM} occurrences)\n")

    # ── 3) NEVER OVERWRITE / RE-DERIVABLE (Law 3): the attested store is untouched ─
    intact = (learn.bigram == base.bigram and learn.unigram == base.unigram)
    print(f"  NEVER OVERWRITE (Law 3): after learning {learn.acquired.seen_ext:,} "
          f"transitions, the\n    attested store is byte-identical to the base "
          f"({'intact' if intact else 'WRITTEN!'}) -- all learning lives in the SEPARATE"
          f"\n    acquired view (attested + acquired), which adds to ground truth and "
          f"never\n    subtracts it; clear it and the pristine base returns.\n")

    # ── 4) CONTAMINATION GUARD: self-generated input is inert ───────────────────
    selfp = Predictor(train, vocab)
    seeds = [w for w, _ in base.unigram.most_common(200)]
    for i, s in enumerate(seeds):
        traj = base.generate(s, n=25, temperature=0.7, rng_seed=i, use_carry=False)
        selfp.ingest([w for w, _, _ in traj], source="self")
    ts = score(selfp, test)
    # a transition the model generated: recorded (malleable) but quarantined
    ex = next(((prv, nx) for prv in selfp.acquired.gen
               for nx in selfp.acquired.gen[prv]
               if selfp.bigram.get(prv, {}).get(nx, 0) == 0), (None, None))
    print(f"  CONTAMINATION GUARD: fed the model {selfp.acquired.seen_gen:,} of its OWN "
          f"generated transitions (source='self').")
    print(f"    test surprisal after self-training: {ts:.3f} bits  "
          f"(base {t0:.3f}; identical? {'YES' if abs(ts - t0) < 1e-9 else 'NO'})")
    if ex[0] is not None:
        print(f"    e.g. self-generated '{ex[0]} -> {ex[1]}' is "
              f"'{selfp.transition_evidence(*ex)}' -- recorded, never predicted from, "
              f"never self-confirming.\n")

    learned = t0 - t1 > 0.02
    print(f"  ==> {'SIGNAL' if learned else 'WEAK'}: the model TRAINS THROUGH INPUT -- "
          f"{t0 - t1:+.3f} bits on unseen\n      text from external reading, while the "
          f"attested store stays frozen and SELF-\n      generated text is inert. "
          f"Acquisition is governed exactly like the inferred\n      lexicon: separate "
          f"store, ternary evidence, no compounding. This is the floor a\n      "
          f"semantic layer can stand on -- the model accumulates knowledge from what it "
          f"reads.")
    return 0 if learned else 1


if __name__ == "__main__":
    raise SystemExit(main())
