"""R-4 acceptance (probe 35, CORRECTED): the safety case in three layers.

Owner-ruled after the finding contradicted the spec's literal gate:
the open-vocabulary imposter ceiling is EXACTLY 1.0 — the voicing-
neutral shape space is many-to-one at the word level, so zero
confabulation is a property of a VOCABULARY (checkable), not of the
geometry. These tests assert the finding itself as canaries: if a
future shape-space change restores injectivity, they fail loudly and
the strong safety claim can be re-examined — deliberately, not by
accident.
"""
import json
from collections import defaultdict

import pytest

from mirror import MirrorLoop, PhonGate, imposter_ceiling, shape
from mirror.config import DATA_DIR
from mirror.diagnostics import realized_ceiling, shape_collisions
from mirror.loop import THETA_DEFAULT

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def split():
    return json.loads((FIX / "imposter_split.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def banks():
    return json.loads((FIX / "battery_banks.json").read_text(
        encoding="utf-8"))


def test_layer1_the_collision_finding(embedder, transform, split):
    """The population truth, asserted as a canary."""
    byb = defaultdict(dict)
    for b, s, w, _ in transform.pairs:
        byb[b][s] = w
    cands = sorted([b for b, d in byb.items()
                    if len(d) >= 2 and len(b) >= 4])
    groups = shape_collisions(embedder, cands)
    involved = sum(len(v) for v in groups.values())
    rate = involved / len(cands)
    print(f"\ncensus: {len(groups)} collision groups, {involved}/"
          f"{len(cands)} bases involved ({rate:.1%})")
    assert 0.40 <= rate <= 0.65, \
        "the collision census moved — the shape space changed character"
    # the pair that sat live in the shipped learning battery
    assert tuple(shape(p) for p in embedder.corpus["cell"]) == \
        tuple(shape(p) for p in embedder.corpus["seal"]), \
        "cell/seal no longer collide — restore the strong safety case?"

    report = imposter_ceiling(
        embedder, transform, split["known_bases"],
        [tuple(x) for x in split["known_forms"]],
        [tuple(x) for x in split["unknown_forms"]])
    assert report.ceiling == 1.0, \
        "the open-split ceiling dropped below 1.0 — collisions gone?"
    assert report.collisions, "no collisions recorded in the open split"


def test_layer2_the_near_miss_continuum(embedder, transform, split):
    """Among genuinely distinct shapes, the ceiling is a continuum that
    GROWS with vocabulary (0.9769 at the probe's draw, ~0.984 at n=40) —
    recorded, with true-binding mass asserted."""
    report = imposter_ceiling(
        embedder, transform, split["known_bases"],
        [tuple(x) for x in split["known_forms"]],
        [tuple(x) for x in split["unknown_forms"]])
    print(f"\nceiling_distinct {report.ceiling_distinct:.4f}  "
          f"true mean {report.true_mean:.4f}  true min "
          f"{report.true_min:.4f}  plateau {report.plateau_width:.4f}  "
          f"(n_true {report.n_true}, n_wrong {report.n_wrong})")
    assert report.true_mean >= 0.99
    assert 0.95 <= report.ceiling_distinct < 1.0
    # hygiene still necessary (and now proven insufficient)
    known = set(split["known_bases"])
    for _, _, w in split["known_forms"] + split["unknown_forms"]:
        assert w not in known, f"'{w}' survived the hygiene filter"
    assert split["hygiene_dropped"], "law-4 hygiene was not exercised"


def test_layer3_the_batteries_explained(embedder, transform, banks):
    """What the pinned batteries actually exposed. The composition
    battery's realized ceiling sits under theta (its clean run was
    geometry); the learning battery contained the cell/seal imposter at
    exactly 1.0 (its clean run was tie order — the canary)."""
    c_ceil, c_arg = realized_ceiling(
        embedder, transform, banks["composition_bases"],
        [tuple(x) for x in banks["composition_observed"]])
    l_ceil, l_arg = realized_ceiling(
        embedder, transform, banks["learning_bases"],
        [tuple(x) for x in banks["learning_observed"]])
    print(f"\ncomposition realized ceiling {c_ceil:.4f} at {c_arg}")
    print(f"learning    realized ceiling {l_ceil:.4f} at {l_arg}")
    assert c_ceil < THETA_DEFAULT, \
        f"composition battery ceiling {c_ceil:.4f} crossed theta"
    assert l_ceil == 1.0 and l_arg[0] == "cell", \
        "the learning battery's cell/seal canary moved"


def test_canary_gated_pipeline_kill(embedder, transform):
    """THE F-2 CANARY: the gated pipeline's false-accept count on the
    pinned attack fixture is ZERO. Part V's finding stands unchanged —
    the SHAPE space is many-to-one and its open-vocabulary ceiling is
    exactly 1.0 (the three canaries above); what changed is that the
    pipeline no longer rests on it. If this test fails, the phon gate
    stopped covering the collision layer and Part VI's unconditional
    zero-confabulation claim is VOID — go read Part V's finding before
    touching anything."""
    sets = json.loads((FIX / "phon_gate_sets.json").read_text(
        encoding="utf-8"))
    gate = PhonGate.from_transform(transform)
    by_b1 = defaultdict(list)
    for B1, B2, sfx, w2 in sets["attacks"]:
        by_b1[B1].append(w2)
    false_accepts = 0
    for B1, words in by_b1.items():
        loop = MirrorLoop(embedder, transform,
                          {B1: embedder.corpus[B1]}, gate=gate)
        for w in words:
            a = loop.analyze(embedder.corpus[w])
            false_accepts += int(a.mode != "REFUSE")
    print(f"\ngated pipeline on the attack fixture: "
          f"{false_accepts}/{len(sets['attacks'])} false accepts")
    assert false_accepts == 0, \
        f"{false_accepts} gated false accepts — the unconditional " \
        f"zero-confabulation claim is VOID (see HANDOFF Part V)"