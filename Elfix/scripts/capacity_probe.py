"""
scripts/capacity_probe.py  —  does ternary evidence actually fit in +/-8?
=============================================================================
PROVENANCE: [NEW->original]; Law 5 (ternary evidence), Law 1 (earned constants).
`converge_probe.py` style: REPORT, don't assert.

A mod-6 CRT packing (a SIGNATURE over feature bits) and a Z/17 accumulator (a
RUNNING SUM over ternary evidence) were proposed as the same object. They are
not the same object unless the accumulator's real dynamic range fits the state
space -- so this measures the range.

+/-8 is a CLAIM about dynamic range. Three ternary valences are tested, each a
Law-5-shaped +1 / 0 / -1 read on a real corpus quantity:

  voicing      +1 voiced, -1 voiceless, 0 vowel/unspecified
  sonority     +1 rising, -1 falling, 0 flat  (step-to-step)
  attestation  +1 bigram attested above median, -1 below, 0 unseen

Reports the running-sum excursion per word. If |max| routinely exceeds 8, the
capacity is wrong and 17 is not the state space. Verdict computed, not asserted.
For the inverse question -- what capacity does the corpus PICK -- see
`earned_capacity.py`.
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu, DEFAULT_CMU
from elfix.substrate.features import Phoneme
from elfix.substrate import features as F

CAP = 8          # the PROPOSED capacity under test (not earned -- that is the point)
FIT = 0.01       # stated budget: a capacity "fits" if under 1% of words overflow


def _inventory() -> dict:
    inv = {}
    for name in dir(F):
        obj = getattr(F, name)
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, Phoneme):
                    inv[k] = v
    return inv


def _excursion(steps) -> int:
    """Peak |running sum| over the step sequence."""
    acc = mx = 0
    for s in steps:
        acc += s
        mx = max(mx, abs(acc))
    return mx


def _report(name: str, excursions: list, cap: int = CAP) -> float:
    n = len(excursions)
    mxs = sorted(excursions)
    over = sum(1 for m in mxs if m > cap)

    def pct(q):
        return mxs[min(n - 1, int(q * n))]

    print(f"  {name}")
    print(f"    median |excursion| : {pct(0.50)}")
    print(f"    p95                : {pct(0.95)}")
    print(f"    p99                : {pct(0.99)}")
    print(f"    max                : {mxs[-1]}")
    print(f"    words exceeding +/-{cap} : {over}/{n}  ({over/n:.2%})")
    print(f"    -> {'FITS' if over / n < FIT else 'OVERFLOWS'} a +/-{cap} accumulator")
    print()
    return over / n


def main() -> int:
    cmu = load_cmu()
    inv = _inventory()
    words = [(w, p) for w, p in cmu.items() if all(s in inv for s in p)]
    print(f"corpus: {DEFAULT_CMU.name}  ({len(words)} words with full feature coverage)")
    print()
    print(f"MEASUREMENT  ternary accumulator dynamic range (capacity claim: +/-{CAP})")
    print(f"             stated fit budget: under {FIT:.0%} of words may overflow")
    print()

    rates = {}

    # --- valence 1: voicing -------------------------------------------------
    exc = []
    for _, phons in words:
        steps = []
        for s in phons:
            v = inv[s].voiced
            steps.append(1 if v is True else (-1 if v is False else 0))
        exc.append(_excursion(steps))
    rates["voicing"] = _report("voicing (+1 voiced / -1 voiceless / 0 vowel)", exc)

    # --- valence 2: sonority direction -------------------------------------
    exc = []
    for _, phons in words:
        steps, prev = [], None
        for s in phons:
            son = inv[s].sonority
            if prev is not None:
                steps.append(1 if son > prev else (-1 if son < prev else 0))
            prev = son
        exc.append(_excursion(steps))
    rates["sonority"] = _report("sonority direction (+1 rising / -1 falling / 0 flat)", exc)

    # --- valence 3: bigram attestation --------------------------------------
    bigrams = Counter()
    for _, phons in words:
        for a, b in zip(phons, phons[1:]):
            bigrams[(a, b)] += 1
    med = sorted(bigrams.values())[len(bigrams) // 2]
    exc = []
    for _, phons in words:
        steps = []
        for a, b in zip(phons, phons[1:]):
            c = bigrams.get((a, b), 0)
            steps.append(0 if c == 0 else (1 if c > med else -1))
        exc.append(_excursion(steps))
    rates["attestation"] = _report(
        f"bigram attestation (+1 above median {med} / -1 below / 0 unseen)", exc)

    # --- verdict ------------------------------------------------------------
    print("VERDICT")
    fitting = [k for k, v in rates.items() if v < FIT]
    failing = [k for k, v in rates.items() if v >= FIT]
    if fitting:
        print(f"  fits +/-{CAP}   : {', '.join(fitting)}")
    if failing:
        print(f"  overflows   : {', '.join(f'{k} ({rates[k]:.2%})' for k in failing)}")
    print()
    print("  'attestation' is the valence Law 5 literally describes (attested /")
    print("  silent / evidenced-against), and it is the one that overflows. A")
    print(f"  capacity that fits two valences and fails the defining one is not a")
    print("  capacity -- run earned_capacity.py for what the corpus picks instead.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
