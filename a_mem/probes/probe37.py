"""Probe 37: THE ENGLISH TEST. Subject-verb number agreement on real
sentences, attractor-split (Linzen-style).
Lexicons: sg = mined -s bases, pl = their derived forms (probe-19 pairs).
Pattern: DET N ... V within 12 tokens, V in {is,are,was,were,has,have,does,do}.
Attractor case: an opposite-number noun strictly between subject and verb.
Models: trigram (train counts, backoff bigram) | most-recent-noun | REGISTER
(first DET-N opens, held to verb). Test on the held 5% split only.
"""
import warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

SG_LEX = set(); PL_LEX = set()
for base, sfx, w, rem in pairs:
    if sfx == "s":
        SG_LEX.add(base); PL_LEX.add(w)
AMBIG = SG_LEX & PL_LEX
SG_LEX -= AMBIG; PL_LEX -= AMBIG
print(f"number lexicon: {len(SG_LEX)} singular, {len(PL_LEX)} plural ({len(AMBIG)} ambiguous dropped)")

SG_V = {"is", "was", "has", "does"}; PL_V = {"are", "were", "have", "do"}
DET = {"the", "a", "an", "this", "that", "these", "those", "all", "some", "his", "her", "their", "its", "our", "my"}

sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt") if len(l.split()) >= 6]
rng = np.random.default_rng(5)
idx = rng.permutation(len(sents))
cut = int(len(sents) * 0.95)
train = [sents[i] for i in idx[:cut]]
held = [sents[i] for i in idx[cut:]]

bi, tri = defaultdict(Counter), defaultdict(Counter)
for s in train:
    for a, b in zip(s, s[1:]): bi[a][b] += 1
    for a, b, c in zip(s, s[1:], s[2:]): tri[(a, b)][c] += 1

def num_of(w):
    if w in SG_LEX: return "sg"
    if w in PL_LEX: return "pl"
    return None

cases = []
for s in held:
    for k in range(len(s) - 2):
        if s[k] in DET and num_of(s[k + 1]):
            subj_i = k + 1; subj_n = num_of(s[subj_i])
            for j in range(subj_i + 1, min(subj_i + 13, len(s))):
                if s[j] in SG_V or s[j] in PL_V:
                    gold = "sg" if s[j] in SG_V else "pl"
                    between = s[subj_i + 1:j]
                    nouns_between = [(t, num_of(t)) for t in between if num_of(t)]
                    attractor = any(n != subj_n for _, n in nouns_between)
                    cases.append((s, subj_i, j, subj_n, gold, attractor, nouns_between))
                    break
            break
print(f"mined {len(cases)} agreement cases from held split "
      f"({sum(c[5] for c in cases)} with opposite-number attractors)")

def predict_trigram(s, j):
    ctx2 = (s[j - 2], s[j - 1]) if j >= 2 else None
    best, bn = None, -1
    for v in SG_V | PL_V:
        c = tri[ctx2][v] if ctx2 in tri else 0
        if c == 0 and s[j - 1] in bi: c = 0.1 * bi[s[j - 1]][v]
        if c > bn: bn, best = c, v
    if best is None: return None
    return "sg" if best in SG_V else "pl"

def predict_recent(s, subj_i, j, subj_n, nouns_between):
    return nouns_between[-1][1] if nouns_between else subj_n

results = {"trigram": [[0, 0], [0, 0]], "recent-noun": [[0, 0], [0, 0]], "REGISTER": [[0, 0], [0, 0]]}
for s, subj_i, j, subj_n, gold, attractor, nb in cases:
    a = int(attractor)
    p = predict_trigram(s, j)
    if p is not None:
        results["trigram"][a][0] += int(p == gold); results["trigram"][a][1] += 1
    p = predict_recent(s, subj_i, j, subj_n, nb)
    results["recent-noun"][a][0] += int(p == gold); results["recent-noun"][a][1] += 1
    results["REGISTER"][a][0] += int(subj_n == gold); results["REGISTER"][a][1] += 1

print("\naccuracy               no-attractor        attractor-present")
for m, ((c0, n0), (c1, n1)) in results.items():
    print(f"  {m:12s}      {c0}/{n0} = {c0/max(n0,1)*100:3.0f}%        {c1}/{n1} = {c1/max(n1,1)*100:3.0f}%")
