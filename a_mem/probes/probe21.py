"""Probe 21: THE SEMANTIC RUNG.
1) Meaning geometry from pure counts: window-4 co-occurrence -> PPMI
   (unseen pairs stay 0: absence != negative evidence -- ternary zero).
2) Sanity: nearest neighbors of common words.
3) Rung rhyme: is a suffix a CONSISTENT offset in meaning space?
   (mean pairwise cosine of derived-minus-base offsets vs random offsets)
4) THE RUNG: episodes = [shape-block | meaning-block]; cue with one block
   zeroed -> retrieve the right episode cross-modally through a_mem.
"""
import sys, tempfile, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import sonority, features

# ── counts -> PPMI ──
VOCAB_N, WIN = 4000, 4
uni = Counter()
sents = [l.split() for l in open("/home/claude/elfix/Elfix/data/corpus.txt")]
for s in sents: uni.update(s)
vocab = [w for w, _ in uni.most_common(VOCAB_N)]
VI = {w: i for i, w in enumerate(vocab)}
co = defaultdict(Counter)
for s in sents:
    idxs = [(i, VI[w]) for i, w in enumerate(s) if w in VI]
    for a in range(len(idxs)):
        ia, wa = idxs[a]
        for b in range(a + 1, len(idxs)):
            ib, wb = idxs[b]
            if ib - ia > WIN: break
            co[wa][wb] += 1; co[wb][wa] += 1
tot = sum(sum(c.values()) for c in co.values())
rowsum = np.array([sum(co[i].values()) if i in co else 0 for i in range(len(vocab))], float)
def ppmi_vec(i):
    v = np.zeros(len(vocab))
    for j, c in co.get(i, {}).items():
        exp = rowsum[i] * rowsum[j] / tot
        if exp > 0 and c > exp:
            v[j] = np.log2(c / exp)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v
M = {w: ppmi_vec(VI[w]) for w in vocab}
print(f"meaning geometry: {len(vocab)} words, window {WIN}, PPMI from counts")

def cos(u, v):
    return float(u @ v)

print("\nsanity — nearest neighbors:")
for w in ("water", "war", "music", "money"):
    if w in M:
        sims = sorted(((cos(M[w], M[o]), o) for o in vocab[:2000] if o != w), reverse=True)[:4]
        print(f"  {w}: " + ", ".join(o for _, o in sims))

print("\nsuffix-as-offset — offsets should agree with each other, not with noise:")
rng = np.random.default_rng(7)
for sfx in ("ed", "ing", "s"):
    offs = []
    for b in vocab:
        d = b + sfx
        if d in M and b in M and len(b) > 3:
            offs.append(M[d] - M[b])
        if len(offs) >= 12: break
    if len(offs) < 6: continue
    offs = [o / max(np.linalg.norm(o), 1e-9) for o in offs]
    sims = [cos(offs[i], offs[j]) for i in range(len(offs)) for j in range(i + 1, len(offs))]
    rand = []
    for _ in range(60):
        a, b2 = rng.choice(len(vocab), 2, replace=False)
        r = M[vocab[a]] - M[vocab[b2]]
        rand.append(r / max(np.linalg.norm(r), 1e-9))
    rsims = [cos(rand[i], rand[j]) for i in range(20) for j in range(i + 1, 20)]
    print(f"  -{sfx}: n={len(offs)} offset-agreement {np.mean(sims):+.3f}  vs random {np.mean(rsims):+.3f}")

# ── the rung: cross-modal recall through a_mem ──
corpus_ph = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2: corpus_ph[p[0]] = tuple(p[1:])
def shape(ph):
    f = features(ph)
    if f is None: return ("?",)
    if (sonority(ph) or 0) >= 6: return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))
PH = sorted({p for pr in corpus_ph.values() for p in pr})
SH = sorted({shape(p) for p in PH}); SHI = {s: i for i, s in enumerate(SH)}
NB = len(SH)
def shape_vec(pr):
    v = np.zeros(NB * NB + NB)
    ss = [shape(p) for p in pr]
    for t in ss: v[NB * NB + SHI[t]] += 1
    for a, b in zip(ss, ss[1:]): v[SHI[a] * NB + SHI[b]] += 1
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

WORDS = [w for w in ("water","music","money","house","school","church","light",
                     "night","world","heart","field","horse","river","stone",
                     "voice","road","fire","door","glass","bread","child",
                     "woman","doctor","window","garden") if w in M and w in corpus_ph][:24]
DS = len(shape_vec(corpus_ph[WORDS[0]]))
DM = len(vocab)
def episode(w, form=True, meaning=True):
    fs = shape_vec(corpus_ph[w]) if form else np.zeros(DS)
    ms = M[w] if meaning else np.zeros(DM)
    v = np.concatenate([fs, ms])
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K
enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
hook = EpisodeHooks(mem, encoder=enc)
mids = {w: hook.write_episode(episode(w)) for w in WORDS}
print(f"\nTHE RUNG — {len(WORDS)} form|meaning episodes, chance {100/len(WORDS):.0f}%:")
for label, kw in (("meaning-only cue -> form episode", dict(form=False)),
                  ("form-only cue -> meaning episode", dict(meaning=False))):
    ok = 0
    for w in WORDS:
        rec = hook.recall_context(episode(w, **kw))
        ok += int(rec.identity == mids[w])
    print(f"  {label}: {ok}/{len(WORDS)} = {ok/len(WORDS)*100:.0f}%")
