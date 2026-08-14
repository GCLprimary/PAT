"""O-3: the discovery batteries (probe 55) — Pat's proposal, gated.

The organ's TASTE is the battery's spine: -ment/-less/-est promoted by
name; -ist certified 27 pairs and REFUSED promotion at the bar (its
pairs retire as truths — capitalist IS capital+ist — but the suffix
earns no table row); the -et fragments likewise (basket = bask+et is
form-true, the sound-and-spelling claim the alias makes, exactly the
side=sigh+ed class); the bound-stem classes CANNOT certify (-ous
strips to nothing — famous has no free *fam*; -ility's yield never
reaches candidacy) and are pinned as the BOUND-STEM CANARY.

PAT'S OWN ACCEPTANCE INEQUALITY (PROPOSAL.md) is evaluated alongside
the spec gates, per the spec: both asserted, conflicts FLAGGED, never
reconciled. Two clauses conflict with measured reality and the
conflicts are pinned below — Pat over-asked ((a) demanded >= 200 pairs
where the best class certifies 133; (c) forecast >= 15% conversion
where the concatenative slice of its class is ~4.4%) — the mutating/
bound majority was invisible to Pat when it wrote the bar, and THAT
gap is the stem-allomorphy lane's founding census.
"""
import json
from collections import Counter
from pathlib import Path

import pytest

from pat import (ReadingSession, discover, register, retire_atoms,
                   write_artifact)
