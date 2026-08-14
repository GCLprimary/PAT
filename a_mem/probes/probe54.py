"""Probe 54: FRAME DEPTH-2 (the longest-waiting tine).
The clause organ, minimal and exact:
  SUBJECT = an NP (det/quant [adj] noun | name | pronoun) whose next
    token is a verb/aux — a subject is an NP that LAUNCHES A
    PREDICATION.
  RELATIVE MASK = 'that/who/which' whose PRECEDING token ends a noun
    NP: the span through the relative's verb (+ optional object NP)
    is bracketed out; the head noun keeps the floor.
  ANTECEDENT(reflexive) = the last unmasked subject to its left.
  phi-check: number (lexicon + pages) always; gender (names page,
    pronouns) when known; abstain when undecidable.
Judges: depth2_viol -> principle_A_{c_command, domain_1/2/3} +
anaphor_number; sva2_pick (noun-side diff, verb-number constant) ->
irregular_plural_SVA_2 (+_1 no-harm). Grades forecast F1 and F2.
"""
import json, glob, warnings
import numpy as np
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe53.py").read().split("files = sorted(glob")[0])
GEN = ("anaphor_gender_agreement",)
_p19 = open("/home/claude/probe/probe19.py").read().split("from amem.api")[0]
_ns = {}
exec(_p19, _ns)
from collections import defaultdict as _dd
_byb = _dd(dict)
for _b, _s, _w, _r in _ns["pairs"]:
    _byb[_b][_s] = _w
VERBS = set()
for _b, _d in _byb.items():
    if "ed" in _d or "ing" in _d:
        VERBS.add(_b)
        if "s" in _d: VERBS.add(_d["s"])
        VERBS |= {v for k, v in _d.items() if k in ("ed", "ing", "s")}
VERBS |= set(PAST_IRR) | set(PAST_IRR.values()) | set(PPART.values())
VERBS |= {"think", "thinks", "imagine", "imagines", "imagined", "say", "says",
          "explain", "explains", "reveal", "reveals", "notice", "notices"}

IRRV = ("irregular_past_participle_verbs", "irregular_past_participle_adjectives")

PRON_SUBJ = {"he": ("m", "sg"), "she": ("f", "sg"), "it": ("n", "sg"),
             "they": (None, "pl"), "i": (None, "sg"), "we": (None, "pl"),
             "you": (None, None)}
DET2 = DETS | {"one", "two", "three", "several", "few", "both"}
AUX_SG = {"is", "isn't", "was", "wasn't", "has", "hasn't", "does", "doesn't"}
AUX_PL = {"are", "aren't", "were", "weren't", "have", "haven't", "do", "don't"}
VERBISH = AUX_SG | AUX_PL | AUXES | set(PAST_IRR.values()) | set(PPART.values()) | \
    {"can", "could", "will", "would", "may", "might", "must", "should",
     "can't", "won't", "wouldn't", "couldn't"}
STOPW = {"that", "who", "which", "and", "or", "but", "of", "in", "on", "at",
         "to", "from", "with", "about", "for", "by", "not"}
def is_verbish(w):
    if w in VERBISH or w in VERBS or w.endswith("ing") or w.endswith("ed"):
        return True
    if w in STOPW or w in DET2 or w in PRON_SUBJ or w in REFL: return False
    if w in FEM or w in MASC: return False
    if w.endswith("s") and not w.endswith("ss") and w[:-1] in VERBS: return True
    if num_of(w) is not None: return False
    return w.isalpha()
REFL = {"himself": ("m", "sg"), "herself": ("f", "sg"),
        "itself": ("n", "sg"), "themselves": (None, "pl")}
def np_at(ws, i):
    """NP starting at i -> (end_index_exclusive, phi) or None."""
    if ws[i].lower() in DET2:
        ws = list(ws); ws[i] = ws[i].lower()
    wl = ws[i].lower()
    if wl in PRON_SUBJ and wl != "you":
        return i + 1, PRON_SUBJ[wl]
    j = i
    if ws[j].lower() in DET2:
        j += 1
        last = None
        limit = 7
        while j < len(ws) and j - i <= limit:
            wj = ws[j].lower()
            if wj == "of" and last is not None:
                j += 1; continue
            if wj in STOPW or wj in VERBS or \
                    (is_verbish(wj) and num_of(wj) is None):
                break
            if num_of(wj) is not None: last = j
            j += 1
        if last is not None:
            return last + 1, (None, num_of(ws[last].lower()))
        return None
    if wl in FEM: return i + 1, ("f", "sg")
    if wl in MASC: return i + 1, ("m", "sg")
    if ws[i][:1].isupper() and wl not in DET2 and wl not in STOPW \
            and wl not in VERBISH and wl not in VERBS \
            and num_of(wl) is None and wl not in REFL:
        return i + 1, (None, "sg")            # unlisted NAME by capitalization
    return None

def clause_map(ws):
    """subjects: list of (np_end, phi) unmasked; relative spans masked."""
    masked = [False] * len(ws)
    for k, w in enumerate(ws):
        if w.lower() in ("that", "who", "which") and k >= 1:
            prev_np = any(np_at(ws, s) and np_at(ws, s)[0] == k
                          for s in range(max(0, k - 4), k))
            if prev_np:
                j = k + 1
                while j < len(ws) and not is_verbish(ws[j].lower()): j += 1
                if j < len(ws):
                    j += 1
                    r = np_at(ws, j) if j < len(ws) else None
                    if r: j = r[0]
                    for m in range(k, min(j, len(ws))): masked[m] = True
    subs = []
    i = 0
    while i < len(ws):
        if not masked[i]:
            r = np_at(ws, i)
            if r and r[0] < len(ws):
                nxt = r[0]
                while nxt < len(ws) and masked[nxt]: nxt += 1
                if nxt < len(ws) and is_verbish(ws[nxt].lower()) and ws[nxt].lower() not in REFL:
                    subs.append((r[0], r[1])); i = r[0]; continue
        i += 1
    return subs

def resolve_local(ws, ri):
    # 1) relativizer-head override: NP ending exactly at a rel-word left of refl
    for k in range(ri - 1, 0, -1):
        if ws[k].lower() in ("that", "who", "which"):
            for s in range(max(0, k - 8), k):
                r = np_at(ws, s)
                if r and r[0] == k:
                    return r[1]
            break
    # 2) walk left from the reflexive through the verb cluster
    i = ri - 1
    NEG = {"didn't", "doesn't", "don't", "not", "n't", "won't", "can't",
           "wasn't", "isn't", "aren't", "weren't", "couldn't", "wouldn't"}
    while i >= 0:
        w = ws[i].lower()
        prev = ws[i - 1].lower() if i >= 1 else ""
        if num_of(w) is not None and (prev in DET2 or prev == "of"
                                      or num_of(prev) is not None):
            for s in range(max(0, i - 7), i + 1):
                r = np_at(ws, s)
                if r and r[0] == i + 1:
                    return r[1]
            return (None, num_of(w))
        if w in FEM: return ("f", "sg")
        if w in MASC: return ("m", "sg")
        if ws[i][:1].isupper() and i > 0 and w not in DET2 and w not in STOPW \
                and w not in VERBS and num_of(w) is None:
            return (None, "sg")
        if w in PRON_SUBJ and w != "you": return PRON_SUBJ[w]
        if is_verbish(w) or w in NEG or w in STOPW or w in DET2:
            i -= 1; continue
        i -= 1
    return None

def depth2_viol(ws):
    ws = [w.strip(".,!?;:") for w in ws]
    ri = next((i for i, w in enumerate(ws) if w.lower() in REFL), None)
    if ri is None: return 0
    rg, rn = REFL[ws[ri].lower()]
    phi = resolve_local(ws, ri)
    if phi is None: return None
    sg_, sn = phi
    if sn is None: return None
    if sn != rn: return 1
    if rg and sg_ and rg != sg_: return 1
    if rg in ("m", "f") and sg_ is None: return None
    return 0

def verb_number(ws, j):
    for w in ws[j:j + 3]:
        w = w.strip(".,!?;:")
        if w in AUX_SG: return "sg"
        if w in AUX_PL: return "pl"
        if is_verbish(w):
            if w.endswith("s") and not w.endswith("ss"): return "sg"
            if not w.endswith("ing") and not w.endswith("ed"): return "pl"
    return None

def sva2_pick(g, b):
    ta = [w.lower().strip(".,!?;:") for w in toks(g)]
    tb = [w.lower().strip(".,!?;:") for w in toks(b)]
    if len(ta) != len(tb): return None
    ks = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
    if len(ks) != 1: return None
    k = ks[0]
    na, nb = num_of(ta[k]), num_of(tb[k])
    if not na or not nb or na == nb: return None
    vn = verb_number(ta, k + 1)
    if vn is None: return None
    return "g" if na == vn else "b"

D2 = ("principle_A_c_command", "principle_A_domain_1", "principle_A_domain_2",
      "principle_A_domain_3", "anaphor_number_agreement")
SVA2 = ("irregular_plural_subject_verb_agreement_2",)

files = sorted(glob.glob("/home/claude/blimp/data/*.jsonl"))
results = {}
for f in files:
    name = f.split("/")[-1][:-6]
    tok_ok = full_ok = n = jn = jok = 0
    is_dn = name.startswith("determiner_noun")
    is_sv = ("subject_verb" in name and name not in SVA2) or \
        name.startswith("distractor_agreement")
    pj = (quant_viol if name in PAGE4 else npi_viol if name in PAGE5 else
          depth2_viol if name in D2 else
          reflexive_viol if name in PAGE3 else None)
    direct = (gender_pick if name in GEN else ppart_pick if name in IRRV else
              sva2_pick if name in SVA2 else None)
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
print(f"FORCED overall (depth-2): {overall:.2f}   (Part XI shipped 65.93)")
print(f"SELECTIVE: {tj}/67000 = {tj/670:.1f}% @ {tk/tj*100:.2f}%")
print("\nparadigm                                  tri -> now   (judged @ acc)   Part XI")
PREV = {"principle_A_c_command": 64.9, "principle_A_domain_1": 97.1,
        "principle_A_domain_2": 41.9, "principle_A_domain_3": 83.9,
        "anaphor_number_agreement": 66.8,
        "irregular_plural_subject_verb_agreement_2": 53.2,
        "irregular_plural_subject_verb_agreement_1": 70.1}
for name in D2 + SVA2:
    t, fu, jn, jok, n = results[name]
    print(f"  {name[:40]:40s} {t:5.1f} -> {fu:5.1f}  ({jn:4d} @ {jok/max(jn,1)*100:5.1f}%)  was {PREV.get(name,'?')}")
