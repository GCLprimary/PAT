"""M-1/M-2: chapters and circulation (probes 48-49b).

LAW 1 CANARY — the fold stays refuted: the colliding-base family
groups fold to pairwise cosine ~0.99 (probe 48: 0.9912; max here is a
flat 1.0000). Geometric chapter identity would recurse the homoshape
collapse one rung up; the canary pins the number so it cannot be
unlearned.

THE RESIDUAL CLASSES, adjudicated by name (this build's measured ten):
  boarder->border, balled->bald      member is a homophone of another
                                     anchor (bare sound-identity, true)
  haul/hauling/hauler/hauls/hauled   haul and hall are homophone
    -> hall                          ANCHORS (cross-ref'd chapters)
  master->master, flicker->flick[er] dual membership: the member IS its
                                     own anchor (the listing pattern)
  seely->seal (+IY)                  ambiguous alternative derivation —
                                     seal+ly and see+ly are both exact
                                     and licensed; sound-true either way
Every one is a sound-valid claim; REAL confabs == 0, asserted.

LAW 3 — a_mem proposes, the gate identifies: raw-similarity
circulation runs ~40% with hundreds of wrong-chapter claims (recorded,
not gated — the law's justification); gated, wrong-chapter <= 2 at
N=300 and each survivor is adjudicated sound-identical; with the
direct-addressing fallback, end-to-end >= 99%.
"""
import json
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

from pat import (ChapterAddresser, Circulation, ReadingSession,
                   cells_of, deserialize, receipts_of, serialize,
                   synthesize)
from amem.api import Memory
from mirror import Page, PhonGate
from mirror.config import DATA_DIR as MIRROR_DATA
from mirror.diagnostics import shape_seq

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"

SOUND_TRUE = {"homophone-anchor", "member-homophone", "dual-self",
              "alt-derivation"}


@pytest.fixture(scope="module")
def world(organs):
    gate = PhonGate.from_transform(organs.transform)
    byb = defaultdict(dict)
    for base, sfx, w, _ in organs.transform.pairs:
        byb[base][sfx] = w
    fams = [(b, d) for b, d in byb.items() if len(d) >= 3][:500]
    addr = ChapterAddresser(gate, [b for b, _ in fams],
                            organs.embedder.corpus)
    return gate, fams, addr


def adjudicate(emb, member, base, got, addr):
    if got is None:
        return "abstain"
    if tuple(emb.corpus[got]) == tuple(emb.corpus[base]):
        return "homophone-anchor"
    if tuple(emb.corpus[got]) == tuple(emb.corpus[member]):
        return ("dual-self" if got == member else "member-homophone")
    p = tuple(emb.corpus[member])
    ap = tuple(emb.corpus[got])
    if len(p) > len(ap) and p[:len(ap)] == ap:
        return "alt-derivation"          # exact stem, licensed — sound-true
    return "REAL"


def test_anchor_addressing_and_crucible(organs, world):
    gate, fams, addr = world
    emb = organs.embedder
    groups = defaultdict(list)
    for b, _ in fams:
        groups[shape_seq(emb.corpus[b])].append(b)
    coll = {b for g in groups.values() if len(g) >= 2 for b in g}
    n_groups = sum(1 for g in groups.values() if len(g) >= 2)
    ok = tot = cok = ctot = 0
    residuals = []
    for b, d in fams:
        for w in [b] + list(d.values()):
            got = addr.address(w)
            hit = got == b
            ok += int(hit)
            tot += 1
            if b in coll:
                cok += int(hit)
                ctot += 1
            if not hit:
                residuals.append(
                    (w, b, got, adjudicate(emb, w, b, got, addr)))
    print(f"\naddressing {ok}/{tot} = {ok/tot*100:.2f}%   crucible "
          f"({n_groups} groups) {cok}/{ctot} = {cok/ctot*100:.2f}%")
    for r in residuals:
        print("  residual:", r)
    assert ok / tot >= 0.99, f"addressing {ok/tot:.4f} < 99%"
    assert cok / ctot >= 0.95, f"crucible {cok/ctot:.4f} < 95%"
    assert 40 <= n_groups <= 55, "the colliding-group census moved"
    real = [r for r in residuals if r[3] == "REAL"]
    assert not real, f"REAL confabs in addressing: {real}"
    named = {r[0] for r in residuals}
    assert {"boarder", "balled", "master", "flicker",
            "seely"} <= named | {None}, \
        f"the named residual set changed: {sorted(named)} — adjudicate " \
        f"the newcomers before trusting the build"


