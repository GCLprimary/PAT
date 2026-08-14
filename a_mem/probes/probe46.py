"""Probe 46: THE TENSE REGISTER (feature #2 on the stamp machinery).
An auxiliary OPENS a form requirement; the verb CLOSES it:
  PERF {has,have,had}        -> -ed form (participle, regulars)
  PROG {is,are,was,were,am}  -> -ing form
  MODAL/DO {will,...,did,to} -> bare form
Battery: attested aux (gap<=3 adverbs) V-form triples from corpus_big;
foils swap V to the other two forms of the SAME base; three-way choice.
Register = distance-blind requirement check; trigram = backoff logp of
the three sentences. Accuracy by gap size is the wall.
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

BASE, ED, ING = {}, {}, {}
fam = defaultdict(dict)
for base, sfx, w, rem in pairs:
    fam[base][sfx] = w
for b, d in fam.items():
    if "ed" in d and "ing" in d:
        BASE[b] = b; ED[b] = d["ed"]; ING[b] = d["ing"]
FORMS = {}          # word -> (base, form)
for b in BASE:
    FORMS[b] = (b, "bare"); FORMS[ED[b]] = (b, "ed"); FORMS[ING[b]] = (b, "ing")

PERF = {"has", "have", "had"}
PROG = {"is", "are", "was", "were", "am", "been", "being"}
MODAL = {"will", "would", "can", "could", "may", "might", "must",
         "should", "shall", "do", "does", "did", "to"}
REQ = {**{a: "ed" for a in PERF}, **{a: "ing" for a in PROG},
       **{a: "bare" for a in MODAL}}
ADV = {"quickly", "really", "very", "also", "never", "always", "often",
       "just", "still", "not", "n't", "already", "recently", "probably",
       "certainly", "finally", "usually", "simply", "actually", "even"}

sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt")]
uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
for s in sents:
    uni.update(s)
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1
tot = sum(uni.values())
def logp(ws):
    s = 0.0
    for i, w in enumerate(ws):
        if i >= 2 and (ws[i-2], ws[i-1]) in tri and tri[(ws[i-2], ws[i-1])][w] > 0:
            c = tri[(ws[i-2], ws[i-1])]; s += np.log(c[w] / sum(c.values()))
        elif i >= 1 and ws[i-1] in bi and bi[ws[i-1]][w] > 0:
            c = bi[ws[i-1]]; s += np.log(0.4 * c[w] / sum(c.values()))
        else: s += np.log(0.16 * max(uni[w], 0.1) / tot)
    return s

cases = defaultdict(list)      # gap -> [(sentence, aux_i, v_i, base, attested_form)]
for s in sents:
    for i, w in enumerate(s[:-1]):
        if w in REQ:
            j = i + 1; gap = 0
            while j < len(s) and s[j] in ADV and gap < 3:
                j += 1; gap += 1
            if j < len(s) and s[j] in FORMS:
                b, form = FORMS[s[j]]
                if form == REQ[w]:            # attested consonant case
                    cases[gap].append((s, i, j, b, form))
for g in cases: 
    rng = np.random.default_rng(11); rng.shuffle(cases[g])
    cases[g] = cases[g][:400]

def register_pick(aux, forms3):
    return REQ[aux]
print("gap   n     REGISTER   trigram")
for g in sorted(cases):
    cs = cases[g]
    reg_ok = tri_ok = 0
    for s, i, j, b, form in cs:
        variants = {"bare": b, "ed": ED[b], "ing": ING[b]}
        reg_ok += int(register_pick(s[i], variants) == form)
        best, bl = None, -1e18
        for f2, w2 in variants.items():
            s2 = list(s); s2[j] = w2
            lo, hi = max(0, j - 4), min(len(s), j + 3)
            l = logp(s2[lo:hi])
            if l > bl: bl, best = l, f2
        tri_ok += int(best == form)
    print(f"  {g}   {len(cs):4d}    {reg_ok/len(cs)*100:5.1f}%    {tri_ok/len(cs)*100:5.1f}%")
print("\naux-class consonance in raw text (rule-reality check):")
for name, aux_set in (("PERF->ed", PERF), ("PROG->ing", PROG), ("MODAL->bare", MODAL)):
    ok = n = 0
    for s in sents[:60000]:
        for i, w in enumerate(s[:-1]):
            if w in aux_set and s[i+1] in FORMS:
                b, form = FORMS[s[i+1]]
                ok += int(form == REQ[w]); n += 1
    print(f"  {name:12s} adjacent attested consonance: {ok}/{n} = {ok/max(n,1)*100:.1f}%")
