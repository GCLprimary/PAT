"""XVI-b: the front-door batteries — the bounced gate's fixes, pinned.

Part XVI shipped a door wired to a newborn: the launcher parsed
`--store` as a store PATH (the top-level `--store/` junk directory was
its fingerprint), booted an empty ~/.pat, and greeted with the v0 verb
list. The reviewer's smoke test caught Pat forgetting who he is — the
project's first bounced gate. These batteries pin the fixes:

F1a  the reading ledger survives death (to_state/from_state parity);
F1b  the shipped canonical store boots the lived Pat — the side
     biography, the lesson, thousands of bases, the oracle receipt;
F2   the store flag parses as a flag, and first boot seeds ~/.pat
     from the canonical store.
"""
import hashlib
import json
from pathlib import Path

import pytest

from pat import Agent
from pat.cli import CANONICAL_STORE, parse_args, resolve_store
from pat.reading import ReadingSession

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"
STORE = Path(__file__).resolve().parent.parent / "data" / "store"
SIDE_BIO = "derivable: sigh+ed; read-taught epoch 1, pruned epoch 5"


@pytest.fixture(scope="module")
def stream_fx():
    return json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))


# ── F1a: the session survives death ──────────────────────────────────
def test_reading_state_roundtrip(organs, stream_fx):
    """Every ledger, every provenance string, every analysis — equal
    across a JSON death and rebirth."""
    s = ReadingSession(organs, seed_bases=stream_fx["seeds"])
    s.read(stream_fx["stream"][:1200], epochs=2, epoch_size=600,
           counts=stream_fx["counts"])
    wire = json.loads(json.dumps(s.to_state()))   # a real serialization
    r = ReadingSession.from_state(organs, wire)
    assert r.known == s.known
    assert r.retired == s.retired
    assert r.deferred == s.deferred
    assert r.adoptions == s.adoptions
    assert r.epoch == s.epoch
    assert r._shape_index == s._shape_index
    assert r.provenance_totals() == s.provenance_totals()
    sample = (list(s.known)[:40] + list(s.retired)[:10]
              + ["government", "brillig"])
    for w in sample:
        assert r.knows(w) == s.knows(w), w
        if w in organs.embedder.corpus:
            assert r.analyze_word(w) == s.analyze_word(w), w


# ── F1b: the canonical store is pinned and boots the lived Pat ───────
def test_canonical_store_pinned():
    """Law 2 structural: the shipped store matches its manifest —
    regeneration is an event, not a refresh."""
    manifest = json.loads((FIX / "canonical_store.json").read_text(
        encoding="utf-8"))
    assert set(manifest) == {"pages.json", "provenance.json",
                             "reading.json", "store.json"}
    for name, expected in manifest.items():
        actual = hashlib.sha256((STORE / name).read_bytes()).hexdigest()
        assert actual == expected, f"canonical store file {name} changed"


@pytest.fixture(scope="module")
def canonical():
    return Agent(str(STORE))


def test_canonical_boot_is_the_lived_pat(canonical):
    """The smoke lines that bounced Part XVI, as a battery: a boot from
    the shipped store answers with the biography, not amnesia."""
    a = canonical
    assert a.reading is not None, "reading.json did not restore"
    assert a.bases_total() >= 3000
    yes, prov = a.reading.knows("side")
    assert yes and prov == SIDE_BIO
    yes, prov = a.reading.knows("men")
    assert yes and prov == "lesson:irregular_plurals"
    yes, prov = a.reading.knows("that")
    assert yes and prov == "read: attested 54244"
    assert a.respond("know side").lines()[0] == \
        f"yes, I know 'side' ({SIDE_BIO})"
    line = a.respond("verify government = govern+ment").lines()[0]
    assert line.startswith("REFUSE — pron('government') does not begin")
    assert a.respond("analyze brillig").lines()[0] == \
        "refuse: 'brillig' is not a form I can read"


def test_canonical_pages_restudy_portably(canonical):
    """The pages ledger re-studies by file name against mirror's
    DATA_DIR when its recorded absolute path is foreign — a store built
    on one machine schools the same Pat on another."""
    a = canonical
    assert a.reading.lawbook is not None, "the page did not re-study"
    num, prov = a.reading.number_of("men")
    assert num == "pl" and prov.startswith("lesson:")


# ── F2: the store flag is a flag ─────────────────────────────────────
def test_store_flag_parses_as_flag(tmp_path):
    """`pat --store X` must never create a directory named '--store'
    (the Part XVI junk-directory bug)."""
    p = str(tmp_path / "s")
    assert parse_args(["--store", p]).store == p
    assert parse_args([p]).store_pos == p
    both = parse_args([p, "--store", str(tmp_path / "flag")])
    store, seeded = resolve_store(both, home=tmp_path)
    assert store == tmp_path / "flag" and not seeded
    store, seeded = resolve_store(parse_args(["--store", p]),
                                  home=tmp_path)
    assert str(store) == p and not seeded
    assert "--store" not in (store.name, store.parent.name)


def test_first_boot_seeds_home_from_canonical(tmp_path):
    """No explicit store, no ~/.pat: the canonical store is copied in —
    then never again."""
    assert (CANONICAL_STORE / "store.json").exists()
    store, seeded = resolve_store(parse_args([]), home=tmp_path)
    assert store == tmp_path / ".pat" and seeded
    assert {f.name for f in store.iterdir()} >= \
        {"store.json", "provenance.json", "pages.json", "reading.json"}
    again, seeded = resolve_store(parse_args([]), home=tmp_path)
    assert again == store and not seeded
