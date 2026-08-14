"""M-1/M-2: chapters — the metabolic synthesis step (probes 48-49b).

LAW 1: A CHAPTER IS AN ANCHOR PLUS A LEDGER — NEVER A CENTROID. Probe
48 measured why: folding a family's member vectors into a centroid
recurses the homoshape collapse one rung up — the colliding-base
family groups fold to pairwise cosine ~0.9912, indistinguishable. The
canary test pins that number so the temptation stays refuted. Here the
base's VECTOR proposes (circulation below), the exact gate IDENTIFIES,
and the chapter's content is merged receipted structure: a ledger of
(word -> provenance), homophone-anchor cross-references (hall <-> haul),
dual-membership notes (master: member of mast's chapter AND anchor of
its own — the listing pattern made structural), and a drift slot
(members whose folded-space margin went negative; receipt only, no
action — mirror.meaning_rows.drift_census fills it).

LAW 2: SYNTHESIS CONSERVES RECEIPTS BY CONSTRUCTION. Ledger-merge is
the only composition; every receipt lives in exactly one ledger
(a dual member's receipt lives in its stem's chapter; its own chapter
holds its members and the cross-note); receipts in == receipts out,
asserted; chapters serialize and reload identically.

LAW 3: A_MEM PROPOSES; THE GATE IDENTIFIES. Circulation writes each
chapter's anchor pattern into a real a_mem library and recalls by
MEMBER cue. The recall's ranked `r.scores` is a proposal list, never
an identity claim: each proposed anchor must pass the sequence-exact
stem check (the shipped artifact ladder) or the walk continues;
exhausted proposals REFUSE; refusals fall back to direct addressing.
Raw-similarity circulation measured 34.8% with 391 wrong-chapter
claims at N=300; gated, ~84% end-to-end proposal accuracy with <= 2 —
and with the fallback, addressing stays >= 99%.
"""
import json

import numpy as np

from mirror import PhonGate
from mirror.surface import classify_remainder

from .reading import ReadingSession


class Chapter:
    def __init__(self, anchor, provenance=None):
        self.anchor = anchor
        self.ledger = {}            # word -> provenance receipt
        self.cross_refs = []        # homophone anchors (sound-identical)
        self.dual = {}              # word -> note (dual membership)
        self.census = []            # shape-census entries riding along
        self.drift = []             # meaning-drift receipts (M-3)
        if provenance is not None:
            self.ledger[anchor] = provenance

    def to_dict(self):
        return {"anchor": self.anchor, "ledger": dict(self.ledger),
                "cross_refs": list(self.cross_refs),
                "dual": dict(self.dual), "census": list(self.census),
                "drift": list(self.drift)}

    @classmethod
    def from_dict(cls, d):
        ch = cls(d["anchor"])
        ch.ledger = dict(d["ledger"])
        ch.cross_refs = list(d["cross_refs"])
        ch.dual = dict(d["dual"])
        ch.census = list(d["census"])
        ch.drift = list(d["drift"])
        return ch


class ChapterAddresser:
    """Direct addressing over a fixed anchor set: bare pron identity
    first, then remainder peeling under the artifact ladder. `scrub`
    forces one (base, suffix) pair onto the induced-table frontier —
    the probe-48b generalization test (addressing without the lookup)."""

    def __init__(self, gate, anchors, corpus):
        self.gate = gate
        self.corpus = corpus
        self.anchor_prons = {}
        for b in anchors:
            self.anchor_prons.setdefault(tuple(corpus[b]), b)
        self.rem2sfx = {}
        self.max_rem = 1
        for sfx, rems in gate.attested.items():
            for r in rems:
                self.rem2sfx.setdefault(r, set()).add(sfx)
                self.max_rem = max(self.max_rem, len(r))

    def _frontier_licensed(self, base_pron, sfx, rem):
        """The unmined-frontier arm of the ladder only (table for
        -s/-ed, suffix-wide set otherwise) — what a scrubbed pair
        faces."""
        if sfx in ("s", "ed"):
            cls = classify_remainder(list(rem), sfx)
            return (cls is not None
                    and cls == self.gate.table.choose(list(base_pron),
                                                      sfx))
        return tuple(rem) in self.gate.attested.get(sfx, ())

    def address(self, word, scrub=None):
        """-> anchor word or None (abstention)."""
        p = tuple(self.corpus[word])
        hit = self.anchor_prons.get(p)
        if hit is not None:
            return hit
        for k in range(1, self.max_rem + 1):
            if len(p) - k < 2:
                break
            stem, rem = p[:-k], p[-k:]
            b = self.anchor_prons.get(stem)
            if b is None or rem not in self.rem2sfx:
                continue
            for sfx in sorted(self.rem2sfx[rem]):
                if scrub == (b, sfx):
                    ok = self._frontier_licensed(self.corpus[b], sfx,
                                                 rem)
                else:
                    ok = self.gate.licensed(self.corpus[b], sfx,
                                            list(rem))
                if ok:
                    return b
        return None


