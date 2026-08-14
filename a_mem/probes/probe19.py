"""Probe 19: THE TRANSFORM. bind(base, suffix) -> predicted derived form.
2x2: {phoneme-identity space, voicing-neutral shape space}
   x {SUM (superpose parts, no seam), SEAM (include junction cross-term)}
Suffix canonical forms learned from a train split (modal remainder);
evaluated on held-out pairs. Judged by cosine to the actual derived form
AND by a_mem retrieval of the actual derived episode.
"""
import sys, tempfile, warnings, numpy as np
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
    if f is None: return ("?",)
    if (sonority(ph) or 0) >= 6: return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))

# ── mine clean (base, suffix, derived) pairs ──
SUFFIXES = ["ing", "s", "ed", "er", "ly", "ness"]
pairs = []
for w in corpus:
    for sfx in SUFFIXES:
        if w.endswith(sfx) and len(w) > len(sfx) + 2:
            base = w[:-len(sfx)]
            if base in corpus:
                B, W = corpus[base], corpus[w]
                if len(W) > len(B) and W[:len(B)] == B:
                    pairs.append((base, sfx, w, W[len(B):]))
rng = np.random.default_rng(7)
rng.shuffle(pairs)
by_sfx = defaultdict(list)
for pr in pairs: by_sfx[pr[1]].append(pr)
train, test = [], []
for sfx, lst in by_sfx.items():
    k = int(len(lst) * 0.6)
    train += lst[:k]; test += lst[k:]
rng.shuffle(test)
test = test[:40]
print(f"mined {len(pairs)} pairs; train {len(train)}, test (capped) {len(test)}")
rem_counts = {s: Counter(tuple(r[3]) for r in train if r[1] == s) for s in SUFFIXES}
modal_phon = {s: list(c.most_common(1)[0][0]) for s, c in rem_counts.items() if c}
allo = {s: len(c) for s, c in rem_counts.items() if c}
print("suffix allomorph counts (phoneme remainders in train):",
      {s: allo[s] for s in allo})

# ── embedders: bigram+unigram vectors in each space ──
PH = sorted({p for pr in corpus.values() for p in pr}); PHI = {p: i for i, p in enumerate(PH)}
SH = sorted({shape(p) for p in PH}); SHI = {s: i for i, s in enumerate(SH)}
def vec(seq, space):
    if space == "phon":
        toks, idx, n = list(seq), PHI, len(PH)
    else:
        toks, idx, n = [shape(p) for p in seq], SHI, len(SH)
    v = np.zeros(n * n + n)
    for t in toks: v[n * n + idx[t]] += 1
    for a, b in zip(toks, toks[1:]): v[idx[a] * n + idx[b]] += 1
    m = np.linalg.norm(v)
    return v / m if m > 0 else v

def predict(base_pron, sfx, space, rule):
    mod = modal_phon[sfx]
    if rule == "SEAM":
        return vec(list(base_pron) + mod, space)     # full interference incl. junction
    vb, vs = vec(base_pron, space), vec(mod, space)  # SUM: parts superposed, no seam
    v = vb + vs
    return v / np.linalg.norm(v)

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K

print(f"\nretrieval library: {len(test)} derived words, chance {100/len(test):.0f}%")
print("space   rule    mean cos(pred, actual)   a_mem retrieval")
for space in ("phon", "shape"):
    lib_enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
    hook = EpisodeHooks(mem, encoder=lib_enc)
    mids = {w: hook.write_episode(vec(corpus[w], space)) for (_, _, w, _) in test}
    for rule in ("SUM", "SEAM"):
        cs, ok = [], 0
        for base, sfx, w, _ in test:
            pred = predict(corpus[base], sfx, space, rule)
            actual = vec(corpus[w], space)
            cs.append(float(pred @ actual))
            rec = hook.recall_context(pred)
            ok += int(rec.identity == mids[w])
        print(f"{space:5s}   {rule:4s}    {np.mean(cs):.3f}                   "
              f"{ok}/{len(test)} = {ok/len(test)*100:.0f}%")
