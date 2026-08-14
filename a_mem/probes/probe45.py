"""Probe 45: PAGES 3-5 and THE LIBRARY CURVE.
Page 3 REFLEXIVES: himself/herself/itself <- sg antecedent, themselves <- pl.
Page 4 QUANTIFIERS: existential 'there' forbids strong quantifiers
       (each/every/all/most/both).
Page 5 NPI: 'ever/any...' require a licensor (negation, 'only', question).
Judges abstain outside their rule (both-violate or neither -> None), so
the judges-don't-leak law holds by construction. Same run reports
trigram-only vs schooled per affected paradigm + the cumulative curve:
pages 0 -> 2 -> 5.
"""
import json, glob, re, warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe43.py").read().split("BEFORE = {")[0])

REFL_SG = {"himself", "herself", "itself", "oneself"}
REFL_PL = {"themselves"}
QUANT_STRONG = {"each", "every", "all", "most", "both"}
BE = {"is", "are", "was", "were"}
NPI = {"ever", "any", "anybody", "anyone", "anything"}
LICENSOR = {"not", "no", "never", "only", "nobody", "none", "nothing",
            "neither", "whether", "hardly", "rarely", "seldom", "without"}
AUX_Q = {"has", "have", "had", "do", "does", "did", "is", "are", "was",
         "were", "can", "could", "will", "would", "should", "might"}

def reflexive_viol(ws):
    """Antecedent = the STRICT FRAME subject only (law: a page without
    structure is seduction with extra steps); anything else ABSTAINS.
    The nearest-prior-noun version scored 20% judged on
    principle_A_c_command — the recent-noun baseline in disguise."""
    refl = None
    for w in ws:
        if w in REFL_SG or w in REFL_PL:
            refl = w; break
    if refl is None: return None
    if len(ws) >= 2 and ws[0] in {"the","a","an","this","that","these",
                                  "those","most","many","all","some",
                                  "no","each","every"}:
        n = num_of(ws[1])
        if n is None and ws[0] in {"these","those","most","many","all",
                                   "some"} and ws[1].endswith("s"):
            n = "pl"
        if ws[0] in {"each","every"}: n = "sg"
        if n:
            want = "sg" if refl in REFL_SG else "pl"
            return 0 if n == want else 1
    return None

def quant_viol(ws):
    for i, w in enumerate(ws[:-2]):
        if w == "there" and ws[i + 1] in BE:
            j = i + 2
            if ws[j] in ("only",): j += 1
            return 1 if ws[j] in QUANT_STRONG else 0
    return None

def npi_viol(ws):
    has_npi = any(w.strip("'") in NPI for w in ws)
    if not has_npi: return 0
    licensed = (ws[0] in AUX_Q) or any(
        w in LICENSOR or w.endswith("n't") for w in ws)
    return 0 if licensed else 1

def page_judge(viol_fn, g, b):
    vg, vb = viol_fn(toks(g)), viol_fn(toks(b))
    if vg is None or vb is None or vg == vb: return None
    return "g" if vg < vb else "b"

PAGE3 = ("anaphor_number_agreement", "principle_A_c_command",
         "principle_A_domain_1", "principle_A_domain_2", "principle_A_domain_3",
         "principle_A_case_1", "principle_A_case_2", "principle_A_reconstruction",
         "anaphor_gender_agreement")
PAGE4 = ("existential_there_quantifiers_1", "existential_there_quantifiers_2")
PAGE5 = ("npi_present_1", "npi_present_2",
         "sentential_negation_npi_licensor_present",
         "only_npi_licensor_present", "matrix_question_npi_licensor_present",
         "only_npi_scope", "sentential_negation_npi_scope")

files = sorted(glob.glob("/home/claude/blimp/data/*.jsonl"))
results = {}
for f in files:
    name = f.split("/")[-1][:-6]
    tok_ok = full_ok = n = jn = jok = 0
    is_dn = name.startswith("determiner_noun")
    is_sv = "subject_verb" in name or name.startswith("distractor_agreement")
    pj = (reflexive_viol if name in PAGE3 else
          quant_viol if name in PAGE4 else
          npi_viol if name in PAGE5 else None)
    for line in open(f):
        d = json.loads(line)
        g, b = d["sentence_good"], d["sentence_bad"]
        tri_pick = "g" if lp(toks(g)) >= lp(toks(b)) else "b"
        pick = None
        if is_dn: pick = lesson_judge(toks(g), toks(b))
        elif is_sv: pick = sv_judge(g, b)
        elif pj: pick = page_judge(pj, g, b)
        if pick is not None: jn += 1; jok += int(pick == "g")
        else: pick = tri_pick
        tok_ok += int(tri_pick == "g"); full_ok += int(pick == "g"); n += 1
    results[name] = (tok_ok / n * 100, full_ok / n * 100, jn, jok / jn * 100 if jn else 0)

overall_tri = np.mean([v[0] for v in results.values()])
overall = np.mean([v[1] for v in results.values()])
print(f"LIBRARY CURVE  pages=0: {overall_tri:.1f}   pages=2: 60.5 (probe 43)   pages=5: {overall:.2f}")
print("\nnew-page paradigms                                tri -> schooled  (judged, acc)")
for grp, label in ((PAGE3, "P3"), (PAGE4, "P4"), (PAGE5, "P5")):
    for name in grp:
        if name not in results: print(f"  !! missing {name}"); continue
        t, fu, jn, ja = results[name]
        print(f"  {label} {name[:44]:44s} {t:5.1f} -> {fu:5.1f}  ({jn}, {ja:.0f}%)")
