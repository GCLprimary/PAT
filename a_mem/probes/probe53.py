"""Probe 53: THE HOUSEKEEPING SWEEP (four loose ends, one run).
1 PAGE 6 (gender names, textbook list — grades forecast L5): frame
  subject is a listed name -> himself/herself checked; abstain else.
2 PAGE 7 (past irregulars, textbook): PERF aux + listed past form
  (ate) is a violation where the participle (eaten) exists; also
  overrides UniMorph V;PST before the table.
3 SELECTIVE BLiMP AGGREGATE: judged coverage + judged accuracy over
  all 67 paradigms — the entry card's missing number.
4 QUANTIFIERS_2: print two pairs; certify the abstention or extend.
"""
import json, glob, warnings
import numpy as np
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe45.py").read().split("files = sorted")[0])

FEM = set("""karla sarah maria anna emily alice carol diane donna ellen gina helen
irene janet karen laura linda megan nancy pamela rachel susan tina wendy amy beth
claire dana erica fiona katherine catherine elizabeth margaret patricia barbara
jennifer jessica ashley amanda stephanie melissa nicole heather michelle kimberly
lisa angela cynthia deborah sharon kathleen ruth carrie julia grace rose lucy
martha ann anne marie diana carla monica veronica valerie natalie vanessa
christine rebecca laurie leslie dawn april tanya sonia rita gloria""".split())
MASC = set("""john james robert michael william david richard joseph thomas charles
daniel matthew mark paul steven kevin brian george edward ronald kenneth adam alan
bruce carl dennis eric frank gary henry christopher anthony donald andrew joshua
kyle brandon jacob ryan justin scott gregory jeffrey stephen timothy jose larry
jerry patrick sean carlos raymond douglas peter walter harold roger keith samuel
benjamin lawrence nicholas todd craig alexander jonathan philip leonard bradley
travis marcus victor martin derek clifford""".split())
def name_gender(ws):
    for w in ws:
        if w in FEM: return "f"
        if w in MASC: return "m"
    return None
def gender_pick(g, b):
    ta = [w.lower().strip('.,!?;:') for w in toks(g)]; tb = [w.lower().strip('.,!?;:') for w in toks(b)]
    if len(ta) != len(tb): return None
    ks = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
    if len(ks) != 1: return None
    x, y = ta[ks[0]], tb[ks[0]]
    if {x, y} != {"himself", "herself"}: return None
    ge = name_gender(ta)
    if ge is None: return None
    want = "herself" if ge == "f" else "himself"
    return "g" if x == want else "b"

P2 = {"wear":("wore","worn"),"hide":("hid","hidden"),"eat":("ate","eaten"),
 "take":("took","taken"),"give":("gave","given"),"write":("wrote","written"),
 "speak":("spoke","spoken"),"break":("broke","broken"),"drive":("drove","driven"),
 "ride":("rode","ridden"),"rise":("rose","risen"),"fall":("fell","fallen"),
 "grow":("grew","grown"),"know":("knew","known"),"throw":("threw","thrown"),
 "fly":("flew","flown"),"draw":("drew","drawn"),"begin":("began","begun"),
 "drink":("drank","drunk"),"swim":("swam","swum"),"ring":("rang","rung"),
 "sink":("sank","sunk"),"sing":("sang","sung"),"see":("saw","seen"),
 "go":("went","gone"),"do":("did","done"),"choose":("chose","chosen"),
 "freeze":("froze","frozen"),"steal":("stole","stolen"),"forget":("forgot","forgotten"),
 "forgive":("forgave","forgiven"),"mistake":("mistook","mistaken"),
 "shake":("shook","shaken"),"tear":("tore","torn"),"bite":("bit","bitten"),
 "beat":("beat","beaten"),"come":("came","come"),"run":("ran","run")}
PAIRSET = {frozenset(v) for v in P2.values() if v[0] != v[1]}
PPARTS = {v[1] for v in P2.values()}
DETS = {"the","a","an","this","that","these","those","some","every","each",
        "all","most","many","his","her","its","their","any","no"}
AUXES = {"has","have","had","is","are","was","were","be","been","being","get","got"}
def ppart_pick(g, b):
    ta = [w.lower().strip('.,!?;:') for w in toks(g)]; tb = [w.lower().strip('.,!?;:') for w in toks(b)]
    if len(ta) != len(tb): return None
    ks = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
    if len(ks) != 1: return None
    k = ks[0]; x, y = ta[k], tb[k]
    if frozenset((x, y)) not in PAIRSET: return None
    prenominal = k >= 1 and ta[k-1] in DETS
    aux_near = any(w in AUXES for w in ta[max(0, k-3):k])
    if prenominal and not aux_near:
        want_ppart = True
    elif not aux_near:
        want_ppart = False
    else:
        return None
    x_is_ppart = x in PPARTS and x not in {p for p, q in P2.values() if p != q}
    return ("g" if x_is_ppart == want_ppart else "b")

PAST_IRR = {"go":"went","eat":"ate","sing":"sang","see":"saw","take":"took",
    "give":"gave","come":"came","run":"ran","write":"wrote","speak":"spoke",
    "break":"broke","drive":"drove","ride":"rode","rise":"rose","fall":"fell",
    "grow":"grew","know":"knew","throw":"threw","fly":"flew","draw":"drew",
    "begin":"began","drink":"drank","swim":"swam","ring":"rang","sink":"sank",
    "sit":"sat","stand":"stood","win":"won","find":"found","hold":"held",
    "tell":"told","sell":"sold","buy":"bought","bring":"brought","think":"thought",
    "teach":"taught","catch":"caught","fight":"fought","seek":"sought",
    "leave":"left","keep":"kept","sleep":"slept","feel":"felt","meet":"met",
    "lead":"led","read":"read","say":"said","make":"made","hear":"heard"}
