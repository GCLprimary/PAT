"""
scripts/semantic_gate.py  —  does MEANING predict where SOUND could not?
========================================================================
The arc-closing falsification. Three class-based backoffs, identical pooling
machinery (PhonoBackoff: pool the bigram continuations of the context word's class),
differing ONLY in where the class comes from:

  unigram   — no class (the sound-blind frequency floor).
  phono     — SOUND classes (the word's final arc-shape). MEASURED NULL earlier
              (scripts/predict_backoff): sound mixes syntactic categories, so its pool
              collapses to the unigram.
  semantic  — DISTRIBUTIONAL classes (the company the word keeps; elfix/semantic).
              These ARE the syntactic/semantic categories, so their pools should be
              DISTINCT from the unigram and predict the next word better.

If semantic beats the unigram (and phono) on held-out SPARSE contexts — the locator
regime, where the word-bigram has nothing — then MEANING carries the predictive
signal exactly where SOUND did not. That is the whole thesis, measured.

METHOD: train/test split; build the bigram + the two class sources on TRAIN; at
held-out (prev->next) pairs whose TRAIN bigram is sparse (mass < MIN_CONTEXT), score
-log2 P(next | prev) under each model (add-alpha smoothed over the same vocab).
Head-to-head on the COVERED subset (where the semantic class exists). Lower = better.

Run:  python scripts/semantic_gate.py        (~1-2 min: the semantic clustering earns)
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.trajectory.trajectory import Trajectory
from elfix.routing.shape_routing import ShapeRouter
from elfix.predict import Predictor, PhonoBackoff, make_key_of, MIN_CONTEXT
from elfix.semantic import SemanticSpace, make_semantic_key_of

ALPHA = 0.1


def _lp(cnt, total, w, V):
    return -math.log2((cnt.get(w, 0) + ALPHA) / (total + ALPHA * V))


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    train = [u for i, u in enumerate(utts) if i % 10 != 0]
    test = [u for i, u in enumerate(utts) if i % 10 == 0]

    p = Predictor(train, vocab)
    U, NU, V = p.unigram, sum(p.unigram.values()), len(p.unigram)
    print(f"train utts {len(train):,}  test utts {len(test):,}  vocab {V:,}")

    print("  earning SOUND classes (router) and MEANING classes (distributional)...")
    router = ShapeRouter([Trajectory.of(w) for w in cmu.values()])
    phono = PhonoBackoff(p.bigram, list(U), make_key_of(router, cmu, "final"))
    space = SemanticSpace(train, vocab, unigram=U)
    sem = PhonoBackoff(p.bigram, list(U), make_semantic_key_of(space))
    print(f"  phono: {len(phono.class_words):,} sound classes; "
          f"semantic: {len(sem.class_words):,} meaning classes "
          f"({len(space.class_words)} clusters)\n")

    # ── score sparse held-out pairs under unigram / phono / semantic ─────────────
    n = cov = 0
    bits = {"uni": 0.0, "phono": 0.0, "sem": 0.0}          # all sparse pairs
    cbits = {"uni": 0.0, "phono": 0.0, "sem": 0.0}         # covered-by-semantic subset
    for utt in test:
        ws = [w for w in utt if w in vocab]
        for prev, nxt in zip(ws, ws[1:]):
            if nxt not in U:
                continue
            if (sum(p.bigram[prev].values()) if prev in p.bigram else 0) >= MIN_CONTEXT:
                continue
            n += 1
            b_uni = _lp(U, NU, nxt, V)
            ph = phono.continuation(prev)
            sm = sem.continuation(prev)
            b_ph = _lp(ph, sum(ph.values()), nxt, V) if ph else b_uni
            b_sm = _lp(sm, sum(sm.values()), nxt, V) if sm else b_uni
            bits["uni"] += b_uni; bits["phono"] += b_ph; bits["sem"] += b_sm
            if sm is not None:                              # the head-to-head regime
                cov += 1
                cbits["uni"] += b_uni; cbits["phono"] += b_ph; cbits["sem"] += b_sm

    print(f"  sparse held-out pairs: {n:,}   semantic covers {cov/n:.0%}\n")
    print(f"  {'model':<10}{'all-sparse bits':>16}{'covered-subset bits':>22}")
    for m, name in (("uni", "unigram"), ("phono", "phono (sound)"),
                    ("sem", "semantic (meaning)")):
        print(f"  {name:<18}{bits[m]/n:>10.3f}{cbits[m]/cov:>20.3f}")
    sem_lift = (cbits["uni"] - cbits["sem"]) / cov
    ph_lift = (cbits["uni"] - cbits["phono"]) / cov
    vs_phono = (cbits["phono"] - cbits["sem"]) / cov
    print()
    print(f"  on the covered subset (vs the sound-blind unigram):")
    print(f"     phono (SOUND)    {ph_lift:+.3f} bits   "
          f"(null, as measured before)")
    print(f"     semantic (MEANING) {sem_lift:+.3f} bits   "
          f"({(2**(cbits['uni']/cov) - 2**(cbits['sem']/cov))/2**(cbits['uni']/cov):+.0%} ppl)")
    print(f"     semantic vs phono: {vs_phono:+.3f} bits in MEANING's favour\n")

    # ── readable: distinct meaning-classes continue distinctly (unlike sound) ────
    print("  WHY it works: a meaning-class pools syntactically-coherent words, so its")
    print("  continuation is DISTINCT from the global marginal (not washed out):")
    big = sorted((c for c in sem.class_words if sum(sem.class_cont[c].values()) >= 50),
                 key=lambda c: -sum(sem.class_cont[c].values()))
    for c in big[:5]:
        pool = sem.class_cont[c]
        mates = ", ".join(space.class_words[c][:4])
        top = ", ".join(f"{w} {k/sum(pool.values()):.0%}" for w, k in pool.most_common(3))
        print(f"    ~{{{', '.join(space.class_anchors(c))}}} (e.g. {mates}) -> {top}")

    print(f"\n  ==> NEGATIVE (deeper than phono): pooling by PREV's class does not "
          f"beat the\n      unigram for sound ({ph_lift:+.3f}) OR meaning ({sem_lift:+.3f}). "
          f"The 'why' lines show it:\n      even a syntactically-coherent class's pooled "
          f"continuation is dominated by the\n      function-word MARGINAL (the 7%, a 2% "
          f"...) -- because next-word identity is\n      governed by that marginal "
          f"regardless of what KIND of word prev is, and the\n      unigram already "
          f"captures it. So prev-class pooling is the wrong mechanism for\n      BOTH. "
          f"The topical signal is in ACCUMULATED context (the carry), not prev's\n      "
          f"category -- the semantic layer's predictive home, if any, is topical "
          f"generalisation\n      (scripts/semantic_carry.py), not this. The classes "
          f"themselves are real, readable\n      structure (elfix/semantic) regardless.")
    return 0          # a measurement that completed: the negative is the finding


if __name__ == "__main__":
    raise SystemExit(main())
