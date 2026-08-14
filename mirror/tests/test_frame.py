"""F-1 acceptance (probe 38): the widened frame — tiers, not thresholds.

Scope frames, don't replace them: coverage is bought bucket by bucket,
and every bucket wears its price as a per-tier measured precision.
Tier-1 must reproduce the strict-frame regression; the full frame must
multiply the attractor evidence (n >= 2x strict's 12) while the
seduction control stays seduced; tier-2 is reported in a band; tier-3
is REPORT-ONLY (asserting 57% at n=7 would be pretending); and the
coordination refusal category must stay live — the amendment that
refuses conjoined subjects rather than guessing.
"""
import json

import pytest

from mirror.agreement import EXPERIMENTAL_TIERS, REFUSAL_TAXONOMY
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def fixture():
    return json.loads((FIX / "agreement_v2_cases.json").read_text(
        encoding="utf-8"))


def accuracy(cases, pred):
    ok = n = 0
    for c in cases:
        p = pred(c)
        if p is None:
            continue
        ok += int(p == c["gold"])
        n += 1
    return (ok / n if n else None), n


def register(c):
    return c["subj_n"]


def recent_noun(c):
    return c["between_nouns"][-1][1] if c["between_nouns"] else c["subj_n"]


def trigram(c):
    return c["trigram_pred"]


def test_fixture_counts_recorded(fixture):
    """Every bucket wears its price: the counts are pinned, coherent,
    and the refusal taxonomy is the named one."""
    cases = fixture["cases"]
    assert fixture["n_cases"] == len(cases)
    assert sum(fixture["buckets"].values()) == len(cases)
    assert fixture["n_attractors"] == sum(1 for c in cases if c["attractor"])
    assert set(fixture["refusals"]) <= set(REFUSAL_TAXONOMY)
    assert fixture["experimental_tiers"] == list(EXPERIMENTAL_TIERS)
    print(f"\nv2 frame: {fixture['n_cases']} cases "
          f"({fixture['n_attractors']} attractors), buckets "
          f"{fixture['buckets']}, refusals {fixture['refusals']}, "
          f"strict-subset agreement "
          f"{fixture['strict_subset_agreement'][0]}/"
          f"{fixture['strict_subset_agreement'][1]}")


def test_tier1_reproduces_strict_regression(fixture):
    """The strict regression on the tier-1 subset — the STRICT-CERTIFIED
    core (v2 cases the strict frame also accepts): REGISTER no-attractor
    >= 90%, attractor >= recent-noun + 30. The plain bucket as a whole
    is WIDER than the strict frame (it admits non-PP-chain material the
    strict frame refused) and wears its own measured price, printed
    below — the tier system's whole point."""
    cert = [c for c in fixture["cases"] if c["strict_certified"]]
    no_att = [c for c in cert if not c["attractor"]]
    att = [c for c in cert if c["attractor"]]
    reg_no, n_no = accuracy(no_att, register)
    reg_at, n_at = accuracy(att, register)
    rec_at, _ = accuracy(att, recent_noun)
    print(f"\nstrict-certified core ({len(cert)}): REGISTER no-attr "
          f"{reg_no:.0%} ({n_no})  attr {reg_at:.0%} ({n_at})  "
          f"recent-noun attr {rec_at:.0%}")
    t1 = [c for c in fixture["cases"] if c["tier"] == 1]
    t1_no, t1_n = accuracy([c for c in t1 if not c["attractor"]], register)
    print(f"whole plain bucket's price: no-attr {t1_no:.0%} ({t1_n})")
    assert len(cert) >= 200, f"certified core collapsed ({len(cert)})"
    assert reg_no >= 0.90, \
        f"certified-core REGISTER no-attractor {reg_no:.0%} < 90%"
    assert reg_at >= rec_at + 0.30, \
        f"certified-core REGISTER attr {reg_at:.0%} not >= " \
        f"recent {rec_at:.0%} + 30"


def test_full_frame_attractors(fixture):
    """The point of widening: at least 2x the strict frame's 12
    attractors, REGISTER >= 70% on them, and the seduction control
    still seduced (recent-noun <= 40%) — or they aren't attractors."""
    att = [c for c in fixture["cases"] if c["attractor"]]
    reg_at, n_at = accuracy(att, register)
    rec_at, _ = accuracy(att, recent_noun)
    tri_at, _ = accuracy(att, trigram)
    print(f"\nfull-frame attractors n={n_at}: REGISTER {reg_at:.0%}  "
          f"recent-noun {rec_at:.0%}  trigram {tri_at:.0%}")
    assert n_at >= 2 * 12, f"attractor n {n_at} < 2x strict's 12"
    assert reg_at >= 0.70, f"full-frame REGISTER attractor {reg_at:.0%} < 70%"
    assert rec_at <= 0.40, \
        f"FLAG: recent-noun {rec_at:.0%} under attraction — " \
        f"the widened frame's attractors aren't attractors"


def test_tier2_band_reported(fixture):
    """Tier-2 (adjunct-led) precision is recorded in a band — small n,
    report, don't over-assert (probe: 75% at n=16)."""
    t2 = [c for c in fixture["cases"] if c["tier"] == 2]
    acc, n = accuracy(t2, register)
    print(f"\ntier-2 REGISTER {acc:.0%} (n={n})")
    assert n >= 10, f"tier-2 bucket collapsed (n={n})"
    assert 0.50 <= acc <= 1.0, \
        f"tier-2 precision {acc:.0%} left its band — re-measure, re-price"


def test_tier3_report_only(fixture):
    """Tier-3 (relative) is EXPERIMENTAL: the number is printed and the
    flag is pinned; no accuracy assert exists on purpose."""
    t3 = [c for c in fixture["cases"] if c["tier"] == 3]
    acc, n = accuracy(t3, register)
    print(f"\ntier-3 REGISTER {acc:.0%} (n={n}) — REPORT-ONLY, experimental")
    assert 3 in fixture["experimental_tiers"], \
        "tier-3 lost its experimental flag — did a probe earn that?"
    assert all(c["bucket"] == "relative" for c in t3)


def test_coordination_refusal_live(fixture):
    """The amendment must stay live: conjoined material between subject
    and verb is refused by name, never guessed at."""
    assert fixture["refusals"].get("coordination", 0) > 0, \
        "the coordination refusal category went silent"
