"""Probe 44: 10x READING + THE DEFERRAL POLICY (dict-exact engine).
Under the exact gate, analysis = pron-index lookups (O(1)/word), so the
FULL qualifying vocabulary is readable. Policies:
  P0 defer-forever (shipped Part VII behavior)
  P1 + stem-existence: if NO lexicon word has the putative stem's pron,
     the derived reading is impossible -> adopt as atom immediately
     (provenance 'read: no-such-stem')
  P2 = P1 + staleness: stem exists but unmet after 3 epochs -> adopt
     ('read: stem <w> exists unread')
Metrics: known, aligned coverage, deferred-final, adoption ledger, REAL
confabs (must be 0), homophones, the government/nothing/market trio.
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
import sys
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features as feat

# artifact ladder pieces
pair_rems = defaultdict(set)
attested = defaultdict(set)
byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    pair_rems[(tuple(corpus[base]), sfx)].add(tuple(rem))
    attested[sfx].add(tuple(rem)); byb[base][sfx] = w
ALL_REMS = set()
for s_, rs in attested.items(): ALL_REMS |= rs
MAXR = max(len(r) for r in ALL_REMS)

# induced table (probe-26 style, all pairs) for the -s/-ed frontier
def sig(ph):
    f = feat(ph); k = str(getattr(f, "kind", "?"))
    if k == "vowel": return ("vowel", "-", "-", "V+")
    return (k, str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")),
            "V+" if getattr(f, "voiced", False) else "V-")
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
TBL = {"s": defaultdict(Counter), "ed": defaultdict(Counter)}
for base, sfx, w, rem in pairs:
    if sfx in TBL:
        c = cls_rem(rem, sfx)
        if c: TBL[sfx][sig(corpus[base][-1])][c] += 1
def table_choose(base_pron, sfx):
    d = TBL[sfx].get(sig(base_pron[-1]))
    return d.most_common(1)[0][0] if d else None

def licensed(base, sfx, rem):
    key = (tuple(corpus[base]), sfx)
    if key in pair_rems: return tuple(rem) in pair_rems[key]
    if sfx in TBL:
        c = cls_rem(rem, sfx)
        return c is not None and c == table_choose(corpus[base], sfx)
    return tuple(rem) in attested[sfx]

# suffix identity for a remainder (for licensing lookup): map remainder->sfxs
REM2SFX = defaultdict(set)
for s_, rs in attested.items():
    for r in rs: REM2SFX[r].add(s_)

# pron index over the WHOLE lexicon (stem-existence oracle)
PRON2WORDS = defaultdict(list)
for w, p in corpus.items(): PRON2WORDS[tuple(p)].append(w)

cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"): cnt.update(l.split())
stream = [w for w, c in cnt.most_common() if c >= 2 and w in corpus and len(w) >= 4]
print(f"stream: {len(stream)} words (full qualifying vocabulary; Part VII used 6,000)")
E = max(1, len(stream) // 6)   # six epochs

def looks_derived(pron):
    return len(pron) >= 5 and any(tuple(pron[-k:]) in ALL_REMS for k in range(1, MAXR + 1))

def stem_candidates(pron):
    out = []
    for k in range(1, MAXR + 1):
        rem = tuple(pron[-k:])
        if rem in REM2SFX and len(pron) - k >= 2:
            out.append((tuple(pron[:-k]), rem))
    return out

def run(policy):
    known = {}
    bare_ix = {}
    def teach(w, prov):
        known[w] = prov; bare_ix.setdefault(tuple(corpus[w]), []).append(w)
    for b in list(byb.keys())[:15]: teach(b, "birth")
    deferred = {}          # word -> epochs waited
    adopt_ledger = Counter()
    def analyze(w):
        p = tuple(corpus[w])
        hit = bare_ix.get(p)
        if hit:
            return ("OK" if w in hit else "HOMOPHONE", hit[0], None)
        for stem_p, rem in stem_candidates(p):
            hits = bare_ix.get(stem_p)
            if not hits: continue
            for sfx in REM2SFX[rem]:
                for b in hits:
                    if licensed(b, sfx, rem):
                        surf = byb.get(b, {}).get(sfx)
                        ident = (surf == w)
                        return ("OK" if ident else "HOMOPHONE", b, sfx)
        return ("REFUSE", None, None)
    for ep in range(6):
        for w in stream[ep * E:(ep + 1) * E]:
            v, b, s = analyze(w)
            if v == "REFUSE" and w not in known:
                p = tuple(corpus[w])
                if looks_derived(p):
                    if policy >= 1 and not any(sc in PRON2WORDS for sc, _ in stem_candidates(p)):
                        teach(w, "read:no-such-stem"); adopt_ledger["no-such-stem"] += 1
                    else:
                        deferred.setdefault(w, 0)
                else:
                    teach(w, "read")
        still = {}
        for w, age in deferred.items():
            v, b, s = analyze(w)
            if v != "REFUSE":
                adopt_ledger["unlocked"] += 1
            elif policy >= 2 and age + 1 >= 3:
                teach(w, "read:stem-exists-unread"); adopt_ledger["stale-adopt"] += 1
            else:
                still[w] = age + 1
        deferred = still
    test = [(b, s2, w) for b, d in byb.items() if b in known for s2, w in d.items()][:400]
    ok = confab = homo = 0
    for b, s2, w in test:
        v, gb, gs = analyze(w)
        if v == "OK" and gb == b and gs == s2: ok += 1
        elif v == "HOMOPHONE": homo += 1
        elif v == "OK": confab += 1
    trio = {w: (known.get(w, "deferred" if w in deferred else "?"))
            for w in ("government", "nothing", "market") if w in corpus}
    return dict(known=len(known), cov=ok / len(test) * 100, confab=confab, homo=homo,
                deferred=len(deferred), ledger=dict(adopt_ledger), trio=trio)

for pol, name in ((0, "P0 defer-forever"), (1, "P1 stem-existence"), (2, "P2 +staleness")):
    r = run(pol)
    print(f"\n{name}: known {r['known']}  coverage {r['cov']:.1f}%  "
          f"deferred-final {r['deferred']}  REALconfab {r['confab']}  homoph {r['homo']}")
    print(f"   adoptions: {r['ledger']}")
    print(f"   trio: {r['trio']}")
