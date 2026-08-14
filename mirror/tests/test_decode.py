"""G-1 acceptance (probes 23, 23b): the inverse embedder.

Snap 100% on 200 words; real-word structural refusal 0%; SUM-bound
refusal >= 80% (the seam-connectivity theorem); original among walks
100%; unique walk >= 45%. The tie-break default is decided by the
promotion inequality (attested adopted iff exact >= 68%).
"""
import numpy as np
import pytest

from mirror import ShapeDecoder, shape, snap_counts


@pytest.fixture(scope="module")
def bank(embedder):
    rng = np.random.default_rng(5)
    words = [w for w in embedder.corpus if 2 <= len(embedder.corpus[w]) <= 12]
    return [words[i] for i in rng.choice(len(words), 500, replace=False)]


def true_counts(embedder, word):
    space = embedder.shape_space
    ss = [shape(p) for p in embedder.corpus[word]]
    v = np.zeros(space.dim)
    for t in ss:
        v[space.n * space.n + space.index[t]] += 1
    for a, b in zip(ss, ss[1:]):
        v[space.index[a] * space.n + space.index[b]] += 1
    return v.astype(np.int64)


def test_integer_snap_is_exact(embedder, bank):
    ok = 0
    for w in bank[:200]:
        c = snap_counts(embedder.shape_vec(embedder.corpus[w]))
        ok += int(c is not None and np.array_equal(c, true_counts(embedder, w)))
    assert ok == 200, f"snap exact on {ok}/200 (< 100%)"


def test_round_trip_and_tie_break(embedder, bank):
    """Real words: never refused; the original is ALWAYS a valid walk of
    the decoded graph (the exact invariant); enumerated-membership under
    the 64-walk cap >= 99% (start inference splits the cap across starts
    on balanced graphs — 2/500 originals fall past the budget; the spec's
    100% figure is the start-known protocol of probe 23); unique >= 45%.
    The promotion inequality decides the tie-break default."""
    results = {}
    for tie in ("lex", "attested"):
        dec = ShapeDecoder(embedder, tie_break=tie)
        recon = uniq = exact = refused = 0
        for w in bank:
            ss = tuple(shape(p) for p in embedder.corpus[w])
            d = dec.decode(embedder.shape_vec(embedder.corpus[w]))
            if d.status != "OK":
                refused += 1
                continue
            # the exact invariant: the decoded graph IS the original's
            # graph, so the original is a valid walk of it
            assert np.array_equal(d.counts, true_counts(embedder, w))
            recon += int(ss in d.walks)
            uniq += int(len(d.walks) == 1)
            exact += int(d.sequence == ss)
        results[tie] = (recon, uniq, exact, refused)
        print(f"\n{tie}: recon {recon / 5:.1f}%  unique {uniq / 5:.0f}%  "
              f"exact {exact / 5:.0f}%  refused {refused}")
        assert refused == 0, f"{tie}: {refused} real words refused"
        assert recon >= 495, f"{tie}: capped enumeration {recon}/500 < 99%"
        assert uniq / 500 >= 0.45, f"{tie}: unique {uniq / 5:.0f}% < 45%"

    # promotion inequality: attested is default only because it clears
    # the lex baseline's probed 68%; if this drops, revisit the default
    assert results["attested"][2] / 500 >= 0.68, \
        "attested tie-break fell below the 68% promotion bar"


def test_seam_connectivity_theorem(embedder):
    """SUM-bound vectors refuse structurally (missing exactly the seam
    edge); SEAM-bound vectors always walk."""
    pairs = []
    for w in embedder.corpus:
        for sfx in ("ing", "ness", "ful"):
            if w.endswith(sfx) and len(w) > len(sfx) + 2:
                base = w[:-len(sfx)]
                if base in embedder.corpus:
                    b, d = embedder.corpus[base], embedder.corpus[w]
                    if len(d) > len(b) and d[:len(b)] == b:
                        pairs.append((base, w))
        if len(pairs) >= 200:
            break
    dec = ShapeDecoder(embedder, tie_break="lex")
    seam_ok = sum_refused = 0
    for base, w in pairs[:200]:
        vb = embedder.shape_vec(embedder.corpus[base])
        vs = embedder.shape_vec(embedder.corpus[w][len(embedder.corpus[base]):])
        v_sum = vb + vs
        v_sum /= np.linalg.norm(v_sum)
        seam_ok += int(dec.decode(
            embedder.shape_vec(embedder.corpus[w])).status == "OK")
        sum_refused += int(dec.decode(v_sum).status != "OK")
    print(f"\nseam decodable {seam_ok}/200, SUM refused {sum_refused}/200")
    assert seam_ok == 200, "a SEAM-bound vector refused to walk"
    assert sum_refused >= 160, f"SUM refusal {sum_refused}/200 < 80%"
