"""G-3 acceptance (probe 25): prefix breadth — the S-4 gate, unlocked.

Prefix SEAM held-out cosine >= 0.99 with SEAM > SUM; loop L3 known-set
>= 16/20 (band rule); withheld refusal 20/20 with zero confabulation
(absolute).
"""
import numpy as np
import pytest

from mirror import MirrorLoop, mine_prefix_pairs


@pytest.fixture(scope="module")
def prefixed(embedder, transform):
    pairs = mine_prefix_pairs(embedder.corpus)
    transform.fit_prefixes(pairs)
    return transform


def test_prefix_mining(prefixed):
    assert len(prefixed.prefix_pairs) >= 2300     # measured 2,583
    assert set(prefixed.prefixes) >= {"un", "re", "dis", "mis", "pre"}


def test_prefix_seam_beats_sum(embedder, prefixed):
    test = prefixed.prefix_test[:400]
    seam = [float(prefixed.bind_prefix(embedder.corpus[b], p) @
                  embedder.shape_vec(embedder.corpus[w]))
            for b, p, w, _ in test]
    sum_ = [float(prefixed.bind_prefix_sum(embedder.corpus[b], p) @
                  embedder.shape_vec(embedder.corpus[w]))
            for b, p, w, _ in test]
    m_seam, m_sum = float(np.mean(seam)), float(np.mean(sum_))
    print(f"\nprefix SEAM {m_seam:.3f}  SUM {m_sum:.3f}")
    assert m_seam >= 0.99, f"prefix SEAM held-out {m_seam:.3f} < 0.99"
    assert m_seam > m_sum


def test_loop_l3(embedder, prefixed):
    """Probe-25 sampling; the loop runs its full L1->L2->L3 ladder."""
    test = prefixed.prefix_test
    known = sorted({b for b, _, _, _ in test})[:40]
    with_t = [(b, p, w) for b, p, w, _ in test if b in known][:20]
    withheld = sorted({b for b, _, _, _ in test} - set(known))[:40]
    wo_t = [(b, p, w) for b, p, w, _ in test if b in withheld][:20]

    loop = MirrorLoop(embedder, prefixed,
                      {b: embedder.corpus[b] for b in known})
    ok = 0
    for b, p, w in with_t:
        a = loop.analyze(embedder.corpus[w])
        ok += int(a.mode == "PRE" and a.base == b and a.prefix == p)
    refused = confab = 0
    for b, p, w in wo_t:
        a = loop.analyze(embedder.corpus[w])
        if a.mode == "REFUSE":
            refused += 1
        else:
            confab += 1
    print(f"\nL3 known {ok}/20; withheld refused {refused}/20, "
          f"confabulated {confab}")
    assert ok >= 16, f"L3 known-set {ok}/20 < 16/20 (band rule)"
    assert refused == 20 and confab == 0, "L3 confabulated — LAW BROKEN"
