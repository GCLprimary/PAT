"""F-2 acceptance (probe 39): the phon gate — two mechanisms, measured.

A: imposter kill — on the pinned attack set (homoshape pairs, only B1
   known, attacked with B2's derived form) the gated pipeline's false
   accepts are ZERO. Hard. This is the safety number now.
B: no-tax inequality — stem-scoped gating accepts >= the blunt
   whole-word gate AND >= 99% of pinned trues; the epenthesis subfamily
   (2+ phoneme remainders, the blunt gate's victims) is asserted
   separately.
C: disambiguation — with BOTH colliding bases known, shape ties at 1.0
   and stem-phon attributes the derived form to the right base.
D: arbitration — wrong-suffix proposals are rejected because the
   observed remainder is not an attested form of the proposed suffix.
"""
import json
from collections import defaultdict

import pytest

from mirror import PhonGate
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


@pytest.fixture(scope="module")
def sets():
    return json.loads((FIX / "phon_gate_sets.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def gate(transform):
    return PhonGate.from_transform(transform)


def test_attested_table_pinned(gate):
    """The arbitration table the gate builds is the pinned artifact —
    build-time construction may never drift from the fixture."""
    pinned = json.loads((FIX / "attested_allomorphs.json").read_text(
        encoding="utf-8"))
    built = {s: sorted(list(r) for r in rems)
             for s, rems in gate.attested.items()}
    assert built == pinned, "attested allomorph sets drifted from the pin"


def test_imposter_kill(embedder, transform, gate, sets):
    """A: shape accepts the homoshape attack (the Part V finding); the
    gate kills every single one. 0 is asserted, not banded."""
    shape_acc = gate_acc = 0
    for B1, B2, sfx, w2 in sets["attacks"]:
        obs = list(embedder.corpus[w2])
        sv = float(embedder.shape_vec(obs)
                   @ transform.bind(embedder.corpus[B1], sfx, "shape"))
        shape_ok = sv >= 0.98
        gated = shape_ok and gate.check_bound(
            obs, embedder.corpus[B1], sfx).ok
        shape_acc += int(shape_ok)
        gate_acc += int(gated)
    print(f"\nshape-only false accepts: {shape_acc}/{len(sets['attacks'])}"
          f"  gated: {gate_acc}/{len(sets['attacks'])}")
    assert shape_acc > 0, \
        "the attack set stopped attacking — shape space changed character"
    assert gate_acc == 0, \
        f"{gate_acc} gated false accepts — THE SAFETY NUMBER MOVED"


def test_no_tax_inequality(embedder, transform, gate, sets):
    """B: the stem-scoped gate must not pay for its safety with true
    accepts — >= the blunt whole-word gate AND >= 99% of pinned trues;
    the epenthesis subfamily asserted separately (the probe's 39/39)."""
    stem_ok = blunt_ok = n_ep = stem_ep = blunt_ep = 0
    trues = sets["trues"]
    for B1, sfx, w1 in trues:
        obs = list(embedder.corpus[w1])
        s_ok = gate.check_bound(obs, embedder.corpus[B1], sfx).ok
        b_ok = (gate.blunt_cos(obs, embedder.corpus[B1],
                               transform.modal_phon[sfx]) >= 0.85
                if sfx in transform.modal_phon else False)
        ep = len(obs) - len(embedder.corpus[B1]) >= 2
        stem_ok += int(s_ok)
        blunt_ok += int(b_ok)
        if ep:
            n_ep += 1
            stem_ep += int(s_ok)
            blunt_ep += int(b_ok)
    print(f"\nstem-scoped true accepts: {stem_ok}/{len(trues)} = "
          f"{stem_ok / len(trues):.1%}   blunt-gate: {blunt_ok}/"
          f"{len(trues)} = {blunt_ok / len(trues):.1%}")
    print(f"epenthesis family (n={n_ep}): stem {stem_ep}/{n_ep}  "
          f"blunt {blunt_ep}/{n_ep}")
    assert stem_ok >= blunt_ok, "the stem gate lost to the blunt gate"
    assert stem_ok / len(trues) >= 0.99, \
        f"true-accept tax appeared: {stem_ok}/{len(trues)}"
    assert stem_ep == n_ep, \
        f"the epenthesis subfamily paid the tax: {stem_ep}/{n_ep}"


def test_disambiguation(embedder, transform, gate, sets):
    """C: both bases known, shape tied at 1.0 — stem-phon attributes the
    derived form to its true base >= 95% (probe: 120/120)."""
    byb = defaultdict(dict)
    for base, sfx, w, _ in transform.pairs:
        byb[base][sfx] = w
    ok = tot = 0
    for B1, B2 in sets["disamb"]:
        for sfx, w2 in byb[B2].items():
            obs = embedder.corpus[w2]
            c1 = gate.stem_cos(obs, embedder.corpus[B1])
            c2 = gate.stem_cos(obs, embedder.corpus[B2])
            ok += int(c2 > c1)
            tot += 1
            break
    print(f"\ncorrect attribution: {ok}/{tot} = {ok / tot:.1%}")
    assert ok / tot >= 0.95, f"disambiguation {ok}/{tot} < 95%"


def test_wrong_suffix_arbitration(embedder, gate, sets):
    """D: a proposal wearing the wrong suffix is rejected because its
    remainder is not an attested form of that suffix (>= 98%)."""
    ok = 0
    wrong = sets["wrong_suffix"]
    for b, right, wrong_s, w in wrong:
        obs = embedder.corpus[w]
        res = gate.check_bound(list(obs), embedder.corpus[b], wrong_s)
        rejected = (not res.ok) and "attested" in res.reason
        ok += int(rejected)
    print(f"\nwrong-suffix proposals rejected: {ok}/{len(wrong)}")
    assert ok / len(wrong) >= 0.98, \
        f"arbitration rejected only {ok}/{len(wrong)}"


def test_refusal_reasons_distinguish_mechanisms(embedder, gate, sets):
    """The two mechanisms name themselves: a cross-stem attack refuses
    with 'stem mismatch'; a wrong-suffix proposal with an attested-form
    reason. One gate, two named vetoes."""
    B1, B2, sfx, w2 = sets["attacks"][0]
    res = gate.check_bound(list(embedder.corpus[w2]),
                           embedder.corpus[B1], sfx)
    assert not res.ok and res.reason == "stem mismatch"
    b, right, wrong_s, w = sets["wrong_suffix"][0]
    res = gate.check_bound(list(embedder.corpus[w]),
                           embedder.corpus[b], wrong_s)
    assert not res.ok and res.reason == \
        f"remainder not an attested -{wrong_s} form"


# ── W-1 (probes 40-41): the exactness refinement ─────────────────────
def test_canary_anagram_stem(embedder, gate):
    """melted-vs-metal must REFUSE: the stems are anagrams and the
    dormant cosine path scores them 0.78 >= theta_p — sequence equality
    is why exactness beats similarity (law 1)."""
    obs = list(embedder.corpus["melted"])
    metal = embedder.corpus["metal"]
    leak = gate.stem_cos(obs, metal)
    res = gate.check_bound(obs, metal, "ed")
    print(f"\nmelted vs metal+ed: stem-cosine {leak:.4f} "
          f"(>= {gate.theta} — the dormant path's blind spot); "
          f"exact gate: {'REFUSE' if not res.ok else 'ACCEPT'}")
    assert leak >= gate.theta, \
        "the anagram leak closed by itself — re-measure the window"
    assert not res.ok and res.reason == "stem mismatch"


def test_canary_place_unlicensed_allomorph(embedder, gate, transform):
    """place-as-play+s must REFUSE: play's -s remainder is z, never s.
    The suffix-wide attested set ADMITS this (the probe-41 hole); the
    pair-exact artifact refuses it."""
    obs = list(embedder.corpus["place"])
    play = embedder.corpus["play"]
    rem = tuple(obs[len(play):])
    suffix_wide = rem in {tuple(r[3]) for r in transform.pairs
                          if r[1] == "s"}
    res = gate.check_bound(obs, play, "s")
    print(f"\nplace as play+s: remainder {rem}; suffix-wide set admits "
          f"{suffix_wide}; refined gate: "
          f"{'REFUSE' if not res.ok else 'ACCEPT'}")
    assert suffix_wide, "the hole this canary guards has changed shape"
    assert not res.ok and res.reason.startswith("remainder not")


def test_canary_homophone_verdict(embedder, gate):
    """find-as-fine+ed must STAND with the HOMOPHONE verdict: the
    pronunciations are identical (genuine sound identity), the surface
    identity differs — an honest verdict class, never a confab."""
    obs = list(embedder.corpus["find"])
    fine = embedder.corpus["fine"]
    res = gate.check_bound(obs, fine, "ed")
    assert res.ok, "find no longer analyzes as fine+ed"
    assert list(embedder.corpus["fined"]) == obs, \
        "find/fined stopped being homophones — corpus changed character"
    assert gate.verdict("find", "BOUND", "fine", "ed") == "HOMOPHONE"
    # nuance worth pinning: (fine, ed) is orthographically UNMINED
    # (e-deletion: fine+ed spells 'fined', not 'fineed'), so this
    # analysis stands via the TABLE FRONTIER, and the artifact cannot
    # certify any word's identity for it — 'fined' carries the same
    # honest HOMOPHONE sound-claim. Identity certification (verdict OK)
    # exists exactly where the pair artifact does:
    assert gate.surface_of("fine", "ed") is None
    assert gate.verdict("fined", "BOUND", "fine", "ed") == "HOMOPHONE"
    b, sfx = sorted(gate.surface_words)[0]
    w = gate.surface_of(b, sfx)
    assert gate.verdict(w, "BOUND", b, sfx) == "OK"
    assert gate.verdict(w + "x", "BOUND", b, sfx) == "HOMOPHONE"
    print("\nfind = fine+ed: sound-identical, verdict HOMOPHONE "
          f"(frontier-licensed; no mined surface to certify); "
          f"mined pair {b}+{sfx} -> '{w}' certifies OK")


def test_consulted_table_matches_pin(embedder, gate):
    """Law 2's checksum: the table the gate consults at import time
    serializes byte-identically to the pinned artifact."""
    import hashlib
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                           / "scripts"))
    from make_reading_fixtures import serialize_table
    consulted = serialize_table(gate.table)
    pinned = (FIX / "allomorph_table.json").read_text(encoding="utf-8")
    h1 = hashlib.sha256(consulted.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(pinned.encode("utf-8")).hexdigest()
    print(f"\nconsulted table sha256 {h1[:16]}...  pin {h2[:16]}...")
    if h1 != h2:
        for i, (x, y) in enumerate(zip(consulted.splitlines(),
                                       pinned.splitlines())):
            if x != y:
                print(f"first diff, line {i}:\n  consulted: {x}\n"
                      f"  pinned:    {y}")
                break
    assert h1 == h2, \
        "the consulted allomorph table drifted from the pinned artifact"


def test_exact_mode_is_the_default_and_cosine_sleeps(embedder, gate):
    """The closed world runs exact; the theta_p path exists, documented,
    dormant. A cosine-passing anagram proves the modes differ."""
    assert gate.exact is True
    from mirror import PhonGate
    dormant = PhonGate(embedder, [], exact=False,
                       table=gate.table)
    obs = list(embedder.corpus["melted"])
    metal = embedder.corpus["metal"]
    assert dormant._stem_ok(obs, metal), \
        "the dormant cosine path changed character"
    assert not gate._stem_ok(obs, metal)
