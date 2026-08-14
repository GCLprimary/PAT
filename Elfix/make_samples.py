"""
make_samples.py  —  build the bundled data samples by SEEDED RANDOM sampling
============================================================================
WHY THIS EXISTS (a reproduction note, not a nicety): the original bundled
samples were alphabetical head-cuts of the full files (a -> "contraptions").
An alphabetical slice is not a random one — it over-represents shared
orthographic prefixes, which hands the frequency (BPE) baseline exactly the
regularity it feeds on and silently INVERTS the headline comparison on a fresh
checkout (sample: geometry F1 ~0.31 vs BPE; full corpus: geometry F1 ~0.94).
A sample that flips the repo's central claim is worse than no sample.

Fix: sample lines uniformly at random with a FIXED SEED, so the bundled sample
is (a) representative, (b) reproducible, and (c) regenerable by anyone holding
the full files. Law 3 applies to data too: the sample is a derived VIEW of the
full corpus — this script is its single source of truth.

Variant lines like "a(2)" are kept or dropped exactly as sampled (load_cmu
already skips them); no other filtering, so the sample stays an honest draw.

Run:  python make_samples.py            # requires data/cmu_preprocessed.txt
                                        # (and data/stress.txt if present)
"""
from __future__ import annotations
import random
from pathlib import Path

SEED = 42
N = 25_000
DATA = Path(__file__).resolve().parent / "data"

PAIRS = [
    ("cmu_preprocessed.txt", "cmu_sample.txt"),
    ("stress.txt", "stress_sample.txt"),
]


def sample_file(full: Path, out: Path, n: int = N, seed: int = SEED) -> None:
    lines = [l for l in full.read_text(encoding="utf-8").splitlines() if l.strip()]
    rng = random.Random(seed)
    if len(lines) <= n:
        chosen = lines
    else:
        chosen = rng.sample(lines, n)
    chosen.sort()  # sorted for stable diffs; sampling, not order, is what matters
    out.write_text("\n".join(chosen) + "\n", encoding="utf-8")
    print(f"  {out.name}: {len(chosen):,} lines sampled from {full.name} "
          f"({len(lines):,}) with seed {seed}")


def main() -> int:
    made = 0
    for full_name, sample_name in PAIRS:
        full = DATA / full_name
        if not full.exists():
            print(f"  SKIP {sample_name}: source {full_name} not present "
                  f"(drop it into data/ and re-run)")
            continue
        sample_file(full, DATA / sample_name)
        made += 1
    return 0 if made else 1


if __name__ == "__main__":
    raise SystemExit(main())
