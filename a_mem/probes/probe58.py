"""Probe 58: THE APOSTROPHE CHANNEL (feasibility numbers for Part XV).
What the pinned corpus already holds: the contraction inventory, the
possessive-'s pair yield under the double-lock, and the remainder's
allomorph split -- which should echo the plural's ruler of thirds
(s / z / IH-z by final phone) if 's is the clitic we think it is.
Case (capitals) is NOT measurable here -- the pinned corpus is
lowercase by vintage; the case census is builder-measured against
raw sources, inequalities in the spec.
"""
import warnings
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"): cnt.update(l.split())

apos = [w for w in corpus if "'" in w]
classes = Counter()
for w in apos:
    for suf in ("n't", "'ll", "'ve", "'re", "'d", "'s", "'m"):
        if w.endswith(suf): classes[suf] += 1; break
    else: classes["other"] += 1
print(f"apostrophe types in lexicon: {len(apos)}; classes: {dict(classes)}")

pairs_s = []
rem_split = Counter()
for w in corpus:
    if not w.endswith("'s") or len(w) < 4: continue
    stem = w[:-2]
    if stem not in corpus or cnt[w] < 2: continue
    wp, sp = tuple(corpus[w]), tuple(corpus[stem])
    if wp[:len(sp)] != sp: continue
    rem = wp[len(sp):]
    pairs_s.append((stem, w, rem))
    rem_split[rem] += 1
print(f"possessive/clitic 's pairs (double-lock, attested>=2): {len(pairs_s)}")
print("remainder allomorph split:", rem_split.most_common(6))
by_final = defaultdict(Counter)
for stem, w, rem in pairs_s:
    by_final[corpus[stem][-1]][rem] += 1
sib = [f for f in by_final if f.lower() in ("s", "z", "sh", "zh", "ch", "jh")]
voiced = [f for f in by_final if f in ("b", "d", "g", "v", "m", "n", "NG", "l", "r", "w") or f.isupper()]
print("modal remainder after sibilants:", Counter(
    {f: by_final[f].most_common(1)[0][0] for f in sib[:4]}))
print("sample voiced-final modal:", [(f, by_final[f].most_common(1)[0][0])
                                     for f in list(voiced)[:4]])
print("\nsample pairs:", [(s, w, " ".join(r)) for s, w, r in pairs_s[:6]])
