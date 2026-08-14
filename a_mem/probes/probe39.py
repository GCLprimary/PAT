"""Probe 39: THE PHON GATE (two mechanisms, from the measured window).
Gate = stem-scoped phon identity (theta_p = 0.77) + remainder-in-attested-
allomorph-set-of-proposed-suffix arbitration.
A) imposter kill: colliding pair (B1,B2 same shape), only B1 known; attack
   with W2 = B2+sfx. Shape accepts (ceiling 1.0); gate must refuse.
B) true tax: W1 = B1+sfx true accepts under stem gate vs BLUNT whole-word
   gate at 0.85 (window predicted ~12.5% blunt tax, ~0 stem tax).
C) disambiguation: B1 AND B2 both known; shape ties at 1.0; stem-phon
   argmax must attribute W2 to B2.
D) wrong-suffix: propose (B, sfx_wrong) for obs = B+sfx_right; remainder
   arbitration must reject.
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    byb[base][sfx] = (w, tuple(rem))
attested = defaultdict(set)
for base, sfx, w, rem in pairs:
    attested[sfx].add(tuple(rem))

def shape_key(b): return tuple(str(x) for p in corpus[b] for x in ([('V',)] if False else []) ) # placeholder
# real shape key:
import sys
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features as feat
def shp(p):
    f = feat(p)
    if str(getattr(f, "kind", "?")) == "vowel": return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
def skey(b): return tuple(shp(p) for p in corpus[b])

groups = defaultdict(list)
for b in byb:
    groups[skey(b)].append(b)
coll = [g for g in groups.values() if len(g) >= 2]
print(f"collision groups among suffixed bases: {len(coll)}")

def phonvec(seq): return vec(seq, "phon")
TH_P = 0.77

def stem_gate(obs_pron, base):
    L = len(corpus[base])
    if len(obs_pron) < L: return False, 0.0
    c = float(phonvec(obs_pron[:L]) @ phonvec(corpus[base]))
    return c >= TH_P, c

def arbitrate(obs_pron, base, sfx):
    L = len(corpus[base])
    return tuple(obs_pron[L:]) in attested[sfx]

rng = np.random.default_rng(9)
# build attack/true/disamb sets
attacks, trues, disamb = [], [], []
for g in coll:
    rng.shuffle(g)
    for i in range(len(g) - 1):
        B1, B2 = g[i], g[i + 1]
        if corpus[B1] == corpus[B2]: continue     # true homophones: out of scope
        for sfx, (w2, rem2) in byb[B2].items():
            if sfx in byb.get(B1, {}) or sfx in modal_phon:
                attacks.append((B1, B2, sfx, w2)); break
        for sfx, (w1, rem1) in byb[B1].items():
            trues.append((B1, sfx, w1)); break
        disamb.append((B1, B2))
attacks = attacks[:120]; trues = trues[:200]; disamb = disamb[:120]

print("\nA · IMPOSTER KILL (only B1 known; attack = B2's derived form)")
shape_acc = gate_acc = 0
for B1, B2, sfx, w2 in attacks:
    obs = corpus[w2]
    sv = float(vec(obs, "shape") @ predict(corpus[B1], sfx, "shape", "SEAM")) if sfx in modal_phon else 0
    shape_ok = sv >= 0.98
    g_ok, c = stem_gate(obs, B1)
    both = shape_ok and g_ok and arbitrate(obs, B1, sfx)
    shape_acc += int(shape_ok); gate_acc += int(both)
print(f"  shape-only false accepts: {shape_acc}/{len(attacks)}")
print(f"  gated false accepts:      {gate_acc}/{len(attacks)}")

print("\nB · TRUE-ACCEPT TAX (stem gate vs blunt whole-word gate @0.85)")
stem_ok = blunt_ok = n_ep = stem_ep = blunt_ep = 0
for B1, sfx, w1 in trues:
    obs = corpus[w1]
    s_ok, _ = stem_gate(obs, B1)
    s_ok = s_ok and arbitrate(obs, B1, sfx)
    if sfx in modal_phon:
        bw = float(phonvec(obs) @ phonvec(list(corpus[B1]) + list(modal_phon[sfx])))
        b_ok = bw >= 0.85
    else:
        b_ok = False
    ep = len(obs) - len(corpus[B1]) >= 2      # epenthesis-family (2+ phoneme remainder)
    stem_ok += int(s_ok); blunt_ok += int(b_ok)
    if ep: n_ep += 1; stem_ep += int(s_ok); blunt_ep += int(b_ok)
print(f"  stem-scoped true accepts: {stem_ok}/{len(trues)} = {stem_ok/len(trues)*100:.1f}%")
print(f"  blunt-gate true accepts:  {blunt_ok}/{len(trues)} = {blunt_ok/len(trues)*100:.1f}%")
print(f"  epenthesis family (n={n_ep}): stem {stem_ep}/{n_ep}  blunt {blunt_ep}/{n_ep}")

print("\nC · DISAMBIGUATION (both bases known; attribute W2 by stem-phon)")
ok = tot = 0
for B1, B2 in disamb:
    for sfx, (w2, rem2) in byb[B2].items():
        obs = corpus[w2]
        _, c1 = stem_gate(obs, B1); _, c2 = stem_gate(obs, B2)
        ok += int(c2 > c1); tot += 1
        break
print(f"  correct attribution: {ok}/{tot} = {ok/max(tot,1)*100:.1f}%")

print("\nD · WRONG-SUFFIX REJECTION (remainder arbitration)")
ok = tot = 0
for b, d in list(byb.items()):
    if len(d) >= 2:
        sfxs = list(d.keys())
        right, wrong = sfxs[0], sfxs[1]
        obs = corpus[d[right][0]]
        rej = not arbitrate(obs, b, wrong) if tuple(obs[len(corpus[b]):]) not in attested[wrong] else None
        if rej is None: continue
        ok += int(rej); tot += 1
        if tot >= 150: break
print(f"  wrong-suffix proposals rejected: {ok}/{tot} = {ok/max(tot,1)*100:.1f}%")
