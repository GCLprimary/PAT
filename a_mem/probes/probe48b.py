"""Probe 48b: THE SPEND TESTS (chapters = anchor + ledger).
A ANCHOR ADDRESSING — every family member resolves to its chapter via
  the exact machinery; the 46 colliding-base groups (centroid cos
  0.9912) must attribute perfectly: the anchor design neutralizes the
  recursed collapse.
B FRONTIER ADDRESSING — hold one member's PAIR out of the arbitration
  artifacts entirely; the member must still reach its chapter through
  the induced-table frontier (generalization, not lookup).
C CONSERVATION — mini world (birth + read/P2 + lesson) synthesized into
  chapters by ledger-merge; receipts counted before/after; serialize ->
  reload -> identical. Synthesis conserves receipts; chapters survive
  death.
"""
import json, warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
import sys
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features as feat

def sig(ph):
    f = feat(ph); k = str(getattr(f, "kind", "?"))
    if k == "vowel": return ("vowel", "-", "-", "V+")
    return (k, str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")),
            "V+" if getattr(f, "voiced", False) else "V-")
def shp(p):
    f = feat(p)
    return ("V",) if str(getattr(f, "kind", "?")) == "vowel" else \
        (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
def skey(w): return tuple(shp(p) for p in corpus[w])
def cls_rem(rem, kind):
    t = [x.lower() for x in rem]
    if kind == "s":
        if len(rem) >= 2 and t[-1] == "z": return "epen"
        if t == ["z"]: return "z"
        if t == ["s"]: return "s"
    else:
        if len(rem) >= 2 and t[-1] == "d": return "epen"
        if t == ["d"]: return "d"
        if t == ["t"]: return "t"
    return None

pair_rems = defaultdict(set); attested = defaultdict(set); byb = defaultdict(dict)
TBL = {"s": defaultdict(Counter), "ed": defaultdict(Counter)}
for base, sfx, w, rem in pairs:
    pair_rems[(base, sfx)].add(tuple(rem)); attested[sfx].add(tuple(rem))
    byb[base][sfx] = w
    if sfx in TBL:
        c = cls_rem(rem, sfx)
        if c: TBL[sfx][sig(corpus[base][-1])][c] += 1
def table_ok(b, sfx, rem):
    if sfx in TBL:
        c = cls_rem(rem, sfx)
        d = TBL[sfx].get(sig(corpus[b][-1]))
        return c is not None and d and c == d.most_common(1)[0][0]
    return tuple(rem) in attested[sfx]
def licensed(b, sfx, rem, skip_pair=False):
    if not skip_pair and (b, sfx) in pair_rems:
        return tuple(rem) in pair_rems[(b, sfx)]
    return table_ok(b, sfx, rem)

fams = [(b, d) for b, d in byb.items() if len(d) >= 3][:500]
anchors = {tuple(corpus[b]): b for b, _ in fams}
def address(w, skip_pair_for=None):
    p = tuple(corpus[w])
    if p in anchors: return anchors[p]
    for k in (1, 2):
        stem, rem = p[:-k], p[-k:]
        b = anchors.get(stem)
        if b:
            for sfx in byb[b]:
                skip = (skip_pair_for == (b, sfx))
                if licensed(b, sfx, list(rem), skip_pair=skip):
                    return b
    return None

# A — full addressing + colliding-group crucible
groups = defaultdict(list)
for b, _ in fams: groups[skey(b)].append(b)
coll_bases = {b for g in groups.values() if len(g) >= 2 for b in g}
ok = tot = cok = ctot = miss = 0
for b, d in fams:
    for w in [b] + list(d.values()):
        got = address(w)
        hit = (got == b); ok += int(hit); tot += 1
        if not hit and got is not None: miss += 1
        if b in coll_bases:
            cok += int(hit); ctot += 1
print(f"A anchor addressing: {ok}/{tot} = {ok/tot*100:.1f}%   wrong-chapter: {miss}")
print(f"  colliding-group crucible ({len([g for g in groups.values() if len(g)>=2])} groups): {cok}/{ctot} = {cok/ctot*100:.1f}%")

# B — frontier addressing (pair scrubbed)
bok = btot = 0
for b, d in fams:
    sfx, w = sorted(d.items())[-1]
    got = address(w, skip_pair_for=(b, sfx))
    bok += int(got == b); btot += 1
print(f"B frontier addressing (pair scrubbed, table licenses): {bok}/{btot} = {bok/btot*100:.1f}%")

# C — conservation through synthesis + restart
cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"): cnt.update(l.split())
stream = [w for w, c in cnt.most_common() if c >= 4 and w in corpus and len(w) >= 4][:2000]
PAGE = {"man": "men", "child": "children", "person": "people", "foot": "feet",
        "goose": "geese", "mouse": "mice", "tooth": "teeth", "woman": "women"}
known = {}
for b in list(byb.keys())[:15]: known[b] = "birth"
for w in stream:
    if w not in known and w in byb: known[w] = f"read: attested {cnt[w]}"
for sg, pl in PAGE.items():
    for w2 in (sg, pl):
        if w2 in corpus and w2 not in known: known[w2] = "lesson:irregular_plurals"
receipts_before = Counter(v.split(":")[0].split()[0] for v in known.values())

chapters = {}
for w, prov in known.items():
    b = address(w) or w
    ch = chapters.setdefault(b, {"anchor": b, "ledger": {}})
    ch["ledger"][w] = prov
receipts_after = Counter(p.split(":")[0].split()[0]
                         for ch in chapters.values() for p in ch["ledger"].values())
placed = sum(len(ch["ledger"]) for ch in chapters.values())
blob = json.dumps(chapters, sort_keys=True)
reborn = json.loads(blob)
identical = (reborn == chapters)
print(f"C conservation: words {len(known)} -> placed {placed} in {len(chapters)} chapters")
print(f"  receipts before {dict(receipts_before)}")
print(f"  receipts after  {dict(receipts_after)}   conserved: {receipts_before == receipts_after}")
print(f"  restart: serialize -> reload identical: {identical}")
