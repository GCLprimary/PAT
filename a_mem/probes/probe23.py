"""Probe 23: THE DECODER. Two generator pieces.
A) Round-trip: shape sequence -> bigram/unigram counts -> Eulerian walk(s)
   over the shape multigraph -> reconstructed sequence. Metrics: percent
   reconstructable, percent unique-walk, percent exact with a deterministic
   tie-break. 500 corpus words.
B) Allomorph production: for -s and -ed, choose the surface allomorph from
   the base's FINAL segment via one earned voicing rule (ElfIX features):
     -s : sibilant-final -> epenthetic vowel + z ; voiced -> z ; else s
     -ed: t/d-final     -> epenthetic vowel + d ; voiced -> d ; else t
   Scored vs actual CMU derived remainders on all mined pairs; baseline =
   always the modal allomorph.
"""
import sys, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import sonority, features

corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2:
        corpus[p[0]] = tuple(p[1:])

def shape(ph):
    f = features(ph)
    if str(getattr(f, "kind", "?")) == "vowel":
        return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))

# ── A: Eulerian round-trip ──
def decode_walks(seq_shapes, cap=64):
    """all Eulerian paths consistent with the bigram multiset + start node"""
    edges = Counter(zip(seq_shapes, seq_shapes[1:]))
    start = seq_shapes[0]
    n_edges = sum(edges.values())
    out = []
    def walk(node, used, path):
        if len(out) >= cap: return
        if used == n_edges:
            out.append(tuple(path)); return
        for (a, b), c in sorted(edges.items()):
            if a == node and c > 0:
                edges[(a, b)] -= 1
                path.append(b)
                walk(b, used + 1, path)
                path.pop()
                edges[(a, b)] += 1
    walk(start, 0, [start])
    return out

rng = np.random.default_rng(5)
words = [w for w in corpus if 2 <= len(corpus[w]) <= 12]
sample = [words[i] for i in rng.choice(len(words), 500, replace=False)]
recon = uniq = exact = 0
amb_counts = []
for w in sample:
    ss = [shape(p) for p in corpus[w]]
    walks = decode_walks(ss)
    ok = tuple(ss) in walks
    recon += int(ok)
    uniq += int(len(walks) == 1)
    exact += int(walks and walks[0] == tuple(ss))   # deterministic tie-break = lexicographic first
    amb_counts.append(len(walks))
print("A · ROUND-TRIP (500 words, shape level)")
print(f"   reconstructable (original among walks): {recon/5:.0f}%")
print(f"   unique walk:                            {uniq/5:.0f}%")
print(f"   exact with lexicographic tie-break:     {exact/5:.0f}%")
print(f"   walk count: median {int(np.median(amb_counts))}, p90 {int(np.percentile(amb_counts,90))}, max {max(amb_counts)}")

# ── B: allomorph production ──
def voiced(ph):
    f = features(ph)
    if str(getattr(f, "kind", "?")) == "vowel": return True
    return bool(getattr(f, "voiced", False))

SIBS = {"s","z","sh","zh","ch","jh"}
def sib(ph): return ph.lower() in SIBS
def alveolar_stop(ph): return ph.lower() in {"t","d"}

def rule_s(base_pron):
    last = base_pron[-1]
    if sib(last): return "epen_z"
    return "z" if voiced(last) else "s"

def rule_ed(base_pron):
    last = base_pron[-1]
    if alveolar_stop(last): return "epen_d"
    return "d" if voiced(last) else "t"

def classify_remainder(rem, kind):
    r = [x.lower() if x.isupper() is False else x for x in rem]
    toks = [t.lower() for t in rem]
    if kind == "s":
        if len(rem) >= 2 and toks[-1] == "z": return "epen_z"
        if toks == ["z"]: return "z"
        if toks == ["s"]: return "s"
    else:
        if len(rem) >= 2 and toks[-1] == "d": return "epen_d"
        if toks == ["d"]: return "d"
        if toks == ["t"]: return "t"
    return "other"

print("\nB · ALLOMORPH PRODUCTION (earned voicing rule vs modal baseline)")
for sfx, rule in (("s", rule_s), ("ed", rule_ed)):
    gold = []
    for w in corpus:
        if w.endswith(sfx) and len(w) > len(sfx) + 2:
            base = w[:-len(sfx)]
            if base in corpus:
                B, W = corpus[base], corpus[w]
                if len(W) > len(B) and W[:len(B)] == B:
                    cls = classify_remainder(W[len(B):], sfx)
                    if cls != "other":
                        gold.append((B, cls))
    dist = Counter(c for _, c in gold)
    modal = dist.most_common(1)[0][0]
    base_acc = dist[modal] / len(gold)
    ok = sum(int(rule(B) == c) for B, c in gold)
    print(f"   -{sfx}: n={len(gold)}  allomorph dist {dict(dist)}")
    print(f"        modal baseline {base_acc*100:.0f}%   voicing rule {ok/len(gold)*100:.1f}%")

print("\n   showpieces (bind -> decode -> surface):")
for base, sfx, rule in (("dog","s",rule_s),("cat","s",rule_s),("horse","s",rule_s),
                        ("play","ed",rule_ed),("help","ed",rule_ed),("want","ed",rule_ed)):
    if base in corpus:
        a = rule(corpus[base])
        surface = {"epen_z":"IH z","z":"z","s":"s","epen_d":"IH d","d":"d","t":"t"}[a]
        print(f"   {base}+{sfx} -> {' '.join(corpus[base])} + [{surface}]")
