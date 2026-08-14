"""W-3: the reading batteries (probes 40-41, pinned stream fixture).

Growth: the creature ends epoch 6 knowing >= 1,500 bases with aligned
derived-form coverage >= 60%, monotone nondecreasing. Honesty: REAL
confabulations are ZERO at every epoch (hard), and every homophone
verdict is same-pron-verified IN THIS TEST (the ledger's claim is
re-checked against the corpus, entry by entry). Metabolism: >= 10
deferred words unlock, the prune ledger is nonempty and 100%
homophone-certified, and the place canary stands guard (place != plays
never prunes — law 3). Self-census: nonempty, entries same-shape
verified; the census curve is recorded data, not a gate.
"""
import json
from pathlib import Path

import pytest

from pat import ReadingSession
from mirror.diagnostics import shape_seq

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def stream_fixture():
    return json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def run(organs, stream_fixture):
    """One 6-epoch read of the pinned stream; every test reads this.
    policy=0 pins Part VII's shipped defer-forever protocol — the
    fixture and every gate below were measured under it; the P2 policy
    (the default law since X-4) has its own battery on the full-
    vocabulary stream (test_reading_full)."""
    session = ReadingSession(organs, seed_bases=stream_fixture["seeds"],
                             policy=0)
    aligned = stream_fixture["aligned_test"]

    def coverage(s):
        ok = real = homo = atoms = 0
        for b, sfx, w in aligned:
            mode, gb, gs, verdict = s.analyze_word(w)
            if mode == "BOUND" and gb == b and gs == sfx \
                    and verdict == "OK":
                ok += 1
            elif mode == "BARE" and gb == w and verdict == "OK":
                atoms += 1        # atoms-before-stems: a truth (X-4)
            elif mode != "REFUSE":
                if verdict == "HOMOPHONE":
                    homo += 1
                else:
                    real += 1
        return {"coverage": ok / len(aligned) * 100,
                "real_confabs": real, "homophones_in_test": homo,
                "atoms_before_stems": atoms}

    report = session.read(stream_fixture["stream"], epochs=6,
                          epoch_size=1000,
                          counts=stream_fixture["counts"],
                          epoch_probe=coverage)
    return session, report


def test_growth(run):
    session, report = run
    snaps = report["snapshots"]
    print("\nepoch  known  deferred  unlocked  pruned  census  "
          "coverage%  REALconfab  homoph")
    for s in snaps:
        print(f"  {s['epoch']}    {s['known']:5d}   "
              f"{s['deferred']:5d}    {s['unlocked']:5d}    "
              f"{s['pruned']:4d}   {s['census']:4d}    "
              f"{s['coverage']:5.1f}      {s['real_confabs']:3d}       "
              f"{s['homophones_in_test']:3d}")
    assert snaps[-1]["known"] >= 1500, \
        f"final vocabulary {snaps[-1]['known']} < 1,500"
    assert snaps[-1]["coverage"] >= 60.0, \
        f"final coverage {snaps[-1]['coverage']:.1f}% < 60%"
    for a, b in zip(snaps, snaps[1:]):
        assert b["coverage"] >= a["coverage"], \
            f"coverage fell: epoch {a['epoch']} {a['coverage']:.1f} -> " \
            f"epoch {b['epoch']} {b['coverage']:.1f}"


def test_honesty_invariant(run, organs):
    """REAL confabs == 0 at EVERY epoch; every ledgered homophone
    verdict is verified same-pron HERE, not taken on faith."""
    session, report = run
    for s in report["snapshots"]:
        assert s["real_confabs"] == 0, \
            f"epoch {s['epoch']}: {s['real_confabs']} REAL confabs " \
            f"— LAW BROKEN"
    corpus = organs.embedder.corpus
    checked = 0
    for h in session.homophones:
        if h["mode"] == "BOUND":
            base_pron = list(corpus[h["base"]])
            obs = list(corpus[h["word"]])
            rem = obs[len(base_pron):]
            assert obs[:len(base_pron)] == base_pron
            if h["surface"]:
                assert list(corpus[h["surface"]]) == obs, \
                    f"homophone ledger lied: {h}"
        else:
            assert list(corpus[h["word"]]) == list(corpus[h["base"]]), \
                f"homophone ledger lied: {h}"
        checked += 1
    print(f"\n{checked} homophone verdicts, all same-pron verified")


def test_metabolism(run, organs):
    """Unlocks >= 10; prunes nonempty and 100% homophone-certified
    (pron identity re-verified here); place stands guard."""
    session, report = run
    assert len(session.unlocked) >= 10, \
        f"only {len(session.unlocked)} unlocks"
    assert session.retired, "the prune ledger is empty"
    corpus = organs.embedder.corpus
    for word, entry in session.retired.items():
        assert list(corpus[word]) == list(corpus[entry["surface"]]), \
            f"UNCERTIFIED PRUNE: {word} vs {entry}"
        assert entry["provenance"].startswith("derivable: ")
    print(f"\n{len(session.unlocked)} unlocked "
          f"(sample: {session.unlocked[:2]}); "
          f"{len(session.retired)} pruned, all certified "
          f"(sample: {list(session.retired.items())[:2]})")
    # the place canary: read-taught, derivable-looking to a suffix-wide
    # set, and NEVER pruned (place != plays; pair-exact refuses first)
    assert "place" in stream_words(session), \
        "place left the pinned stream — regenerate nothing, investigate"
    assert "place" not in session.retired, \
        "PLACE WAS PRUNED — the set-vs-table hole reopened (law 3)"
    if "place" in session.known:
        assert session.known["place"].startswith("read")


def stream_words(session):
    return set(session.known) | set(session.retired) | \
        set(session.deferred)


def test_self_census(run, organs):
    """The creature's own ambiguity ledger: nonempty, every entry
    verified same-shape; the per-epoch curve is data, recorded."""
    session, report = run
    assert session.census, "self-census is empty"
    for entry in session.census:
        a = shape_seq(organs.embedder.corpus[entry["word"]])
        b = shape_seq(organs.embedder.corpus[entry["collides_with"]])
        assert a == b, f"census entry not same-shape: {entry}"
    curve = [s["census"] for s in report["snapshots"]]
    print(f"\nself-census: {len(session.census)} entries; "
          f"curve by epoch {curve}; sample {session.census[:3]}")


def test_provenance_classes(run):
    """birth / read in the living ledger; pruned aliases answer
    truthfully through knows()."""
    session, report = run
    totals = report["provenance_totals"]
    print(f"\nprovenance totals: {totals}")
    assert totals.get("birth", 0) == 15
    assert totals.get("read", 0) >= 1400
    word, entry = next(iter(session.retired.items()))
    yes, prov = session.knows(word)
    assert yes and prov.startswith("derivable: ")
    yes, prov = session.knows("qqqq-not-a-word")
    assert not yes
