"""Probe 22: SCALING dose-response.
A) Meaning organ at 1M (Brown) vs 5M (stacked NLTK) words, same recipe:
   window-4, vocab 4000, content-only contexts (STOP_K=120), PPMI.
   Metrics: relatedness triples; suffix-offset agreement vs random floor.
B) Rung crowding: cross-modal recall at 24 vs 44 words (grid-47 ceiling).
"""
import sys, tempfile, warnings, numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import sonority, features

def build_meaning(path, VOCAB_N=4000, WIN=4, STOP_K=120):
    uni = Counter()
    sents = [l.split() for l in open(path)]
    for s in sents: uni.update(s)
    vocab = [w for w, _ in uni.most_common(VOCAB_N)]
    VI = {w: i for i, w in enumerate(vocab)}
    STOP = set(w for w, _ in uni.most_common(STOP_K))
    co = defaultdict(Counter)
    for s in sents:
        idxs = [(i, VI[w], w) for i, w in enumerate(s) if w in VI]
        for a in range(len(idxs)):
            ia, wa, sa = idxs[a]
            for b in range(a + 1, len(idxs)):
                ib, wb, sb = idxs[b]
                if ib - ia > WIN: break
                if sb not in STOP: co[wa][wb] += 1
                if sa not in STOP: co[wb][wa] += 1
    tot = sum(sum(c.values()) for c in co.values())
    rowsum = np.array([sum(co[i].values()) if i in co else 0 for i in range(len(vocab))], float)
    ctxsum = np.zeros(len(vocab))
    for i, c in co.items():
        for j, v in c.items(): ctxsum[j] += v
    M = {}
    for w in vocab:
        i = VI[w]; v = np.zeros(len(vocab))
        for j, c in co.get(i, {}).items():
            exp = rowsum[i] * ctxsum[j] / tot
            if exp > 0 and c > exp: v[j] = np.log2(c / exp)
        n = np.linalg.norm(v)
        M[w] = v / n if n > 0 else v
    return M, vocab, STOP

TRIPLES = [("water","surface"),("war","civil"),("music","songs"),("money","tax"),
           ("school","students"),("night","morning"),("doctor","hospital"),
           ("church","god"),("river","water"),("fire","heat"),("court","judge"),
           ("food","eat"),("book","read"),("game","play"),("heart","blood"),
           ("road","car"),("winter","snow"),("voice","heard"),("door","open"),
           ("child","mother")]

def cos(u, v): return float(u @ v)

def evaluate(M, vocab, tag, rng):
    hits = tot = 0
    for w, rel in TRIPLES:
        if w in M and rel in M:
            rnd = vocab[rng.integers(500, len(vocab))]
            if rnd in (w, rel): continue
            hits += int(cos(M[w], M[rel]) > cos(M[w], M[rnd])); tot += 1
    offs_out = {}
    for sfx in ("ed", "ing", "s"):
        offs = []
        for b in vocab:
            d = b + sfx
            if d in M and b in M and len(b) > 3:
                o = M[d] - M[b]; n = np.linalg.norm(o)
                if n > 0: offs.append(o / n)
            if len(offs) >= 12: break
        sims = [cos(offs[i], offs[j]) for i in range(len(offs)) for j in range(i + 1, len(offs))]
        rand = []
        for _ in range(20):
            a, b2 = rng.choice(len(vocab), 2, replace=False)
            r = M[vocab[a]] - M[vocab[b2]]; n = np.linalg.norm(r)
            if n > 0: rand.append(r / n)
        rsims = [cos(rand[i], rand[j]) for i in range(len(rand)) for j in range(i + 1, len(rand))]
        offs_out[sfx] = (float(np.mean(sims)), float(np.mean(rsims)))
    print(f"{tag}: relatedness {hits}/{tot}   offsets: " +
          "  ".join(f"-{s} {a:+.3f}(rnd {r:+.3f})" for s, (a, r) in offs_out.items()))
    return offs_out

rng = np.random.default_rng(7)
print("A · DOSE-RESPONSE (same recipe, two corpus sizes)")
M1, V1, S1 = build_meaning("/home/claude/elfix/Elfix/data/corpus.txt")
o1 = evaluate(M1, V1, "  1M (Brown)      ", rng)
M5, V5, S5 = build_meaning("/home/claude/elfix/Elfix/data/corpus_big.txt")
o5 = evaluate(M5, V5, "  5M (stacked)    ", rng)
print("  offset gain 1M->5M: " + "  ".join(
    f"-{s}: {o1[s][0]:+.3f}->{o5[s][0]:+.3f}" for s in ("ed", "ing", "s")))

print("\nB · RUNG CROWDING — cross-modal recall, 24 vs 44 words (grid 47)")
corpus_ph = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2: corpus_ph[p[0]] = tuple(p[1:])
def shape(ph):
    f = features(ph)
    if str(getattr(f, "kind", "?")) == "vowel": return ("V",)
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
CAND = [w for w in V5[300:2000] if w in corpus_ph and w in M5 and w.isalpha() and len(w) > 3]
from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K
for NW in (24, 39):
    WORDS = CAND[:NW]
    DS = len(shape_vec(corpus_ph[WORDS[0]])); DM = len(V5)
    def episode(w, form=True, meaning=True):
        fs = shape_vec(corpus_ph[w]) if form else np.zeros(DS)
        ms = M5[w] if meaning else np.zeros(DM)
        v = np.concatenate([fs, ms]); n = np.linalg.norm(v)
        return v / n if n > 0 else v
    enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
    hook = EpisodeHooks(mem, encoder=enc)
    mids = {w: hook.write_episode(episode(w)) for w in WORDS}
    line = f"  {NW} words: "
    for label, kw in (("meaning->form", dict(form=False)), ("form->meaning", dict(meaning=False))):
        ok = sum(int(hook.recall_context(episode(w, **kw)).identity == mids[w]) for w in WORDS)
        line += f"{label} {ok}/{NW}  "
    print(line + f"(chance {100/NW:.0f}%)")
