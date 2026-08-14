"""Tests for the running-text loader (elfix/running_text.py): utterance loading,
provenance tagging (attested/inferred/oov), frequency corroboration, and the
no-compounding / attested-precedence guarantees carried through from the store."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.running_text import load_utterances, grow_store, tag_utterances


def test_load_utterances_splits_lines_into_words(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("the cat sat\nit ran\n", encoding="utf-8")
    assert load_utterances(p) == [["the", "cat", "sat"], ["it", "ran"]]


def test_tagging_attested_inferred_oov():
    cmu = {"cat": ["k", "AE", "t"], "the": ["DH", "AH"]}
    store = grow_store([["cats", "cats"]], cmu)          # cats <- cat+s
    tagged, stats = tag_utterances([["the", "cat", "cats", "qqq"]], cmu, store)
    assert [t.tag for t in tagged[0]] == ["attested", "attested", "inferred", "oov"]
    assert stats == {"attested": 2, "inferred": 1, "oov": 1}
    assert tagged[0][2].phonemes == ["k", "AE", "t", "s"]   # the composed pron
    assert tagged[0][3].phonemes is None                    # oov has none


def test_frequency_corroboration_confirms_recurring_oov():
    cmu = {"cat": ["k", "AE", "t"]}
    store = grow_store([["cats"], ["cats", "cats"]], cmu)   # cats x3 -> FREQ_CONFIRM
    assert store.lookup("cats")[1] == "inferred:confirmed"
    # a one-off decomposable OOV stays malleable
    store2 = grow_store([["cats"]], cmu)
    assert store2.lookup("cats")[1] == "inferred:malleable"


def test_grow_store_no_compounding_and_attested_untouched():
    cmu = {"run": ["r", "AH", "n"]}
    store = grow_store([["running"], ["runnings"]], cmu)
    assert store.lookup("running")[1].startswith("inferred")   # from attested 'run'
    assert store.evidence("runnings") is None                  # NOT from inferred 'running'
    assert store.lookup("run") == (["r", "AH", "n"], "attested")