def test_frontier_addressing(organs, world):
    """Pair scrubbed from the artifacts: the member must reach its
    chapter through the induced-table frontier (generalization, not
    lookup); homophone-anchor landings stay honest."""
    gate, fams, addr = world
    emb = organs.embedder
    ok = tot = 0
    residuals = []
    for b, d in fams:
        sfx, w = sorted(d.items())[-1]
        got = addr.address(w, scrub=(b, sfx))
        hit = got == b
        ok += int(hit)
        tot += 1
        if not hit:
            residuals.append(
                (w, b, got, adjudicate(emb, w, b, got, addr)))
    print(f"\nfrontier addressing (pair scrubbed): {ok}/{tot} = "
          f"{ok/tot*100:.2f}%  residuals {residuals}")
    assert ok / tot >= 0.95
    assert all(r[3] in SOUND_TRUE | {"abstain"} for r in residuals), \
        f"a frontier residual is a REAL confab: {residuals}"


def test_fold_canary_law_one(organs, world):
    """Geometric chapter identity is FORBIDDEN, and this is why,
    pinned: colliding-base families FOLD TOGETHER (~0.99 pairwise;
    probe 48 measured 0.9912). If this canary fails, the shape space
    changed character — it does NOT mean centroids became safe."""
    gate, fams, addr = world
    emb = organs.embedder
    tr = organs.transform

    def fold(b, d):
        vs = [emb.shape_vec(emb.corpus[b])]
        for sfx, w in d.items():
            vs.append(tr.bind(emb.corpus[b], sfx, "shape")
                      if sfx in tr.modal_phon
                      else emb.shape_vec(emb.corpus[w]))
        v = np.sum(vs, axis=0)
        return v / np.linalg.norm(v)

    groups = defaultdict(list)
    for b, d in fams:
        groups[shape_seq(emb.corpus[b])].append((b, d))
    sims = []
    for g in groups.values():
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                sims.append(float(fold(*g[i]) @ fold(*g[j])))
    sims = np.array(sims)
    print(f"\nfold canary: {len(sims)} colliding family pairs; "
          f"cos mean {sims.mean():.4f}  max {sims.max():.4f}")
    assert sims.mean() >= 0.97 and sims.max() >= 0.999, \
        "the fold collision weakened — the shape space changed " \
        "character (centroids are still not identity)"


def test_conservation_and_restart(organs, stream_fixture=None):
    """LAW 2, hard: receipts in == receipts out, exact class counts;
    serialize -> reload identical."""
    from collections import Counter
    fx = json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))
    session = ReadingSession(organs, seed_bases=fx["seeds"], policy=2)
    session.read(fx["stream"][:2000], epochs=2, epoch_size=1000,
                 counts=fx["counts"])
    session.study(Page.load(MIRROR_DATA / "page_irregular_plurals.txt"))
    before = Counter(p.split(":")[0].split()[0]
                     for p in session.known.values())
    before.update(p["provenance"].split(":")[0].split()[0]
                  for p in session.retired.values())
    chapters = synthesize(session)
    after = receipts_of(chapters)
    placed = sum(len(c.ledger) for c in chapters.values())
    n_in = len(session.known) + len(session.retired)
    print(f"\nconservation: {n_in} receipts -> {placed} placed in "
          f"{len(chapters)} chapters; classes {after}")
    assert placed == n_in
    assert dict(before) == after, \
        f"receipts NOT conserved: {dict(before)} != {after}"
    assert len(after) == 4          # birth / read / lesson / derivable
    blob = serialize(chapters)
    assert serialize(deserialize(blob)) == blob, \
        "chapters did not survive death identically"


