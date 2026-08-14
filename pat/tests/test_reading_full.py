"""X-4: the full-vocabulary reading battery (probe 44) — adoption
needs a reason, never silence, never forever.

The dict-exact engine reads the ENTIRE qualifying vocabulary (37,109
words, pinned) in six epochs under deferral policy P2:

  `read:no-such-stem`            no lexicon word carries any putative
                                 stem's pron — the derived reading is
                                 impossible; adopt at once;
  `read: stem <w> exists unread` the stem exists but three epochs of
                                 revisits never met it; adopt, naming
                                 the stem (market's is 'markka' — the
                                 Finnish currency, unread forever);
  `unlocked by <stem>`           the stem arrived; the ledger says who.

P0 (defer-forever, Part VII's shipped policy) is run beside it as the
recorded catastrophe: ~14,268 words stranded — the row the policy
retires.

THE ATOMS-BEFORE-STEMS CLASS, counted as truthful: 4-phoneme derived
words sit under looks_derived's len >= 5 dial, become early atoms
('called', 'told', 'lots'...), truthfully answer BARE-of-themselves
until their stems arrive, and the prune pass then retires them into
certified aliases (272 prunes at full scale, 139 of them 4-phoneme).
A BARE-OK answer about a word the creature legitimately knows is a
truth, not a confabulation — asserted as such here, per the spec's
ruling. (The spec quotes probe 44's SEVEN for this class; the
delivered probe44.py has no prune pass, so that number is
unreproducible from the delivered code — our measured class is listed
above and flagged in HANDOFF Part IX.)
"""
import json
from pathlib import Path

import pytest

from pat import ReadingSession

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def full_stream():
    return json.loads((FIX / "reading_stream_full.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def seeds():
    return json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))["seeds"]


def run_policy(organs, full_stream, seeds, policy):
    stream = full_stream["stream"]
    session = ReadingSession(organs, seed_bases=seeds, policy=policy)
    aligned = None

    def probe(s):
        nonlocal aligned
        if aligned is None:
            aligned = [(b, sf, w) for b, d in s.byb.items()
                       if b in s.known for sf, w in d.items()][:400]
        ok = real = homo = atoms = 0
        for b, sf, w in aligned:
            mode, gb, gs, verdict = s.analyze_word(w)
            if mode == "BOUND" and gb == b and gs == sf \
                    and verdict == "OK":
                ok += 1
            elif mode == "BARE" and gb == w and verdict == "OK":
                atoms += 1
            elif mode != "REFUSE":
                if verdict == "HOMOPHONE":
                    homo += 1
                else:
                    real += 1
        return {"coverage": ok / len(aligned) * 100,
                "real_confabs": real, "atoms_before_stems": atoms,
                "homos": homo}

    report = session.read(stream, epochs=6,
                          epoch_size=max(1, len(stream) // 6),
                          counts=full_stream["counts"],
                          epoch_probe=probe)
    return session, report


@pytest.fixture(scope="module")
def p2(organs, full_stream, seeds):
    return run_policy(organs, full_stream, seeds, policy=2)


def test_growth_and_deferral(p2, organs, full_stream, seeds):
    session, report = p2
    snaps = report["snapshots"]
    print("\nepoch  known  deferred  unlocked  no-such  stale  pruned  "
          "cov%  REAL  atoms")
    for s in snaps:
        a = s["adoptions"]
        print(f"  {s['epoch']}   {s['known']:6d}   {s['deferred']:6d}   "
              f"{a['unlocked']:6d}   {a['no-such-stem']:6d} "
              f"{a['stale-adopt']:6d}  {s['pruned']:5d}  "
              f"{s['coverage']:5.1f}  {s['real_confabs']:4d}  "
              f"{s['atoms_before_stems']:4d}")
    final = snaps[-1]
    assert final["known"] >= 22_000, \
        f"final vocabulary {final['known']} < 22,000"
    assert final["deferred"] <= 2_000, \
        f"{final['deferred']} words still deferred — the policy failed"
    # law 1 across the whole run, with the atoms class ruled truthful
    for s in snaps:
        assert s["real_confabs"] == 0, \
            f"epoch {s['epoch']}: {s['real_confabs']} REAL confabs " \
            f"— LAW BROKEN"

    # the P0 catastrophe, recorded beside it
    p0_session, p0_report = run_policy(organs, full_stream, seeds,
                                       policy=0)
    p0_final = p0_report["snapshots"][-1]
    print(f"\nP0 defer-forever (the retired catastrophe): "
          f"known {p0_final['known']}, {p0_final['deferred']} words "
          f"stranded in the deferral queue")
    assert p0_final["deferred"] >= 10_000, \
        "the P0 catastrophe shrank — re-measure the policy's value"
    assert final["deferred"] < p0_final["deferred"] / 5


def test_trio_canary_by_provenance(p2):
    """government/nothing = no-such-stem; market = stem-exists-unread.
    Adoption reasons, asserted on the ledger itself (law 3)."""
    session, _ = p2
    prov = {w: session.known.get(w) for w in
            ("government", "nothing", "market")}
    print(f"\ntrio: {prov}")
    assert prov["government"] == "read:no-such-stem"
    assert prov["nothing"] == "read:no-such-stem"
    assert prov["market"].startswith("read: stem ") \
        and prov["market"].endswith(" exists unread")


def test_adoption_ledger_complete(p2):
    """Every non-birth resolution carries one of the three reasons —
    never silence (law 3)."""
    session, _ = p2
    a = session.adoptions
    print(f"\nadoptions: {a}; prunes {len(session.retired)}")
    assert a["no-such-stem"] > 0 and a["stale-adopt"] > 0 \
        and a["unlocked"] > 0
    for w, p in session.known.items():
        assert p == "birth" or p.startswith("read") \
            or p.startswith("lesson"), f"unledgered provenance: {w}={p}"
    for w in session.deferred:
        assert w not in session.known and w not in session.retired


def test_atoms_before_stems_are_pruned_truths(p2, organs):
    """The len >= 5 dial's cost, retired by the metabolism: 4-phoneme
    early atoms end as certified aliases, not lies."""
    session, _ = p2
    atoms4 = [w for w in session.retired
              if len(organs.embedder.corpus[w]) == 4]
    print(f"\n4-phoneme pruned atoms: {len(atoms4)} "
          f"(sample {atoms4[:8]})")
    assert len(atoms4) >= 50
    for w in atoms4[:50]:
        entry = session.retired[w]
        assert list(organs.embedder.corpus[w]) == \
            list(organs.embedder.corpus[entry["surface"]])