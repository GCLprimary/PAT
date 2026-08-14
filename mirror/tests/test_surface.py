"""G-2 acceptance (probes 23, 26): the induced allomorph table.

No hand-written rule anywhere: the table is learned from counts and must
rediscover voicing assimilation and epenthesis. >= 98.5% held-out for -s
and -ed; the six showpieces as literal assertions; readable export with
>= 15 signatures.
"""
import pytest

from mirror import AllomorphTable


@pytest.fixture(scope="module")
def table(embedder):
    return AllomorphTable().fit(embedder.corpus)


def test_induced_accuracy(table):
    print(f"\n-s {table.accuracy['s']:.1%} (n={table.n_test['s']})   "
          f"-ed {table.accuracy['ed']:.1%} (n={table.n_test['ed']})")
    assert table.accuracy["s"] >= 0.985
    assert table.accuracy["ed"] >= 0.985


def test_showpieces(embedder, table):
    """Voicing assimilation and epenthesis, rediscovered from counts."""
    expected = {("dog", "s"): "z", ("cat", "s"): "s",
                ("horse", "s"): "epen_z", ("play", "ed"): "d",
                ("help", "ed"): "t", ("want", "ed"): "epen_d"}
    for (base, sfx), cls in expected.items():
        got = table.choose(embedder.corpus[base], sfx)
        assert got == cls, f"{base}+{sfx}: induced {got}, phonology says {cls}"
    # and the surface forms realize them
    assert table.surface(embedder.corpus["horse"], "s")[-2:] == ["IH", "z"]
    assert table.surface(embedder.corpus["want"], "ed")[-2:] == ["IH", "d"]


def test_table_exports_readably(table):
    text = table.export()
    n_signatures = len(table.rules["s"]) + len(table.rules["ed"])
    print(f"\n{text}")
    assert n_signatures >= 15
    assert "epen" in text and "->" in text
