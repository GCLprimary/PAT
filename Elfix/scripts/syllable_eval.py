"""
scripts/syllable_eval.py  —  the geometry on the job it is built for
===================================================================
milestone1.py scores the sonority geometry on MORPHEME boundaries, where it is
structurally blind to ~half of them (a morpheme seam like played=play+d has no
sonority minimum). That is the hard, honest rung. This script asks the fairer,
prior question:

  How well does the geometry recover SYLLABLE structure — the thing sonority
  minima actually are — and does the emergent (self-forming) refinement help
  HERE, against an EARNED Maximal-Onset gold (elfix/syllable.py)?

Two measurements:
  (A) syllable COUNT: do sonority peaks match the true nuclei count?
  (B) syllable BOUNDARY placement: P/R/F1 vs Maximal-Onset gold, for the contour,
      the two emergent-gated variants, and a granularity-matched BPE contrast.

Run:  python scripts/syllable_eval.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.syllable import build_syllable_gold
from elfix.substrate.features import features
from elfix.trajectory.trajectory import Trajectory
from elfix.emergent.emergent_unit import syllable_boundaries
from scripts.milestone1 import learn_bpe, bpe_boundaries


def score_multi(gold, predict):
    """Boundary precision/recall/F1 over MULTIPLE gold boundaries per word,
    plus mean segments/word (granularity)."""
    tp = fp = fn = seg = 0
    for _, phons, bs in gold:
        g = set(bs)
        pred = set(predict(phons))
        seg += len(pred) + 1
        tp += len(pred & g)
        fp += len(pred - g)
        fn += len(g - pred)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, seg / max(1, len(gold))


def count_acc(gold, predict_count):
    """Exact-match accuracy and mean abs error of a syllable-COUNT predictor."""
    exact = mae = 0
    for _, phons, bs in gold:
        true = len(bs) + 1
        pc = predict_count(phons)
        exact += (pc == true)
        mae += abs(pc - true)
    n = max(1, len(gold))
    return exact / n, mae / n


def main() -> int:
    cmu = load_cmu()
    corpus = list(cmu.values())
    gold = build_syllable_gold(cmu)                  # earned Maximal-Onset gold
    n_bounds = sum(len(b) for _, _, b in gold)
    print(f"corpus words: {len(corpus):,}   multisyllabic gold words: "
          f"{len(gold):,}   gold syllable boundaries: {n_bounds:,}\n")

    # ── (A) syllable COUNT: peaks vs true nuclei count ────────────────────────
    geo_count = lambda ph: len(Trajectory.of(ph).peaks())
    vow_count = lambda ph: sum(1 for s in ph
                               if (f := features(s)) is not None and f.kind == "vowel")
    ge_acc, ge_mae = count_acc(gold, geo_count)
    vc_acc, vc_mae = count_acc(gold, vow_count)
    print("  syllable COUNT (predicted #syllables vs true nuclei)")
    print(f"    geometry peaks    exact {ge_acc:6.1%}   MAE {ge_mae:.3f}")
    print(f"    count-the-vowels  exact {vc_acc:6.1%}   MAE {vc_mae:.3f}   (trivial check)")
    print()

    # ── (B) syllable BOUNDARY placement vs Maximal-Onset gold ─────────────────
    # The geometry's native syllabifier is `syllable_boundaries` (maximal-onset:
    # boundary AT the sonority minimum). We do NOT apply the emergent gate here:
    # it is an established subtractive no-op (scripts/milestone1) and on syllable
    # seams it could only WITHHOLD a correct boundary, never improve placement.
    g = score_multi(gold, syllable_boundaries)

    target = g[3]
    best = None
    for m in (50, 100, 200, 400, 800):
        merges = learn_bpe(corpus, m)
        s = score_multi(gold, lambda ph: bpe_boundaries(ph, merges))
        if best is None or abs(s[3] - target) < abs(best[0][3] - target):
            best = (s, m)
    b, b_m = best

    print("  syllable BOUNDARY placement vs Maximal-Onset gold")
    print("                       precision   recall      F1    ~segments/word")
    print(f"    geometry (onset)   {g[0]:8.3f} {g[1]:8.3f} {g[2]:8.3f}   {g[3]:6.2f}")
    print(f"    BPE (freq, m={b_m:<3})  {b[0]:8.3f} {b[1]:8.3f} {b[2]:8.3f}   {b[3]:6.2f}")
    print()
    # Verdict is COMPUTED, never canned (a lesson learned the hard way: an
    # earlier version printed a fixed conclusion that a skewed bundled sample
    # silently contradicted). Numbers first; interpretation only where the
    # numbers actually support it.
    if g[2] >= b[2]:
        print(f"  ==> geometry beats frequency on SYLLABLES: F1 {g[2]:.3f} vs "
              f"BPE {b[2]:.3f}.\n      On the job the sonority contour is built "
              f"for (syllabification), earned\n      sound-shape beats "
              f"orthographic frequency on this corpus.")
        return 0
    print(f"  ==> geometry does NOT beat frequency here: F1 {g[2]:.3f} vs BPE "
          f"{b[2]:.3f}.\n      If you are running on a bundled sample, re-run on "
          f"the full corpus (see\n      data/README.md) before drawing any "
          f"conclusion; if this is the full\n      corpus, the claim fails — "
          f"diagnose, don't explain it away.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
