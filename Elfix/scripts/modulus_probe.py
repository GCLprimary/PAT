"""
scripts/modulus_probe.py  —  earn the congruence modulus from the corpus
=============================================================================
PROVENANCE: [NEW->original]; polynomial hashing / Rabin-Karp (Karp & Rabin 1987),
CRT packing (standard). Written in `converge_probe.py` style: REPORT, don't
assert; verdict computed at the end.

Answers the "how is the modulus earned?" hole. Every candidate rule below derives
p from a MEASURED quantity, and the collision rate of each is then measured
against the real lexicon rather than assumed from the bound.

Law 1 check: no constant here comes from outside the data. The only inputs are
the corpus and a stated collision budget (a REQUIREMENT, not a constant -- it is
chosen by the operator and reported, not discovered).

TWO MEASUREMENTS THAT ARE EASY TO SKIP AND MUST NOT BE (both were reported in an
earlier write-up with no script behind them; they are implemented here):
  M5  the BASE sweep. The polynomial base x matters more than the modulus: with
      x below the alphabet size the polynomial is not injective BEFORE the mod is
      applied, so the collision rate plateaus no matter how large p grows.
  M6  the feature-bundle merge cost. Signatures computed over feature bundles
      cannot distinguish phonemes that share a bundle; this prices that in
      word-pairs against the irreducible true-homophone floor.
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu, DEFAULT_CMU
from elfix.substrate.features import Phoneme
from elfix.substrate import features as F

# The one operator input, stated (Law 1): how much collision may the HASH add on
# top of the lexicon's own irreducible duplicate rate?
HASH_TOLERANCE = 0.002          # 0.2 percentage points


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def _next_prime(n: int) -> int:
    p = max(2, n)
    while not _is_prime(p):
        p += 1
    return p


def _bundle(ph: Phoneme) -> tuple:
    """The feature bundle, as an orderable tuple. Identity of a phoneme in
    feature space -- two phonemes with the same bundle are indistinguishable
    to any feature-based signature."""
    return (ph.kind, ph.place, ph.manner, ph.voiced,
            ph.height, ph.backness, ph.rounded,
            getattr(ph, "rhotic", None), getattr(ph, "offglide", None))


def _inventory() -> dict:
    inv = {}
    for name in dir(F):
        obj = getattr(F, name)
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, Phoneme):
                    inv[k] = v
    return inv


def _dup_rate(seqs) -> tuple:
    """(# words sharing their sequence with >=1 other, rate). The lexicon's own
    duplicate floor when seqs are phoneme strings; the merge cost when they are
    bundle-code strings."""
    seen = Counter(seqs)
    shared = sum(c for c in seen.values() if c > 1)
    return shared, shared / max(1, len(seqs))


def main() -> int:
    cmu = load_cmu()
    inv = _inventory()
    print(f"corpus: {DEFAULT_CMU.name}  ({len(cmu)} entries)")
    print()

    # ---- MEASUREMENT 1: alphabet and feature-bundle cardinality -------------
    attested = Counter()
    for phons in cmu.values():
        attested.update(phons)

    n_symbols = len(attested)
    bundles, unmapped = {}, []
    for sym in attested:
        ph = inv.get(sym)
        if ph is None:
            unmapped.append(sym)
            continue
        bundles.setdefault(_bundle(ph), []).append(sym)
    n_bundles = len(bundles)

    print("MEASUREMENT 1  alphabet / feature bundles")
    print(f"  distinct phoneme symbols attested : {n_symbols}")
    print(f"  distinct feature bundles          : {n_bundles}")
    if unmapped:
        print(f"  symbols with no feature entry     : {len(unmapped)} {sorted(unmapped)[:12]}")
    collisions = {k: v for k, v in bundles.items() if len(v) > 1}
    print(f"  bundles shared by >1 symbol       : {len(collisions)}")
    for _, v in sorted(collisions.items(), key=lambda kv: str(kv[0])):
        print(f"      {sorted(v)}")
    print()

    # ---- MEASUREMENT 2: word length distribution ---------------------------
    lens = sorted(len(p) for p in cmu.values())
    n = len(lens)

    def pct(q):
        return lens[min(n - 1, int(q * n))]

    L_max = lens[-1]
    print("MEASUREMENT 2  word length in phonemes")
    for label, val in (("max", L_max), ("p99.9", pct(0.999)), ("p99", pct(0.99)),
                       ("p95", pct(0.95)), ("median", pct(0.50))):
        print(f"  {label:8s} : {val}")
    print(f"  {'mean':8s} : {sum(lens)/n:.2f}")
    print()

    # ---- MEASUREMENT 3: candidate moduli, each from a measured quantity ----
    print("MEASUREMENT 3  candidate moduli (each derived, none chosen)")
    cands = {
        "bundle_cardinality": _next_prime(n_bundles),
        "symbol_cardinality": _next_prime(n_symbols),
        "max_length": _next_prime(L_max),
        "p999_length": _next_prime(pct(0.999)),
    }
    # root-count rule: a nonzero difference polynomial of degree < L has at most
    # L-1 roots, so at most (L-1)/p evaluation points are bad.
    for budget in (0.01, 0.001):
        cands[f"root_budget_{budget:g}"] = _next_prime(int((L_max - 1) / budget))
    # birthday rule: expected fraction of words in a random collision is n/(2p),
    # so p >= n / (2 * tolerance) makes the HASH's own contribution <= tolerance.
    n_words = len(cmu)
    cands[f"birthday_{HASH_TOLERANCE:g}"] = _next_prime(int(n_words / (2 * HASH_TOLERANCE)))
    for name, p in sorted(cands.items(), key=lambda kv: kv[1]):
        print(f"  {name:24s} -> p = {p}")
    print()

    # ---- MEASUREMENT 4: MEASURED collision rate per candidate --------------
    bundle_idx = {b: i for i, b in enumerate(sorted(bundles.keys(), key=str))}
    sym_code = {s: bundle_idx[b] for b, syms in bundles.items() for s in syms}

    def sig(phons, p, x):
        h = 0
        for s in phons:
            h = (h * x + sym_code.get(s, 0) + 1) % p
        return h

    words = [(w, p) for w, p in cmu.items() if all(s in sym_code for s in p)]
    # base must be >= the number of distinct codes for the polynomial to be
    # injective before reduction (see M5). Earned from the alphabet, not chosen.
    x_earned = n_bundles
    print(f"MEASUREMENT 4  measured collision rate  ({len(words)} words with full "
          f"feature coverage, base x = {x_earned})")
    print(f"  {'modulus':>12}  {'buckets used':>13}  {'colliding words':>16}  {'rate':>9}")
    for name, p in sorted(set(cands.items()), key=lambda kv: kv[1]):
        seen = Counter(sig(ph, p, x_earned) for _, ph in words)
        colliding = sum(c for c in seen.values() if c > 1)
        print(f"  {p:>12}  {len(seen):>13}  {colliding:>16}  {colliding/len(words):>8.4f}")
    print()

    # ---- MEASUREMENT 5: the BASE sweep (the base matters more than p) ------
    p_big = cands[f"birthday_{HASH_TOLERANCE:g}"]
    print(f"MEASUREMENT 5  base sweep at p = {p_big}  (alphabet = {n_bundles} bundles)")
    print("  codes run 0..{}, so the polynomial is injective only for x >= {};".format(
        n_bundles - 1, n_bundles))
    print("  below that it collides BEFORE the mod is applied and no modulus can")
    print("  repair it. Primality of x buys nothing here -- x = alphabet suffices.")
    print(f"  {'base x':>8}  {'colliding words':>16}  {'rate':>9}")
    for x in (2, 3, 5, 17, 31, n_bundles, x_earned, _next_prime(2 * n_bundles)):
        seen = Counter(sig(ph, p_big, x) for _, ph in words)
        colliding = sum(c for c in seen.values() if c > 1)
        flag = "  <- x > alphabet" if x > n_bundles else ""
        print(f"  {x:>8}  {colliding:>16}  {colliding/len(words):>8.4f}{flag}")
    print()

    # ---- MEASUREMENT 6: what the bundle merge costs ------------------------
    print("MEASUREMENT 6  cost of computing signatures over BUNDLES, not symbols")
    true_shared, true_rate = _dup_rate([tuple(ph) for _, ph in words])
    code_shared, code_rate = _dup_rate(
        [tuple(sym_code[s] for s in ph) for _, ph in words])
    print(f"  true homophones (identical phoneme strings) : {true_shared:>7}  {true_rate:.4%}")
    print(f"  identical BUNDLE-CODE sequences             : {code_shared:>7}  {code_rate:.4%}")
    print(f"  merge cost                                  : {code_rate - true_rate:+.4%}"
          f"  ({code_shared - true_shared} extra words made indistinguishable)")
    print("  the true-homophone rate is English and irreducible; the excess is a")
    print("  SUBSTRATE limitation, fixable by adding the distinguishing feature.")
    print()

    # ---- VERDICT -----------------------------------------------------------
    print("VERDICT")
    print(f"  base    : x = {x_earned}  (the {n_bundles}-code alphabet; smallest injective base)")
    print(f"  modulus : p = {p_big}  (birthday rule at the stated {HASH_TOLERANCE:g} tolerance)")
    seen = Counter(sig(ph, p_big, x_earned) for _, ph in words)
    rate = sum(c for c in seen.values() if c > 1) / len(words)
    # The hash operates on BUNDLE CODES, so its own contribution is measured
    # against the bundle-code duplicate rate -- not against true homophones,
    # which would charge the hash for the substrate's merge as well.
    excess = rate - code_rate
    print()
    print("  the collision rate decomposes into three named parts:")
    print(f"    {true_rate:>8.4%}  true homophones      (English; irreducible)")
    print(f"    {code_rate - true_rate:>+8.4%}  bundle merge         (SUBSTRATE defect; fixable)")
    print(f"    {excess:>+8.4%}  the hash itself      (tunable via p)")
    print(f"    {rate:>8.4%}  total measured")
    print(f"  -> the hash is {'WITHIN' if excess <= HASH_TOLERANCE else 'OVER'} "
          f"the stated {HASH_TOLERANCE:g} tolerance")
    print()
    print("  NOTE  no SMALL modulus can be an identity key: 17 buckets cannot hold")
    print(f"        {len(words)} words. If a small prime has a job it is as an")
    print("        ACCUMULATOR state space, never as a hash. See earned_capacity.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
