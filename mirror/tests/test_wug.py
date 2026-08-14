"""E-2 (probe 52): the wug battery — the induced table meets stems
that do not exist.

Law 2, twice, as canaries: (1) the corrected textbook gold carries the
affricates in the sibilant set — the table taught us that (and taught
us AGAIN at build when a transcription slip graded it wrong: the
armchair lost both rounds); (2) kn-/vl-/ts- onsets are ATTESTED
(Knupp/Knut, Vlad/Vlach, Tsang/Tsai) so the attestation gate refuses
the textbook's "illegal" label for them — only the truly-unattested
21 refuse, 100%.
"""
import pytest

from mirror import AllomorphTable
from mirror.wug import (monosyllable_parts, novel_stems, textbook_gold,
                        wug_inflect)

UNATTESTED_21 = ("bn", "dl", "dn", "fp", "gt", "lr", "pf", "tl", "vp",
                 "wl", "bd", "gp", "kt", "lm", "ns", "pk", "bz", "dg",
                 "fk", "lz", "nk")
ATTESTED_SURPRISES = {"kn": ("knupp", "knut"), "vl": ("vlad", "vlach"),
                      "ts": ("tsang", "tsai")}


@pytest.fixture(scope="module")
def table(embedder):
    return AllomorphTable().fit(embedder.corpus)


@pytest.fixture(scope="module")
def stems(embedder):
    return novel_stems(embedder.corpus, n=300, seed=50)


def test_wug_agreement_both_suffixes(table, stems):
    """On answered stems the induced table agrees with the CORRECTED
    textbook rule >= 99% for both suffixes; unseen final signatures
    refuse and the refusals are counted, never patched."""
    print()
    for sfx in ("ed", "s"):
        agree = wrong = refused = 0
        disputes = []
        for stem in stems:
            cls = wug_inflect(table, stem, sfx)
            if cls is None:
                refused += 1
                continue
            gold = textbook_gold(stem[-1], sfx)
            if cls == gold:
                agree += 1
            else:
                wrong += 1
                disputes.append((stem[-1], cls, gold))
        n_ans = agree + wrong
        print(f"  -{sfx}: {agree}/{n_ans} answered agree, "
              f"{refused} refused{'  disputes: ' + str(disputes[:4]) if disputes else ''}")
        assert agree / n_ans >= 0.99, \
            f"-{sfx}: table vs corrected textbook {agree}/{n_ans} — " \
            f"if the table is right AGAIN, correct the gold, not the " \
            f"table (law 2)"
        assert refused > 0, \
            f"-{sfx}: zero refusals — selectivity went silent"


def test_illegal_onsets_refuse_attested_ones_do_not(embedder):
    """Law 2's second canary: the 21 truly-unattested onsets refuse
    100%; the textbook's other 'illegal' onsets — kn, vl, ts — are
    attested (Knupp/Knut, Vlad/Vlach, Tsang/Tsai) and therefore
    LEGAL. Legality is attestation, not the armchair."""
    onsets, _, _, _ = monosyllable_parts(embedder.corpus)
    refused = [c for c in UNATTESTED_21 if tuple(c) not in onsets]
    print(f"\nunattested onsets refused: {len(refused)}/"
          f"{len(UNATTESTED_21)}")
    assert len(refused) == len(UNATTESTED_21) == 21, \
        f"an 'illegal' onset became attested: " \
        f"{set(UNATTESTED_21) - set(refused)} — move it to the " \
        f"surprises list and name its exemplar (law 2)"
    for cluster, exemplars in ATTESTED_SURPRISES.items():
        assert tuple(cluster) in onsets, \
            f"{cluster}- lost its attestation ({exemplars})"
        attested_words = set(onsets[tuple(cluster)])
        assert attested_words & set(exemplars), \
            f"{cluster}-'s exemplars moved: {sorted(attested_words)[:4]}"