def test_chapter_structure_dual_and_crossrefs(organs):
    """The structures law 1 demands, exercised deliberately: master is
    a member of mast's chapter AND anchors its own (dual, both ways);
    hall and haul are sound-identical anchors (cross-refs both ways)."""
    session = ReadingSession(
        organs, seed_bases=["mast", "master", "masters", "hall",
                            "haul", "hauls"], policy=2)
    chapters = synthesize(session)
    assert "master" in chapters["mast"].ledger
    assert "masters" in chapters["master"].ledger
    assert "master" in chapters["mast"].dual
    assert "master" in chapters["master"].dual
    print(f"\ndual: mast.dual={chapters['mast'].dual}  "
          f"master.dual={chapters['master'].dual}")
    assert chapters["hall"].cross_refs == ["haul"]
    assert chapters["haul"].cross_refs == ["hall"]
    assert "hauls" in chapters["haul"].ledger \
        or "hauls" in chapters["hall"].ledger


def test_gated_circulation(organs, world):
    """LAW 3: a_mem proposes, the gate identifies. Raw similarity is
    recorded as the law's justification; the gated walk's wrong-chapter
    count is <= 2 at N=300 with every survivor sound-identical; with
    the fallback, end-to-end >= 99%."""
    gate, fams, addr = world
    emb = organs.embedder
    sel = fams[:300]
    with tempfile.TemporaryDirectory() as tmp:
        mem = Memory(seed=3, path=str(Path(tmp) / "cx"), autosave=False)
        g = int(mem.grid)
        addr300 = ChapterAddresser(gate, [b for b, _ in sel],
                                   emb.corpus)
        circ = Circulation(mem, gate, addr300, emb)
        for b, d in sel:
            mid = mem.write(cells_of(emb.shape_vec(emb.corpus[b]), g),
                            meta={"anchor": b})
            circ.anchor_of[mid] = b

        raw_ok = raw_wrong = tot = 0
        for b, d in sel:
            for w in list(d.values())[:2]:
                r = mem.recall(
                    cue=cells_of(emb.shape_vec(emb.corpus[w]), g))
                tot += 1
                got = circ.anchor_of.get(r.identity) if r else None
                if got == b or (got and tuple(emb.corpus[got])
                                == tuple(emb.corpus[b])):
                    raw_ok += 1
                elif got is not None:
                    raw_wrong += 1
        print(f"\nraw circulation (recorded, not gated): "
              f"{raw_ok}/{tot} = {raw_ok/tot*100:.1f}% with "
              f"{raw_wrong} wrong-chapter claims")

        ok = wrong = refuse = fallback = 0
        wrongs = []
        for b, d in sel:
            for w in list(d.values())[:2]:
                got, how = circ.recall_chapter(w)
                fallback += int(how == "fallback-direct")
                if got is None:
                    refuse += 1
                elif got == b or tuple(emb.corpus[got]) == \
                        tuple(emb.corpus[b]):
                    ok += 1
                else:
                    wrong += 1
                    wrongs.append((w, b, got))
        print(f"gated: {ok}/{tot} = {ok/tot*100:.1f}%  refuse {refuse}"
              f"  wrong {wrong} {wrongs}  (fallback rescued {fallback})")
        assert wrong <= 2, \
            f"{wrong} gated wrong-chapter claims — a 3 is a finding"
        for w, b, got in wrongs:
            assert tuple(emb.corpus[w])[:len(emb.corpus[got])] == \
                tuple(emb.corpus[got]) or tuple(emb.corpus[w]) == \
                tuple(emb.corpus[got]), \
                f"a gated wrong-chapter claim is NOT sound-true: " \
                f"{w} -> {got}"
        assert ok / tot >= 0.99, f"end-to-end {ok/tot:.4f} < 99%"
        assert raw_wrong > 50, \
            "the raw catastrophe shrank — re-measure law 3's premium"
