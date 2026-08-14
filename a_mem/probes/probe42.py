"""Probe 42: THE BLiMP HARNESS + the first lesson line.
A) Trigram forced-choice baseline (stupid backoff, corpus_big 5.2M) on all
   67 paradigms -> overall + category table.
B) REGISTER judgment on agreement paradigms (number lexicon from our own
   -s pairs): det-noun consonance (this/that=sg, these/those=pl) and
   subject-verb (subject number vs verb s-form), trigram fallback.
C) THE LESSON LINE: the det-number rule IS one taught line. Exchange rate:
   trigram at 1M vs 5.2M on those paradigms vs the line — can volume buy
   what a page teaches?
"""
import json, glob, re, warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

SG_LEX, PL_LEX = set(), set()
for base, sfx, w, rem in pairs:
    if sfx == "s": SG_LEX.add(base); PL_LEX.add(w)
AMB = SG_LEX & PL_LEX; SG_LEX -= AMB; PL_LEX -= AMB

def toks(s):
    return re.sub(r"[^a-z' ]", "", s.lower()).split()

def build_lm(path, cap=None):
    uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
    n = 0
    for l in open(path):
        ws = l.split()
        uni.update(ws)
        for a, b in zip(ws, ws[1:]): bi[a][b] += 1
        for a, b, c in zip(ws, ws[1:], ws[2:]): tri[(a, b)][c] += 1
        n += len(ws)
        if cap and n >= cap: break
    tot = sum(uni.values())
    return uni, bi, tri, tot

def scorer(lm):
    uni, bi, tri, tot = lm
    def logp(ws):
        s = 0.0
        for i, w in enumerate(ws):
            if i >= 2 and (ws[i-2], ws[i-1]) in tri and tri[(ws[i-2], ws[i-1])][w] > 0:
                c = tri[(ws[i-2], ws[i-1])]
                s += np.log(c[w] / sum(c.values()))
            elif i >= 1 and ws[i-1] in bi and bi[ws[i-1]][w] > 0:
                c = bi[ws[i-1]]
                s += np.log(0.4 * c[w] / sum(c.values()))
            else:
                s += np.log(0.4 * 0.4 * max(uni[w], 0.1) / tot)
        return s
    return logp

DEMO_SG = {"this", "that"}; DEMO_PL = {"these", "those"}
def num_of(w):
    if w in SG_LEX: return "sg"
    if w in PL_LEX: return "pl"
    return None

def lesson_judge(g, b):
    """the taught line: demonstrative number must match its noun."""
    def viol(ws):
        for i, w in enumerate(ws[:-1]):
            if w in DEMO_SG or w in DEMO_PL:
                for j in (i + 1, i + 2, i + 3):     # allow adjectives
                    if j < len(ws):
                        n = num_of(ws[j])
                        if n:
                            want = "sg" if w in DEMO_SG else "pl"
                            return 0 if n == want else 1
        return None
    vg, vb = viol(g), viol(b)
    if vg is None or vb is None or vg == vb: return None
    return "g" if vg < vb else "b"

def sv_judge(g, b):
    """subject-verb: first det-N subject number vs the differing verb's s-form."""
    DET = {"the", "a", "an", "this", "that", "these", "those", "some", "all", "most", "many", "each"}
    dg, db = toks(g), toks(b)
    if len(dg) != len(db): return None
    diffs = [i for i, (x, y) in enumerate(zip(dg, db)) if x != y]
    if len(diffs) != 1: return None
    i = diffs[0]
    vg_, vb_ = dg[i], db[i]
    s_g = vg_.endswith("s") and not vb_.endswith("s")
    s_b = vb_.endswith("s") and not vg_.endswith("s")
    if not (s_g or s_b): return None
    subj = None
    for k in range(len(dg) - 1):
        if dg[k] in DET and num_of(dg[k + 1]) and k + 1 < i:
            subj = num_of(dg[k + 1]); break
    if subj is None: return None
    want_s = (subj == "sg")
    good_has_s = s_g
    return "g" if good_has_s == want_s else "b"

files = sorted(glob.glob("/home/claude/blimp/data/*.jsonl"))
lm_big = build_lm("/home/claude/elfix/Elfix/data/corpus_big.txt")
lp = scorer(lm_big)

results = {}
for f in files:
    name = f.split("/")[-1][:-6]
    ok = n = 0
    reg_ok = reg_n = 0
    is_dn = name.startswith("determiner_noun")
    is_sv = "subject_verb" in name or name.startswith("distractor_agreement")
    for line in open(f):
        d = json.loads(line)
        g, b = d["sentence_good"], d["sentence_bad"]
        pick = None
        if is_dn:
            j = lesson_judge(toks(g), toks(b))
            if j: pick = j; reg_n += 1; reg_ok += int(j == "g")
        elif is_sv:
            j = sv_judge(g, b)
            if j: pick = j; reg_n += 1; reg_ok += int(j == "g")
        if pick is None:
            pick = "g" if lp(toks(g)) >= lp(toks(b)) else "b"
        ok += int(pick == "g"); n += 1
    results[name] = (ok / n * 100, reg_n, (reg_ok / reg_n * 100 if reg_n else 0))

tri_only = {}
for f in files:
    name = f.split("/")[-1][:-6]
    if name.startswith("determiner_noun") or "subject_verb" in name or name.startswith("distractor_agreement"):
        ok = n = 0
        for line in open(f):
            d = json.loads(line)
            ok += int(lp(toks(d["sentence_good"])) >= lp(toks(d["sentence_bad"]))); n += 1
        tri_only[name] = ok / n * 100

overall = np.mean([v[0] for v in results.values()])
print(f"OVERALL (67 paradigms, register+lesson where applicable): {overall:.1f}%")
print("\nagreement paradigms — trigram-only vs +register/lesson (coverage):")
for name in sorted(tri_only):
    full, cov_n, cov_acc = results[name]
    print(f"  {name[:44]:44s} {tri_only[name]:5.1f} -> {full:5.1f}   (judged {cov_n}, {cov_acc:.0f}%)")
tri_overall = np.mean([tri_only.get(k, v[0]) for k, v in results.items()])
print(f"\ntrigram-only overall: {tri_overall:.1f}%")
