"""
scripts/lexicon_gate.py  —  holdout falsification gate for lexicon growth
=========================================================================
Reconstruct each inflected CMU word's pronunciation from its (in-CMU) STEM + the
earned allomorphy, and score EXACT match vs the real CMU pronunciation, stratified
by suffix. The word's own entry is never consulted, so this is self-contained on
CMU — it needs NO running text.

PASS: earned allomorphy beats a no-allomorphy baseline (same decompositions, a
fixed allomorph per suffix) — proving the earned voicing rule is load-bearing, not
decoration. The earned - baseline DELTA isolates the allomorphy from any
decomposition noise (both score on the same splits). See spec_lexicon_growth.md.

Run:  python scripts/lexicon_gate.py
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.lexicon.ortho_affix import decompose, discover_suffixes, INFLECTIONAL
from elfix.lexicon.compose_pron import compose

# no-allomorphy baseline: the majority allomorph per suffix, applied unconditionally
_BASELINE = {"s": ["z"], "es": ["IH", "z"], "ed": ["d"], "ing": ["IH", "NG"],
             "er": ["ER"], "est": ["IH", "s", "t"]}


def main() -> int:
    cmu = load_cmu()
    in_lex = cmu.__contains__
    earned = discover_suffixes(cmu.keys())
    print(f"vocab: {len(cmu):,}   earned suffixes (frac .5, len<=3): "
          f"{sorted(earned)}")
    print(f"v1 inflectional set {list(INFLECTIONAL)} all earned: "
          f"{all(s in earned for s in INFLECTIONAL)}\n")

    cases = []                                  # (true_pron, stem, suffix)
    for w, pron in cmu.items():
        d = decompose(w, in_lex)
        if d:
            stem, suf = d[0]                    # longest-suffix split
            cases.append((pron, cmu[stem], suf))
    print(f"decomposable inflected words: {len(cases):,}\n")

    per = defaultdict(lambda: [0, 0, 0])        # suffix -> [n, earned_ok, base_ok]
    tot = [0, 0, 0]
    reg_n = reg_ok = 0                           # "regular" = stem pron preserved
    for pron, stem_pron, suf in cases:
        earned_pron = compose(stem_pron, suf)
        base_pron = list(stem_pron) + _BASELINE[suf]
        e_ok, b_ok = (earned_pron == pron), (base_pron == pron)
        per[suf][0] += 1; per[suf][1] += e_ok; per[suf][2] += b_ok
        tot[0] += 1; tot[1] += e_ok; tot[2] += b_ok
        if pron[:len(stem_pron)] == stem_pron:  # stem preserved -> real, regular
            reg_n += 1; reg_ok += e_ok

    print(f"  {'suffix':6} {'n':>8} {'earned':>9} {'baseline':>10}")
    for suf in INFLECTIONAL:
        n, e, b = per[suf]
        if n:
            print(f"  {suf:6} {n:8,} {e/n:9.1%} {b/n:10.1%}")
    n, e, b = tot
    print(f"  {'ALL':6} {n:8,} {e/n:9.1%} {b/n:10.1%}\n")

    delta = (e - b) / n
    verdict = "PASS" if e > b else "FAIL"
    print(f"  ==> lexicon gate: {verdict}  (earned {e/n:.1%} vs no-allomorphy "
          f"baseline {b/n:.1%}; +{delta:.1%} from the earned voicing rule)")
    print("  The same rule that SEGMENTS the -s/-z, -t/-d allomorphs (appendix.py) "
          "GENERATES the right one here.")

    # Precision analysis: the overall number force-decomposes monomorphemic in-vocab
    # look-alikes (thing -> the+ing) that DEPLOYMENT looks up rather than decomposes.
    # On REGULAR decompositions (stem pron preserved -- v1's actual scope) compose is
    # far cleaner. Phonotactic validation does NOT separate the look-alikes (measured:
    # recognition & coda-legality ~no-op -- they are well-formed); precision comes from
    # OOV-only scoping + Stage 4 corroboration, not a critic.
    print(f"\n  precision analysis:")
    print(f"    overall (force-decompose all 28k):              {e/n:.1%}")
    print(f"    on REGULAR decompositions (stem preserved, n={reg_n:,}): {reg_ok/reg_n:.1%}")
    print(f"    -> the gap is monomorphemic in-vocab look-alikes deployment looks up.")
    return 0 if e > b else 1


if __name__ == "__main__":
    raise SystemExit(main())
