"""T-2/T-3 batteries: the compass fold (probes 60, 61), probe-exact.

The census, the separation, and the invertibility are pinned to the
probe's own numbers — the lexicon is the same import, so the numbers
must be bit-equal, not merely close. The homoshape healing battery
(T-4) prints the scar and its cure together: the shape space still
confuses colliding bases (Part X's canary recorded 0.9903 on the
chapter fold), and the compass tells every one of them apart.
"""
from collections import Counter, defaultdict

import numpy as np
import pytest

from mirror import mine_pairs
from mirror.compass import (P7, P8, WINDOW, decode, dial_bit, fold,
                            locality_violations)
from mirror.diagnostics import shape_seq


@pytest.fixture(scope="module")
def census(embedder):
    """Probe 60's collision census: same counts, different orders."""
    sig = defaultdict(list)
    for w, p in embedder.corpus.items():
        if len(p) < WINDOW:
            sig[tuple(sorted(p))].append((w, tuple(p)))
    return {k: v for k, v in sig.items()
            if len({pr for _, pr in v}) >= 2}


def test_tangency_and_bitplanes(embedder):
    """Probe 61 #1/#2: the dials nest with zero slack over every
    position the lexicon uses (and the whole window); dial level k
    reads bit k."""
    maxlen = max(len(p) for p in embedder.corpus.values())
    for i in range(max(maxlen, WINDOW)):
        assert i % 4 == (i % 8) % 4 and i % 2 == (i % 4) % 2
        assert (dial_bit(i, 0), dial_bit(i, 1), dial_bit(i, 2)) == \
            tuple((i >> k) & 1 for k in range(3))
    print(f"\ntangency holds 0..{max(maxlen, WINDOW)-1}, zero slack; "
          f"bit-planes read coarse-to-fine")


def test_census_and_separation_probe_exact(census):
    """Probe 60 #1/#2: 9,451 colliding count-signatures carrying
    21,836 orderings; the compass separates all 16,520 pairs."""
    orders = sum(len({pr for _, pr in v}) for v in census.values())
    sep = tot = 0
    for v in census.values():
        prs = list({pr for _, pr in v})
        for i in range(len(prs)):
            for j in range(i + 1, len(prs)):
                tot += 1
                sep += int(fold(prs[i]) != fold(prs[j]))
    print(f"\ncensus: {len(census)} signatures, {orders} orderings; "
          f"separation {sep}/{tot}")
    assert len(census) == 9451
    assert orders == 21836
    assert (sep, tot) == (16520, 16520)


def test_invertibility_whole_lexicon(embedder):
    """Probe 60 #3 / 61 #3: decode(fold(w)) == pron(w), every lexicon
    word inside the window — 135,166/135,166."""
    ok = n = 0
    for w, p in embedder.corpus.items():
        if len(p) >= WINDOW:
            continue
        n += 1
        ok += int(decode(fold(tuple(p)), len(p)) == tuple(p))
    print(f"\ninvertibility: {ok}/{n}")
    assert (ok, n) == (135166, 135166)


def test_decode_matches_probe_literal(embedder):
    """The module's CRT table is the probe's literal range-scan done
    once — parity asserted on a 300-word sample."""
    def probe_decode(bag, n):
        slots = [None] * n
        for (ph, r8, r7), c in bag:
            i0 = next(i for i in range(56)
                      if i % P8 == r8 and i % P7 == r7)
            for k in range(c):
                pos = i0 + 56 * k
                if pos < n and slots[pos] is None:
                    slots[pos] = ph
        return tuple(slots)

    for w in list(embedder.corpus)[:300]:
        p = tuple(embedder.corpus[w])
        bag = fold(p)
        assert decode(bag, len(p)) == probe_decode(bag, len(p)) == p


def test_headroom_asserted_against_artifact(embedder):
    """Probe 61 #4: the longest pronunciation sits inside the mod-56
    window with its margin reported."""
    maxlen = max(len(p) for p in embedder.corpus.values())
    print(f"\nheadroom: longest pron {maxlen} < window {WINDOW}, "
          f"margin {WINDOW - maxlen}")
    assert maxlen == 28 and maxlen < WINDOW


def test_locality_zero_violations(embedder):
    """Probe 61 #5: equal full dyadic readings differ by exact
    multiples of 8 — no exceptions."""
    maxlen = max(len(p) for p in embedder.corpus.values())
    assert locality_violations(maxlen) == 0


def test_fold_equality_is_order_sensitive(census, embedder):
    """Law 3's equality contract, both directions: folds equal
    exactly when sequences are equal. Sampled across the census plus
    the pinned pair (past, taps) — same sounds, different order."""
    past = tuple(embedder.corpus["past"])
    taps = tuple(embedder.corpus["taps"])
    assert Counter(past) == Counter(taps) and past != taps
    assert fold(past) != fold(taps)
    checked = 0
    for v in list(census.values())[:500]:
        prs = [pr for _, pr in v]
        for i in range(len(prs)):
            for j in range(i + 1, len(prs)):
                assert (fold(prs[i]) == fold(prs[j])) == \
                    (prs[i] == prs[j])
                checked += 1
    assert checked > 500


def test_homoshape_healing_beside_the_scar(embedder):
    """T-4: the colliding-base families — the class behind Part X's
    0.9903 fold canary — re-measured WITH the compass. The scar and
    its healing, printed together; the cone keeps its counts."""
    bases = {b for b, _, _, _ in mine_pairs(embedder.corpus)}
    groups = defaultdict(list)
    for b in bases:
        groups[shape_seq(embedder.corpus[b])].append(b)
    colliding = {k: sorted(v) for k, v in groups.items()
                 if len({tuple(embedder.corpus[b]) for b in v}) >= 2}

    sims, distinct, tot = [], 0, 0
    for fam in colliding.values():
        for i in range(len(fam)):
            for j in range(i + 1, len(fam)):
                a = tuple(embedder.corpus[fam[i]])
                b = tuple(embedder.corpus[fam[j]])
                if a == b:
                    continue          # true homophones: not order's job
                va = embedder.shape_vec(a)
                vb = embedder.shape_vec(b)
                sims.append(float(
                    va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb))))
                tot += 1
                distinct += int(fold(a) != fold(b))
    sims = np.array(sims)
    print(f"\nthe scar: {tot} colliding-base pairs, shape cosine "
          f"mean {sims.mean():.4f} max {sims.max():.4f} (Part X's "
          f"chapter-fold canary recorded 0.9903); the healing: "
          f"compass-distinct {distinct}/{tot} = "
          f"{distinct/tot*100:.1f}%")
    assert sims.mean() >= 0.90        # the scar is still a scar
    assert distinct == tot            # and the compass heals it: 100%
