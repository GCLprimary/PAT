"""R-3 acceptance (probe 37b): the English agreement test, pinned.

The register holds the sentence-initial subject to its verb; the
recent-noun control gets seduced by attractors (that seduction is the
control that proves the attractors are real); the trigram control does
what volume can. Subject identification is the frontier, not agreement
(law 3): the broken first miner (probe 37, adjunct mislabels) stays in
a_mem/probes as evidence.
"""
import json

import pytest

from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def fixture():
    return json.loads((FIX / "agreement_cases.json").read_text(
        encoding="utf-8"))


def split_accuracy(cases, pred):
    buckets = {False: [0, 0], True: [0, 0]}
    for c in cases:
        p = pred(c)
        if p is None:
            continue
        b = buckets[c["attractor"]]
        b[0] += int(p == c["gold"])
        b[1] += 1
    return {k: (v[0] / v[1] if v[1] else None, v[1])
            for k, v in buckets.items()}


def test_agreement_register_vs_controls(fixture):
    cases = fixture["cases"]
    print(f"\n{fixture['n_cases']} cases, {fixture['n_attractors']} "
          f"attractors; lexicon {fixture['lexicon_sizes']}")

    register = split_accuracy(cases, lambda c: c["subj_n"])
    recent = split_accuracy(
        cases, lambda c: (c["between_nouns"][-1][1]
                          if c["between_nouns"] else c["subj_n"]))
    trigram = split_accuracy(cases, lambda c: c["trigram_pred"])

    for name, r in (("REGISTER", register), ("recent-noun", recent),
                    ("trigram", trigram)):
        print(f"  {name:12s} no-attr {r[False][0]:.0%} ({r[False][1]})   "
              f"attr {r[True][0]:.0%} ({r[True][1]})")

    reg_no, reg_at = register[False][0], register[True][0]
    rec_at = recent[True][0]
    tri_at = trigram[True][0]

    assert reg_no >= 0.90, f"REGISTER no-attractor {reg_no:.0%} < 90%"
    assert reg_at >= rec_at + 0.30, \
        f"REGISTER attractor {reg_at:.0%} not >= recent-noun {rec_at:.0%} + 30"
    assert reg_at >= tri_at, \
        f"REGISTER attractor {reg_at:.0%} < trigram {tri_at:.0%}"
    # the seduction assertion: the control must be seduced, or the
    # fixture's attractors aren't attractors
    assert rec_at <= 0.40, \
        f"FLAG: recent-noun at {rec_at:.0%} under attraction — the " \
        f"fixture's attractors aren't attractors"


def test_lexicon_hygiene(fixture):
    """Ambiguous sg/pl forms were dropped at lexicon build (law 4)."""
    sizes = fixture["lexicon_sizes"]
    assert sizes["sg"] > 10_000 and sizes["pl"] > 10_000
    assert sizes["sg"] == sizes["pl"]        # one derived form per base