PPART = {"go":"gone","eat":"eaten","sing":"sung","see":"seen","take":"taken",
    "give":"given","come":"come","write":"written","speak":"spoken",
    "break":"broken","drive":"driven","ride":"ridden","rise":"risen",
    "fall":"fallen","grow":"grown","know":"known","throw":"thrown",
    "fly":"flown","draw":"drawn","begin":"begun","drink":"drunk","swim":"swum",
    "ring":"rung","sink":"sunk","run":"run"}
PERF = {"has", "have", "had"}
PAST_ONLY = set(PAST_IRR.values()) - set(PPART.values())
def perf_viol(ws):
    ws = [w.lower() for w in ws]
    for i, w in enumerate(ws[:-1]):
        if w in PERF:
            for j in (i + 1, i + 2, i + 3):
                if j < len(ws):
                    if ws[j] in PAST_ONLY: return 1
                    if ws[j] in set(PPART.values()): return 0
    return None

files = sorted(glob.glob("/home/claude/blimp/data/*.jsonl"))
GEN = ("anaphor_gender_agreement",)
IRRV = ("irregular_past_participle_verbs", "irregular_past_participle_adjectives")
results = {}
for f in files:
    name = f.split("/")[-1][:-6]
    tok_ok = full_ok = n = jn = jok = 0
    is_dn = name.startswith("determiner_noun")
    is_sv = "subject_verb" in name or name.startswith("distractor_agreement")
    pj = (reflexive_viol if name in PAGE3 else quant_viol if name in PAGE4 else
          npi_viol if name in PAGE5 else None)
    direct = gender_pick if name in GEN else ppart_pick if name in IRRV else None
    for line in open(f):
        d = json.loads(line)
        g, b = d["sentence_good"], d["sentence_bad"]
        tpick = "g" if lp(toks(g)) >= lp(toks(b)) else "b"
        pick = None
        if is_dn: pick = lesson_judge(toks(g), toks(b))
        elif is_sv: pick = sv_judge(g, b)
        elif direct: pick = direct(g, b)
        elif pj: pick = page_judge(pj, g, b)
        if pick is not None: jn += 1; jok += int(pick == "g")
        else: pick = tpick
        tok_ok += int(tpick == "g"); full_ok += int(pick == "g"); n += 1
    results[name] = (tok_ok / n * 100, full_ok / n * 100, jn, jok, n)

overall = np.mean([v[1] for v in results.values()])
tj = sum(v[2] for v in results.values()); tk = sum(v[3] for v in results.values())
tp = sum(v[4] for v in results.values())
print(f"FORCED overall (7 pages): {overall:.2f}  (was 64.79 at 5 pages)")
print(f"SELECTIVE AGGREGATE: judged {tj}/{tp} = {tj/tp*100:.1f}% coverage, "
      f"accuracy on judged {tk/tj*100:.2f}%")
for name in GEN + IRRV:
    t, fu, jn, jok, n = results[name]
    print(f"  {name[:40]:40s} {t:5.1f} -> {fu:5.1f}  ({jn} judged @ {jok/max(jn,1)*100:.0f}%)")

for line in open("/home/claude/blimp/data/existential_there_quantifiers_2.jsonl"):
    d = json.loads(line)
    print("Q2 sample:", d["sentence_good"], "||", d["sentence_bad"])
    break

# UniMorph V;PST with the page riding first
from collections import defaultdict as dd, Counter as Ctr
import random
VOW = set("aeiou")
def uclassify(base, word):
    if word == base + "ed": return "ed"
    if base.endswith("e") and word == base + "d": return "d"
    if base.endswith("y") and word == base[:-1] + "ied": return "ied"
    if len(base) >= 2 and word == base + base[-1] + "ed": return "Ced"
    return None
def usig(base):
    prev = "V" if len(base) > 1 and base[-2] in VOW else "C"
    pprev = "V" if len(base) > 2 and base[-3] in VOW else "C"
    return (pprev + prev, base[-1])
gold = dd(dict)
for line in open("/home/claude/unimorph_eng/eng"):
    p = line.rstrip("\n").split("\t")
    if len(p) == 3 and p[2] == "V;PST": gold[p[0]] = p[1]
lem = [l for l in gold if l.isalpha() and l.islower() and 3 <= len(l) <= 12]
random.Random(7).shuffle(lem)
cut = int(len(lem) * 0.8); train, test = lem[:cut], lem[cut:cut + 3000]
T = dd(Ctr)
for l in train:
    c = uclassify(l, gold[l])
    if c: T[usig(l)][c] += 1
def uapply(l):
    if l in PAST_IRR: return PAST_IRR[l]
    d = T.get(usig(l))
    if not d: return None
    c = d.most_common(1)[0][0]
    return {"ed": l+"ed", "d": l+"d", "ied": l[:-1]+"ied", "Ced": l+l[-1]+"ed"}[c]
ok = wr = ref = 0
for l in test:
    p = uapply(l)
    if p is None: ref += 1
    elif p == gold[l]: ok += 1
    else: wr += 1
print(f"\nUniMorph V;PST with page 7 riding first: {ok}/{ok+wr+ref} = "
      f"{ok/(ok+wr+ref)*100:.1f}% forced (was 90.6 table-only); wrong {wr}, refused {ref}")
