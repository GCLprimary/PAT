"""Probe 26: RULE INDUCTION — learn the allomorph choice from counts.
Signature of the base's FINAL segment (kind, manner, place, voiced) ->
allomorph class, learned as an argmax count table on a 60% train split,
tested on 40%. Compare to the hand rule (99.1 / 99.4) and print the
learned table: the rule should be READABLE and rediscover phonology.
"""
import sys, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import features

corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2: corpus[p[0]] = tuple(p[1:])

def sig(ph):
    f = features(ph)
    kind = str(getattr(f, "kind", "?"))
    if kind == "vowel": return ("vowel", "-", "-", "V+")
    return (kind, str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")),
            "V+" if getattr(f, "voiced", False) else "V-")

def classify_remainder(rem, kind):
    toks = [t.lower() for t in rem]
    if kind == "s":
        if len(rem) >= 2 and toks[-1] == "z": return "epen_z"
        if toks == ["z"]: return "z"
        if toks == ["s"]: return "s"
    else:
        if len(rem) >= 2 and toks[-1] == "d": return "epen_d"
        if toks == ["d"]: return "d"
        if toks == ["t"]: return "t"
    return None

for sfx in ("s", "ed"):
    gold = []
    for w in corpus:
        if w.endswith(sfx) and len(w) > len(sfx) + 2:
            base = w[:-len(sfx)]
            if base in corpus:
                B, W = corpus[base], corpus[w]
                if len(W) > len(B) and W[:len(B)] == B:
                    c = classify_remainder(W[len(B):], sfx)
                    if c: gold.append((sig(B[-1]), c))
    rng = np.random.default_rng(7)
    rng.shuffle(gold)
    cut = int(len(gold) * 0.6)
    tr, te = gold[:cut], gold[cut:]
    table = defaultdict(Counter)
    for s, c in tr: table[s][c] += 1
    rule = {s: c.most_common(1)[0][0] for s, c in table.items()}
    fallback = Counter(c for _, c in tr).most_common(1)[0][0]
    ok = sum(int(rule.get(s, fallback) == c) for s, c in te)
    print(f"-{sfx}: induced table accuracy {ok/len(te)*100:.1f}%  (n_test={len(te)}, "
          f"{len(rule)} signatures)")
    # readable table, most frequent signatures first
    freq = Counter(s for s, _ in tr)
    for s, _ in freq.most_common(6):
        d = table[s]
        tot = sum(d.values())
        top = d.most_common(1)[0]
        print(f"    {str(s):48s} -> {top[0]:6s} ({top[1]}/{tot})")
    print()