def synthesize(session):
    """Ledger-merge a ReadingSession's known/retired/census state into
    chapters. MAXR is asserted against the artifact (law: never
    hard-coded). Receipts in == receipts out, by construction —
    asserted anyway in the battery, because 'by construction' is a
    claim and claims get tests."""
    artifact_maxr = max(len(r) for rems in session.gate.attested.values()
                        for r in rems)
    assert session.max_rem == artifact_maxr, \
        f"MAXR {session.max_rem} != artifact {artifact_maxr}"

    corpus = session.emb.corpus
    chapters = {}

    def chapter_of(anchor):
        if anchor not in chapters:
            chapters[anchor] = Chapter(anchor)
        return chapters[anchor]

    # every living receipt: a member of its stem's chapter when the
    # engine derives it (exclude=self — a word never stems itself),
    # its own anchor otherwise
    placements = {}
    for w, prov in list(session.known.items()):
        mode, b, sfx, verdict = session.analyze_word(w, exclude=w)
        anchor = b if mode == "BOUND" and b in session.known else w
        placements[w] = anchor
        chapter_of(anchor).ledger[w] = prov
    # retired receipts: aliases live in their derivation stem's chapter
    for w, entry in session.retired.items():
        stem = entry["alias"].split()[1].split("+")[0]
        anchor = stem if stem in session.known else w
        placements[w] = anchor
        chapter_of(anchor).ledger[w] = entry["provenance"]

    # dual membership: a word receipted in another's chapter that also
    # anchors its own (the master/mast structure) — noted both ways
    for w, anchor in placements.items():
        if anchor != w and w in chapters:
            chapters[anchor].dual[w] = f"also anchors its own chapter"
            chapters[w].dual[w] = f"member of {anchor}'s chapter"

    # homophone-anchor cross-refs: distinct anchors, identical prons
    by_pron = {}
    for a in chapters:
        by_pron.setdefault(tuple(corpus[a]), []).append(a)
    for group in by_pron.values():
        if len(group) >= 2:
            for a in group:
                chapters[a].cross_refs = [x for x in group if x != a]

    # the shape census rides with its word's chapter
    for entry in session.census:
        anchor = placements.get(entry["word"])
        if anchor is not None:
            chapters[anchor].census.append(dict(entry))
    return chapters


def receipts_of(chapters):
    """Provenance-class counts across every ledger (the conservation
    currency)."""
    counts = {}
    for ch in chapters.values():
        for prov in ch.ledger.values():
            cls = prov.split(":")[0].split()[0]
            counts[cls] = counts.get(cls, 0) + 1
    return counts


def serialize(chapters):
    return json.dumps({a: ch.to_dict() for a, ch in chapters.items()},
                      sort_keys=True)


def deserialize(blob):
    return {a: Chapter.from_dict(d)
            for a, d in json.loads(blob).items()}


# ── M-2: gated circulation (a_mem proposes, the gate identifies) ─────
def cells_of(vec, grid, k=24):
    """The pinned adapter: a unit shape vector's top-k dimensions as
    lattice cells."""
    idx = np.argsort(vec)[::-1][:k]
    return [(int(d) // grid, int(d) % grid) for d in idx]


class Circulation:
    """Chapters written to a real a_mem library as anchor patterns;
    member-cued recall returns a RANKED PROPOSAL that the exact gate
    adjudicates. Refusal falls back to direct addressing."""

    def __init__(self, memory, gate, addresser, embedder,
                 propose_k=12):
        self.memory = memory
        self.gate = gate
        self.addresser = addresser
        self.emb = embedder
        self.propose_k = propose_k
        self.anchor_of = {}         # mid -> anchor word
        self.grid = int(memory.grid)

    def write_chapter(self, chapter):
        v = self.emb.shape_vec(self.emb.corpus[chapter.anchor])
        mid = self.memory.write(cells_of(v, self.grid),
                                meta={"anchor": chapter.anchor})
        self.anchor_of[mid] = chapter.anchor
        return mid

    def _stem_identifies(self, member_pron, anchor):
        """The shipped ladder as the identity check: exact bare pron,
        or exact stem + licensed remainder."""
        ap = tuple(self.emb.corpus[anchor])
        p = tuple(member_pron)
        if p == ap:
            return True
        if len(p) > len(ap) and p[:len(ap)] == ap:
            rem = p[len(ap):]
            for sfx in sorted(self.gate.attested):
                if self.gate.licensed(list(ap), sfx, list(rem)):
                    return True
        return False

    def recall_chapter(self, member):
        """-> (anchor | None, how): how in {'gated-proposal',
        'fallback-direct', 'refused'}."""
        p = self.emb.corpus[member]
        r = self.memory.recall(
            cue=cells_of(self.emb.shape_vec(p), self.grid))
        if r is not None and r.scores:
            ranked = sorted(r.scores, key=r.scores.get, reverse=True)
            for mid in ranked[:self.propose_k]:
                anchor = self.anchor_of.get(mid)
                if anchor is None:
                    continue
                if self._stem_identifies(p, anchor):
                    return anchor, "gated-proposal"
        direct = self.addresser.address(member)
        if direct is not None:
            return direct, "fallback-direct"
        return None, "refused"
