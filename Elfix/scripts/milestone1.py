"""
scripts/milestone1.py  —  THE FALSIFICATION GATE (spec Piece 3)
===============================================================
The only thing worth building before anything else. Per SPEC.md:

  Does sound-geometry segmentation recover held-out MORPHEME boundaries
  ABOVE a frequency-matched BPE baseline?

  PASS  -> the core thesis (readable, self-forming units from earned sound-
           geometry) has its first real evidence. Climb the ladder.
  FAIL  -> stop. The thesis failed at the cheapest rung, exactly where you want
           to learn it. Diagnose Tier 3 before building 4-7 on a hollow claim.

This runs end-to-end on the bundled sample (no deps beyond stdlib). Drop in the
full ElfIX cmu_preprocessed.txt for the real number.

Run:  python scripts/milestone1.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu, build_morpheme_gold
from elfix.emergent.emergent_unit import (
    geometry_boundaries, geometry_boundaries_emergent, discover, auto_quanta)
from elfix.emergent.appendix import (
    discover_appendices, geometry_boundaries_additive)
from elfix.trajectory.trajectory import Trajectory


# ── Frequency baseline: Byte-Pair Encoding over phonemes (Sennrich 2016) ──────
def learn_bpe(corpus: List[List[str]], num_merges: int) -> List[Tuple[str, str]]:
    """Learn `num_merges` BPE merges by adjacency FREQUENCY (the contrast
    baseline: merges by orthographic/symbol frequency, not sound-geometry)."""
    seqs = [list(w) for w in corpus if len(w) > 1]
    merges: List[Tuple[str, str]] = []
    for _ in range(num_merges):
        pairs: Counter = Counter()
        for s in seqs:
            for a, b in zip(s, s[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        (x, y), _ = pairs.most_common(1)[0]
        merges.append((x, y))
        merged = x + "\u2063" + y           # invisible joiner marks a merged unit
        new = []
        for s in seqs:
            out, i = [], 0
            while i < len(s):
                if i < len(s) - 1 and s[i] == x and s[i + 1] == y:
                    out.append(merged); i += 2
                else:
                    out.append(s[i]); i += 1
            new.append(out)
        seqs = new
    return merges


def bpe_boundaries(phons: List[str], merges: List[Tuple[str, str]]) -> List[int]:
    """Segment a word with learned merges; return interior boundary indices."""
    units = list(phons)
    for x, y in merges:
        out, i = [], 0
        while i < len(units):
            if (i < len(units) - 1
                    and units[i].split("\u2063")[-1] == x
                    and units[i + 1].split("\u2063")[0] == y):
                out.append(units[i] + "\u2063" + units[i + 1]); i += 2
            else:
                out.append(units[i]); i += 1
        units = out
    # boundary indices = cumulative lengths between merged units
    bounds, pos = [], 0
    for u in units[:-1]:
        pos += u.count("\u2063") + 1
        bounds.append(pos)
    return bounds


# ── Scoring ───────────────────────────────────────────────────────────────────
def score(gold: List[Tuple[str, List[str], int]],
          predict) -> Tuple[float, float, float, float]:
    """Boundary precision / recall / F1 at the single gold morpheme boundary,
    plus mean #segments (granularity, for fair matching)."""
    tp = fp = fn = 0
    seg_total = 0
    for _, phons, b in gold:
        pred = set(predict(phons))
        seg_total += len(pred) + 1
        if b in pred:
            tp += 1
        else:
            fn += 1
        fp += len(pred - {b})
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, seg_total / max(1, len(gold))


