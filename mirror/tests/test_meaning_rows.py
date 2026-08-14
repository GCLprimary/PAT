"""X-6: the literature row — sentinels, not gates.

WS-353 (sim/rel) and SimLex-999 at 5.2M words, the honest small-corpus
point: recorded bands +-0.03 around the measured centers. If a row
drifts, THE MEANING ORGAN CHANGED CHARACTER — corpus, PPMI recipe,
SVD, or centering — and the 10M-corpus frontier loses its baseline;
that is what the failure message says. Benchmark files are vendored
(vecto-ai/word-benchmarks; WordSim-353: Finkelstein et al. 2001,
sim/rel split Agirre et al. 2009; SimLex-999: Hill et al. 2015) and
manifest-pinned; tests never fetch.
"""
import hashlib
import json
from pathlib import Path

import pytest

from mirror.config import DATA_DIR
from mirror.meaning_rows import meaning_rows

VENDOR = Path(__file__).resolve().parent / "fixtures" / "meaning"
BANDS = {                       # measured at build; probe-47-exact
    "WS353-sim": 0.433,
    "WS353-rel": 0.244,
    "SimLex-999": 0.160,
}
TOL = 0.03


@pytest.fixture(scope="module")
def rows():
    manifest = json.loads(
        (DATA_DIR / "fixtures" / "meaning_manifest.json").read_text(
            encoding="utf-8"))
    for name, expected in manifest.items():
        got = hashlib.sha256((VENDOR / name).read_bytes()).hexdigest()
        assert got == expected, f"{name} drifted from its manifest"
    return meaning_rows({
        "WS353-sim": VENDOR / "wordsim353-sim.csv",
        "WS353-rel": VENDOR / "wordsim353-rel.csv",
        "SimLex-999": VENDOR / "simlex999.csv",
    })


def test_sentinel_rows(rows):
    print("\nbenchmark     pairs  covered   Spearman rho   band")
    for name, (n, cov, rho) in rows.items():
        print(f"  {name:11s} {n:5d}   {cov:4d}     {rho:+.3f}       "
              f"{BANDS[name]:+.3f} ± {TOL}")
        assert cov / n >= 0.97, f"{name}: coverage collapsed ({cov}/{n})"
        assert abs(rho - BANDS[name]) <= TOL, \
            f"SENTINEL: {name} rho {rho:+.3f} left its band " \
            f"{BANDS[name]:+.3f} ± {TOL} — THE MEANING ORGAN CHANGED " \
            f"CHARACTER (corpus, PPMI, SVD, or centering); the " \
            f"10M-corpus frontier just lost its baseline"
