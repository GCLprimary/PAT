"""Probe 38: THE WIDENED FRAME (subject identification, law-14 work).
v2 frame = adjunct-skip + subject-relative inner registers + frame refusal.
Buckets: plain / adjunct-led / relative-clause; attractors within each.
Models: REGISTER (frame subject) | recent-noun | trigram.
Regression: on strict-frame sentences, v2 must agree with strict.
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

SG_LEX, PL_LEX = set(), set()
for base, sfx, w, rem in pairs:
    if sfx == "s": SG_LEX.add(base); PL_LEX.add(w)
AMB = SG_LEX & PL_LEX; SG_LEX -= AMB; PL_LEX -= AMB
SG_V = {"is", "was", "has", "does"}; PL_V = {"are", "were", "have", "do"}
DET = {"the", "a", "an", "this", "that", "these", "those", "his", "her", "their", "its", "our", "my"}
PREP = {"of", "in", "on", "at", "with", "for", "to", "from", "by", "over", "under", "near", "during", "after", "before", "through"}
REL = {"who", "which", "whose"}

def num_of(w):
    if w in SG_LEX: return "sg"
    if w in PL_LEX: return "pl"
    return None
def lexy(w): return num_of(w) is not None

sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt") if len(l.split()) >= 6]
rng = np.random.default_rng(5)
idx = rng.permutation(len(sents)); cut = int(len(sents) * 0.95)
train = [sents[i] for i in idx[:cut]]; held = [sents[i] for i in idx[cut:]]
bi, tri = defaultdict(Counter), defaultdict(Counter)
for s in train:
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1

def frame_v2(s):
    """-> (subj_i, verb_j, bucket) or (None, None, refusal_reason)"""
    i = 0; had_adjunct = False
    # adjunct-skip: leading PP chains
    while i < len(s) - 2 and s[i] in PREP:
        had_adjunct = True
        i += 1
        if i < len(s) and s[i] in DET: i += 1
        # consume up to 2 tokens to reach the PP's noun
        hops = 0
        while i < len(s) and not lexy(s[i]) and hops < 2: i += 1; hops += 1
        if i >= len(s) or not lexy(s[i]): return None, None, "adjunct-unparsed"
        i += 1
    if i >= len(s) - 1 or s[i] not in DET or not num_of(s[i + 1]):
        return None, None, "no-det-n-subject"
    subj_i = i + 1
    j = subj_i + 1; had_rel = False; guard = 0
    while j < min(subj_i + 16, len(s)):
        t = s[j]
        rel_here = t in REL or (t == "that" and lexy(s[j - 1]))
        if rel_here:
            had_rel = True
            if j + 1 < len(s):
                nxt = s[j + 1]
                verbish = (nxt in SG_V | PL_V) or (lexy(nxt) and s[j] not in DET | PREP)
                if verbish:
                    j += 2            # close inner clause at its verb, scan on
                    continue
            return None, None, "object-relative"
        if t in SG_V | PL_V:
            bucket = "relative" if had_rel else ("adjunct" if had_adjunct else "plain")
            return subj_i, j, bucket
        j += 1; guard += 1
    return None, None, "no-verb-in-window"

def between_nouns(s, subj_i, j):
    out = []
    for k in range(subj_i + 1, j):
        if num_of(s[k]) and s[k - 1] in DET | PREP:
            out.append((s[k], num_of(s[k])))
    return out

cases = []; refusals = Counter(); strict_agree = [0, 0]
for s in held:
    subj_i, j, bucket = frame_v2(s)
    if subj_i is None:
        refusals[bucket] += 1; continue
    subj_n = num_of(s[subj_i]); gold = "sg" if s[j] in SG_V else "pl"
    nb = between_nouns(s, subj_i, j)
    attractor = any(n != subj_n for _, n in nb)
    cases.append((s, subj_i, j, subj_n, gold, attractor, nb, bucket))
    # strict-frame regression: sentence-initial DET-N + PP-only chain
    if s[0] in DET and num_of(s[1]):
        strict_ok = (subj_i == 1)
        strict_agree[0] += int(strict_ok); strict_agree[1] += 1

print(f"v2 yield: {len(cases)} cases  (strict frame was 240)")
print(f"  attractors: {sum(c[5] for c in cases)}  (strict was 12)")
bk = Counter(c[7] for c in cases)
print(f"  buckets: {dict(bk)}")
print(f"  frame refusals: {sum(refusals.values())}  top: {refusals.most_common(3)}")
print(f"  strict-subset agreement: {strict_agree[0]}/{strict_agree[1]}")

res = {}
for name in ("trigram", "recent-noun", "REGISTER"):
    res[name] = {b: [0, 0] for b in ("plain", "adjunct", "relative")} | {"att": [0, 0], "noatt": [0, 0]}
for s, subj_i, j, subj_n, gold, att, nb, bucket in cases:
    ctx = (s[j - 2], s[j - 1]); best, bn = None, -1
    for v in SG_V | PL_V:
        c = tri[ctx][v] if ctx in tri else 0
        if c == 0 and s[j - 1] in bi: c = 0.1 * bi[s[j - 1]][v]
        if c > bn: bn, best = c, v
    preds = {
        "trigram": ("sg" if best in SG_V else "pl") if best else None,
        "recent-noun": nb[-1][1] if nb else subj_n,
        "REGISTER": subj_n,
    }
    for name, p in preds.items():
        if p is None: continue
        res[name][bucket][0] += int(p == gold); res[name][bucket][1] += 1
        key = "att" if att else "noatt"
        res[name][key][0] += int(p == gold); res[name][key][1] += 1

print("\naccuracy         plain          adjunct        relative       no-att         attractor")
for name in ("trigram", "recent-noun", "REGISTER"):
    row = []
    for b in ("plain", "adjunct", "relative", "noatt", "att"):
        c, n = res[name][b]
        row.append(f"{c}/{n}={c/max(n,1)*100:3.0f}%")
    print(f"  {name:12s} " + "  ".join(f"{x:12s}" for x in row))