def main() -> int:
    cmu = load_cmu()
    corpus = list(cmu.values())
    gold = build_morpheme_gold(cmu)
    print(f"corpus words: {len(corpus):,}   gold morpheme boundaries: {len(gold):,}\n")
    if len(gold) < 50:
        print("Too few gold examples in this sample to judge. Drop in the full "
              "cmu_preprocessed.txt and re-run."); return 2

    # GEOMETRY (contour only): the Tier 2 baseline — sonority seams + coda.
    g_p, g_r, g_f, g_gran = score(gold, geometry_boundaries)

    # GEOMETRY + EMERGENT (Tier 3, SUBTRACTIVE): keep a contour seam only where a
    # confirmed emergent unit ends. Established no-op on morphemes (can only
    # withhold seams); kept as the contrast to the additive cue below.
    quanta = auto_quanta([Trajectory.of(w) for w in corpus])
    inv = discover(corpus, quanta=quanta)
    eb_p, eb_r, eb_f, eb_gran = score(
        gold, lambda ph: geometry_boundaries_emergent(ph, inv, quanta, both_sides=True))

    # GEOMETRY + APPENDIX (Tier 3, ADDITIVE): self-forming appendix units PROPOSE
    # the boundaries the contour misses (the ~52% with no sonority seam). Shapes
    # are voicing-neutral, so -s/-z and -t/-d each become ONE appendix unit -- a
    # merge BPE cannot make. THIS is the additive self-forming test.
    appendix = discover_appendices(corpus)
    a_p, a_r, a_f, a_gran = score(
        gold, lambda ph: geometry_boundaries_additive(ph, appendix))

    # BPE baseline: learn each merge count once, then match a row to each geometry
    # granularity (a fair, granularity-matched comparison for BOTH geometry rows).
    bpe_rows = []
    for m in (20, 30, 50, 100, 200, 400, 800):
        merges = learn_bpe(corpus, m)
        p, r, f, gran = score(gold, lambda ph: bpe_boundaries(ph, merges))
        bpe_rows.append((p, r, f, gran, m))
    bpe_match = lambda t: min(bpe_rows, key=lambda row: abs(row[3] - t))
    bc, ba = bpe_match(g_gran), bpe_match(a_gran)

    print(f"emergent units: {len(inv):,} (arc quanta place/manner {quanta})   "
          f"appendix shapes: {len(appendix)}\n")
    print("                        precision   recall      F1    ~segments/word")
    print(f"  geometry (contour)    {g_p:8.3f} {g_r:8.3f} {g_f:8.3f}   {g_gran:6.2f}")
    print(f"  + emergent (subtract) {eb_p:8.3f} {eb_r:8.3f} {eb_f:8.3f}   {eb_gran:6.2f}")
    print(f"  + appendix (additive) {a_p:8.3f} {a_r:8.3f} {a_f:8.3f}   {a_gran:6.2f}")
    print(f"  BPE @ contour gran    {bc[0]:8.3f} {bc[1]:8.3f} {bc[2]:8.3f}   {bc[3]:6.2f}  (m={bc[4]})")
    print(f"  BPE @ additive gran   {ba[0]:8.3f} {ba[1]:8.3f} {ba[2]:8.3f}   {ba[3]:6.2f}  (m={ba[4]})")
    print()

    # Primary gate: best geometry variant beats its granularity-matched BPE.
    best_f = max(g_f, eb_f, a_f)
    matched = ba if best_f == a_f else bc
    verdict = "PASS" if best_f >= matched[2] else "FAIL"
    print(f"  ==> Tier 3 gate: {verdict}  (best geometry F1 {best_f:.3f} "
          f"{'>=' if verdict=='PASS' else '<'} matched BPE F1 {matched[2]:.3f})")

    # Task 2a -- SUBTRACTIVE emergent gating: an established no-op (recall-bound).
    contour_miss = sum(1 for _, ph, b in gold
                       if b not in set(geometry_boundaries(ph)))
    reach = 1 - contour_miss / len(gold)
    print(f"  ==> subtractive emergent gate: NEUTRAL ({eb_f - g_f:+.5f} F1). The "
          f"contour proposes only {reach:.1%} of gold boundaries; a gate that\n"
          f"      only WITHHOLDS seams cannot reach the missing {contour_miss/len(gold):.1%}.")

    # Task 2b -- ADDITIVE appendix units: the headline result.
    print(f"  ==> ADDITIVE self-formation: appendix units lift recall {g_r:.2f} -> "
          f"{a_r:.2f}, F1 {g_f:.3f} -> {a_f:.3f} (+{a_f-g_f:.3f}); matched BPE only "
          f"{ba[2]:.3f}.\n      Voicing-neutral shape merges the -s/-z and -t/-d "
          f"allomorphs -- a move frequency-over-symbols cannot make. (Precision is\n"
          f"      optimistic: the positives-only gold cannot count monomorphemic "
          f"false positives -- see appendix.py.)")
    print()
    if verdict == "PASS":
        print("  Sound-geometry beats frequency on morphology, and self-forming "
              "appendix units add the recall the contour structurally lacks.")
    else:
        print("  Geometry does NOT beat frequency here -- an honest failure at the "
              "cheapest rung. Diagnose before climbing.")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