from mirror import PhonGate

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def run(organs):
    full = json.loads((FIX / "reading_stream_full.json").read_text(
        encoding="utf-8"))
    seeds = json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))["seeds"]
    stream = full["stream"]
    session = ReadingSession(organs, seed_bases=seeds, policy=2)
    session.read(stream, epochs=6,
                 epoch_size=max(1, len(stream) // 6),
                 counts=full["counts"])
    result, retired_pairs = discover(session, stream)
    return session, stream, result, retired_pairs, seeds, full


def test_gates_and_artifact_pin(run, tmp_path):
    session, stream, result, retired_pairs, _, _ = run
    promoted = {d["suffix"]: d for d in result["discovered"]}
    total = sum(len(p) for _, _, p, _ in retired_pairs)
    print(f"\nclass {result['no_such_stem_size']}; promoted "
          f"{list(promoted)}; certified total {total}; "
          f"confabs {result['confabs']}")
    assert len(promoted) >= 3
    assert promoted["ment"]["certified"] >= 130
    assert promoted["less"]["certified"] >= 75
    assert promoted["est"]["certified"] >= 55
    assert total >= 300
    assert result["confabs"] == 0, "THE DOUBLE-LOCK LEAKED"
    # the artifact reproduces its pin
    pinned = json.loads((FIX / "checksums.json").read_text(
        encoding="utf-8"))["discovered_suffixes.json"]
    sha = write_artifact(result, retired_pairs,
                         tmp_path / "artifact.json")
    assert sha == pinned, "discovery drifted from its pinned artifact"


def test_the_organs_taste_canaries(run, organs):
    session, stream, result, retired_pairs, _, _ = run
    census = {tuple(c["tail"]): c for c in result["census"]}
    ist = census[("IH", "s", "t")]
    assert ist["kind"] == "certified-below-promotion-bar"
    assert ist["count"] < 40, f"-ist reached the bar ({ist['count']})"
    assert ("AH", "t") in census and ("IH", "t") in census
    promoted_names = {d["suffix"] for d in result["discovered"]}
    assert "ist" not in promoted_names and "et" not in promoted_names
    # the bound-stem canary
    corpus = organs.embedder.corpus
    no_such = [w for w in stream
               if session._looks_derived(w)
               and not session._stem_exists(tuple(corpus[w]))]

    def raw(tail):
        k = len(tail)
        hit = tot = 0
        for w in no_such:
            p = tuple(corpus[w])
            if len(p) - k < 3 or p[-k:] != tail:
                continue
            tot += 1
            hit += int(p[:-k] in session._pron_index)
        return hit, tot

    ous_h, ous_n = raw(("AH", "s"))
    il_h, il_n = raw(("IH", "l", "AH", "t", "IY"))
    print(f"\nbound-stem canary: -ous {ous_h}/{ous_n}; "
          f"-ility {il_h}/{il_n} (yield below the {50} bar)")
    assert ous_h == 0, \
        "-ous certified a free stem — famous grew a *fam*? what changed"
    assert il_n < 50, "-ility reached candidacy — what changed"
    assert not any(d["suffix"] in ("ous", "ility")
                   for d in result["discovered"])


def test_pats_inequality_alongside(run):
    """PROPOSAL.md's own bar, clause by clause. (b) HOLDS; (a) and (c)
    CONFLICT with measured reality — pinned as flags, not reconciled.
    If reality ever satisfies Pat's bars, these pins fail loudly and
    the flag retires with a decision, not by drift."""
    session, stream, result, retired_pairs, _, _ = run
    best = max(d["certified"] for d in result["discovered"])
    total = sum(len(p) for _, _, p, _ in retired_pairs)
    conversion = total / result["no_such_stem_size"]
    # (b): audit clears the Part IX floor; SEAM cosine is 1.0 by
    # exactness (certified pairs are exact concatenations)
    for d in result["discovered"]:
        assert d["rate"] * 100 >= 30.0
    # (a): mined pair count >= 200 — CONFLICT, pinned
    print(f"\nPat's (a) >= 200 pairs: best class certifies {best} "
          f"-> CONFLICT (flagged)")
    assert best < 200, \
        "Pat's clause (a) now HOLDS — retire the flag deliberately"
    # (c): >= 15% conversion — CONFLICT, pinned
    print(f"Pat's (c) >= 15% conversion: measured "
          f"{conversion * 100:.1f}% -> CONFLICT (flagged; the "
          f"mutating/bound majority was invisible to Pat)")
    assert conversion < 0.15, \
        "Pat's clause (c) now HOLDS — retire the flag deliberately"


def test_registration_retirement_and_reread(run, organs):
    session, stream, result, retired_pairs, seeds, full = run
    corpus = organs.embedder.corpus
    gate2 = PhonGate.from_transform(organs.transform)
    register(gate2, result, retired_pairs, corpus)
    n = retire_atoms(session, retired_pairs)
    totals = session.provenance_totals()
    print(f"\nretired {n}; provenance {totals}")
    assert n >= 300
    assert totals.get("discovered", 0) == n     # the FIFTH class, live
    assert totals.get("pruned", 0) > 0          # the fourth kept its own
    # every retired word analyzes as stem + suffix through the
    # standard gate (exclude=self, the prune pathway's own protocol)
    sess2 = ReadingSession(organs, seed_bases=seeds, policy=2,
                           gate=gate2)
    ok = checked = 0
    for sfx, tail, pairs, promoted in retired_pairs:
        for w, sw in pairs:
            sess2.teach(sw, "birth")
            mode, gb, gs, verdict = sess2.analyze_word(w, exclude=w)
            checked += 1
            ok += int(mode == "BOUND" and gb == sw and gs == sfx
                      and verdict == "OK")
    print(f"re-read: {ok}/{checked}")
    assert ok == checked, f"{checked - ok} retired words lost their way"
    # the wrinkle, kept: industrialist was a BIRTH seed and is also
    # industrial+ist — it retires with both receipts
    assert "industrialist" in session.retired
    assert session.retired["industrialist"]["provenance"].startswith(
        "discovered:ist")
    # MAXR asserted against the artifact, never hard-coded
    maxr = max(len(r) for rems in gate2.attested.values() for r in rems)
    assert maxr == 4                             # -ment is 4
    sess3 = ReadingSession(organs, seed_bases=seeds, policy=2,
                           gate=gate2)
    assert sess3.max_rem == maxr


def test_reading_delta_and_no_harm(run, organs):
    """The widened oracle shrinks future no-such-stem adoptions
    (reported, both vintages); the SHIPPED gate stays six-suffix —
    registration is opt-in, and every pinned battery keeps its
    vintage."""
    session, stream, result, retired_pairs, seeds, full = run
    gate2 = PhonGate.from_transform(organs.transform)
    register(gate2, result, retired_pairs, organs.embedder.corpus)
    widened = ReadingSession(organs, seed_bases=seeds, policy=2,
                             gate=gate2)
    widened.read(stream, epochs=6,
                 epoch_size=max(1, len(stream) // 6),
                 counts=full["counts"])
    old = session.adoptions["no-such-stem"]
    new = widened.adoptions["no-such-stem"]
    print(f"\nREADING DELTA: no-such-stem adoptions {old} (shipped) "
          f"-> {new} (widened); delta {old - new}")
    assert new < old
    shipped = PhonGate.from_transform(organs.transform)
    assert len(shipped.attested) == 6, \
        "the SHIPPED gate widened — registration leaked out of opt-in"