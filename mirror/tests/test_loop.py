"""W-3 acceptance (probe 20): the mirror loop.

Known set >= 17/20 correct at theta 0.98; withheld set refused 20/20 with
ZERO confabulation (hard); and the laziness law as a test — a laxer
mirror must do WORSE (measured 4/20 at 0.90 vs 19/20 at 0.98). If the
laziness law ever inverts, the embedder or corpus changed character.
"""
from collections import defaultdict

import numpy as np
import pytest

from mirror import MirrorLoop


@pytest.fixture(scope="module")
def loop_setup(embedder, transform):
    """Probe-20 sampling: base sets drawn from the SHUFFLED pair order."""
    rng2 = np.random.default_rng(11)
    byb = defaultdict(dict)
    for base, sfx, w, _ in transform.pairs:
        byb[base][sfx] = w
    cands = [b for b, d in byb.items() if len(d) >= 1 and len(b) >= 4]
    rng2.shuffle(cands)
    known, withheld = cands[:40], cands[40:80]

    def pick(bases, n=20):
        out = []
        for b in bases:
            for sfx, w in byb[b].items():
                out.append((b, sfx, w))
                break
            if len(out) >= n:
                break
        return out

    loop = MirrorLoop(embedder, transform,
                      {b: embedder.corpus[b] for b in known})
    return loop, pick(known), pick(withheld)


def run(loop, embedder, tests, theta):
    correct = refused = confabulated = 0
    for b, sfx, w in tests:
        a = loop.analyze(embedder.corpus[w], theta)
        if a.mode == "REFUSE":
            refused += 1
        elif a.base == b and a.suffix == sfx:
            correct += 1
        else:
            confabulated += 1
    return correct, refused, confabulated


def test_known_set_at_strict_theta(embedder, loop_setup):
    """Amended (generation spec): the known-set gate is a BAND, >= 16/20
    across sampling protocols — the shuffled canonical order measures
    19/20, the raw mining order 16/20. Zero-confabulation and the
    laziness inversion remain absolute."""
    loop, known, _ = loop_setup
    correct, refused, _ = run(loop, embedder, known, 0.98)
    print(f"\nknown @0.98: {correct}/20 correct, {refused} refused")
    assert correct >= 16, f"known-set accuracy {correct}/20 < 16/20 (band rule)"


def test_withheld_zero_confabulation(embedder, loop_setup):
    """The hard law: an unknown base must be refused, never invented."""
    loop, _, withheld = loop_setup
    _, refused, confabulated = run(loop, embedder, withheld, 0.98)
    assert refused == 20, f"only {refused}/20 withheld words refused"
    assert confabulated == 0, f"{confabulated} confabulations — LAW BROKEN"


def test_laziness_law(embedder, loop_setup):
    """Strictness is where the accuracy comes from: theta 0.90 must be
    WORSE than 0.98 on knowns. If this inverts, flag the build."""
    loop, known, _ = loop_setup
    lax, _, _ = run(loop, embedder, known, 0.90)
    strict, _, _ = run(loop, embedder, known, 0.98)
    print(f"\nlaziness: @0.90 {lax}/20 vs @0.98 {strict}/20")
    assert lax < strict, \
        f"laziness law inverted ({lax} >= {strict}) — embedder/corpus changed character"
