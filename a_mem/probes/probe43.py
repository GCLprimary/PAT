"""Probe 43: PAGE #2 — the irregular-plural page (the pure thesis test).
~45 pairs from standard grammar (NOT mined from BLiMP), wired as the LAW
class: page-first for listed words, induced lexicon otherwise, conflicts
ledgered. Rerun the full harness: the four dead/harmed irregular
paradigms must rise, the regulars must not fall, overall must rise.
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

# THE PAGE (textbook irregular plurals; provenance: lesson)
PAGE = {
 "man":"men","woman":"women","child":"children","person":"people","foot":"feet",
 "tooth":"teeth","goose":"geese","mouse":"mice","ox":"oxen","louse":"lice",
 "wife":"wives","knife":"knives","life":"lives","leaf":"leaves","loaf":"loaves",
 "half":"halves","calf":"calves","shelf":"shelves","wolf":"wolves","thief":"thieves",
 "elf":"elves","self":"selves","scarf":"scarves","hoof":"hooves","dwarf":"dwarves",
 "cactus":"cacti","focus":"foci","fungus":"fungi","nucleus":"nuclei","stimulus":"stimuli",
 "alumnus":"alumni","radius":"radii","syllabus":"syllabi","analysis":"analyses",
 "basis":"bases","crisis":"crises","thesis":"theses","hypothesis":"hypotheses",
 "oasis":"oases","axis":"axes","phenomenon":"phenomena","criterion":"criteria",
 "datum":"data","bacterium":"bacteria","curriculum":"curricula","medium":"media",
 "memorandum":"memoranda","appendix":"appendices","index":"indices","matrix":"matrices",
 "vertex":"vertices","cherub":"cherubim",
}
PAGE_SG = set(PAGE); PAGE_PL = set(PAGE.values())
conflicts = [(w, "page:sg", "induced:pl") for w in PAGE_SG & PL_LEX] + \
            [(w, "page:pl", "induced:sg") for w in PAGE_PL & SG_LEX]
print(f"THE PAGE: {len(PAGE)} lines; conflicts with induced lexicon (ledgered): {len(conflicts)}")
for c in conflicts[:5]: print("   conflict:", c)

def toks(s): return re.sub(r"[^a-z' ]", "", s.lower()).split()

def build_lm(path):
    uni, bi, tri = Counter(), defaultdict(Counter), defaultdict(Counter)
    for l in open(path):
        ws = l.split()
        uni.update(ws)
        for a, b in zip(ws, ws[1:]): bi[a][b] += 1
        for a, b, c in zip(ws, ws[1:], ws[2:]): tri[(a, b)][c] += 1
    return uni, bi, tri, sum(uni.values())

uni, bi, tri, tot = build_lm("/home/claude/elfix/Elfix/data/corpus_big.txt")
def lp(ws):
    s = 0.0
    for i, w in enumerate(ws):
        if i >= 2 and (ws[i-2], ws[i-1]) in tri and tri[(ws[i-2], ws[i-1])][w] > 0:
            c = tri[(ws[i-2], ws[i-1])]; s += np.log(c[w] / sum(c.values()))
        elif i >= 1 and ws[i-1] in bi and bi[ws[i-1]][w] > 0:
            c = bi[ws[i-1]]; s += np.log(0.4 * c[w] / sum(c.values()))
        else:
            s += np.log(0.16 * max(uni[w], 0.1) / tot)
    return s

def num_of(w):
    if w in PAGE_SG: return "sg"      # LAW class first for listed words
    if w in PAGE_PL: return "pl"
    if w in SG_LEX: return "sg"
    if w in PL_LEX: return "pl"
    return None

DEMO_SG = {"this", "that"}; DEMO_PL = {"these", "those"}
def lesson_judge(g, b):
    def viol(ws):
        for i, w in enumerate(ws[:-1]):
            if w in DEMO_SG or w in DEMO_PL:
                for j in (i + 1, i + 2, i + 3):
                    if j < len(ws):
                        n = num_of(ws[j])
                        if n:
                            return 0 if n == ("sg" if w in DEMO_SG else "pl") else 1
        return None
    vg, vb = viol(g), viol(b)
    if vg is None or vb is None or vg == vb: return None
    return "g" if vg < vb else "b"

DET = {"the", "a", "an", "this", "that", "these", "those", "some", "all", "most", "many", "each"}
def sv_judge(g, b):
    dg, db = toks(g), toks(b)
    if len(dg) != len(db): return None
    diffs = [i for i, (x, y) in enumerate(zip(dg, db)) if x != y]
    if len(diffs) != 1: return None
    i = diffs[0]
    s_g = dg[i].endswith("s") and not db[i].endswith("s")
    s_b = db[i].endswith("s") and not dg[i].endswith("s")
    if not (s_g or s_b): return None
    subj = None
    for k in range(len(dg) - 1):
        if dg[k] in DET and num_of(dg[k + 1]) and k + 1 < i:
            subj = num_of(dg[k + 1]); break
    if subj is None: return None
    return "g" if (s_g == (subj == "sg")) else "b"

BEFORE = {  # probe-42 measured values for comparison
 "determiner_noun_agreement_irregular_1": 65.7, "determiner_noun_agreement_irregular_2": 59.4,
 "determiner_noun_agreement_with_adj_irregular_1": 60.6, "determiner_noun_agreement_with_adj_irregular_2": 55.3,
 "irregular_plural_subject_verb_agreement_1": 53.6, "irregular_plural_subject_verb_agreement_2": 59.6,
 "determiner_noun_agreement_1": 88.4, "determiner_noun_agreement_2": 85.5,
}
files = sorted(glob.glob("/home/claude/blimp/data/*.jsonl"))
results = {}
for f in files:
    name = f.split("/")[-1][:-6]
    ok = n = jn = jok = 0
    is_dn = name.startswith("determiner_noun")
    is_sv = "subject_verb" in name or name.startswith("distractor_agreement")
    for line in open(f):
        d = json.loads(line)
        g, b = d["sentence_good"], d["sentence_bad"]
        pick = None
        if is_dn:
            j = lesson_judge(toks(g), toks(b))
            if j: pick = j; jn += 1; jok += int(j == "g")
        elif is_sv:
            j = sv_judge(g, b)
            if j: pick = j; jn += 1; jok += int(j == "g")
        if pick is None:
            pick = "g" if lp(toks(g)) >= lp(toks(b)) else "b"
        ok += int(pick == "g"); n += 1
    results[name] = (ok / n * 100, jn, jok / jn * 100 if jn else 0)

overall = np.mean([v[0] for v in results.values()])
print(f"\nOVERALL with the page: {overall:.1f}%   (probe-42: 58.7, trigram-only 56.8)")
print("\nparadigm                                        before -> after   (judged, acc)")
for name in sorted(BEFORE):
    a, jn, jacc = results[name]
    print(f"  {name[:46]:46s} {BEFORE[name]:5.1f} -> {a:5.1f}   ({jn}, {jacc:.0f}%)")
