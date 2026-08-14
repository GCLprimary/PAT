"""Probe 18: the merge embedder. Acceptance: beat bag's noisy self-recall
while holding relative-form recall >= 10x chance.

Candidates (all earned from ElfIX machinery):
  E0 bag        -- phoneme counts + length/sonority stats   (baseline, 54%)
  E1 contour    -- sonority trajectory resampled to 16 pts + syllable count
  E2 shapes     -- voicing-neutral (manner,place) bigram counts (appendix geometry)
  E3 combined   -- E1 + E2 concatenated (blocks L2-normalized then joined)

Noise: fixed-angle perturbation (cos theta = 0.95 / 0.90) so severity is
identical across embedding dimensions -- probe 17's per-dim sigma was unfair
across dims.
"""
import sys, tempfile, warnings, numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import sonority, features
from elfix.trajectory.trajectory import Trajectory

np.set_printoptions(precision=3, suppress=True)
corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    p = line.strip().split()
    if len(p) >= 2:
        corpus[p[0]] = tuple(p[1:])

WORDS = ["lock","play","help","read","load","fold","trust","open","will",
         "lead","build","heat","law","work","agree","think","group","bend",
         "fill","end","cat","dog","house","water","light"]
WORDS = [w for w in WORDS if w in corpus]
RELATIVES = {"lock":"unlocking","play":"replaying","read":"misreading",
             "load":"reloading","help":"unhelpful","think":"unthinking",
             "build":"rebuilding","work":"reworking","open":"reopening",
             "lead":"misleading"}
RELATIVES = {b: r for b, r in RELATIVES.items() if b in corpus and r in corpus}

PHONES = sorted({p for pr in corpus.values() for p in pr})
PIDX = {p: i for i, p in enumerate(PHONES)}

def shape(ph):
    f = features(ph)
    if f is None: return ("?",)
    if getattr(f, "is_vowel", None) or (sonority(ph) or 0) >= 6:
        return ("V",)
    return (str(getattr(f, "manner", "?")), str(getattr(f, "place", "?")))

SHAPES = sorted({shape(p) for p in PHONES})
SIDX = {s: i for i, s in enumerate(SHAPES)}
NB = len(SHAPES)

def nrm(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else v

def e_bag(pr):
    v = np.zeros(len(PHONES) + 3)
    sons = [sonority(p) or 0 for p in pr]
    for p in pr: v[PIDX[p]] += 1
    v[-3] = len(pr); v[-2] = np.mean(sons); v[-1] = np.max(sons)
    return nrm(v)

def e_contour(pr):
    sons = np.array([sonority(p) or 0 for p in pr], dtype=float)
    xs = np.linspace(0, len(sons) - 1, 16)
    cont = np.interp(xs, np.arange(len(sons)), sons)
    t = Trajectory.of(list(pr))
    return nrm(np.concatenate([cont, [t.syllable_count(), len(pr)]]))

def e_shapes(pr):
    v = np.zeros(NB * NB + NB)
    ss = [shape(p) for p in pr]
    for s in ss: v[NB * NB + SIDX[s]] += 1
    for a, b in zip(ss, ss[1:]): v[SIDX[a] * NB + SIDX[b]] += 1
    return nrm(v)

def e_combined(pr):
    return nrm(np.concatenate([e_contour(pr), e_shapes(pr)]))

EMB = {"E0 bag": e_bag, "E1 contour": e_contour, "E2 shapes": e_shapes,
       "E3 combined": e_combined}

def angle_noise(e, c, rng):
    g = rng.normal(size=len(e)); g -= (g @ e) * e
    g = nrm(g)
    return nrm(e * c + g * np.sqrt(1 - c * c))

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K

print(f"library: {len(WORDS)} words, {len(RELATIVES)} relative pairs, chance {1/len(WORDS)*100:.0f}%")
print("embedder      dim   crowd(nn-cos)  self@.95  self@.90  relative  discrim")
for name, fn in EMB.items():
    vecs = {w: fn(corpus[w]) for w in WORDS}
    M = np.array([vecs[w] for w in WORDS])
    G = M @ M.T; np.fill_diagonal(G, -1)
    crowd = float(G.max(axis=1).mean())
    enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
    hook = EpisodeHooks(mem, encoder=enc)
    mids = {w: hook.write_episode(vecs[w]) for w in WORDS}
    rng = np.random.default_rng(9)
    res = {}
    for c in (0.95, 0.90):
        ok = tot = 0
        for w in WORDS:
            for _ in range(2):
                rec = hook.recall_context(angle_noise(vecs[w], c, rng))
                ok += int(rec.identity == mids[w]); tot += 1
        res[c] = ok / tot
    ok = 0
    for b, r in RELATIVES.items():
        rec = hook.recall_context(fn(corpus[r]))
        ok += int(rec.identity == mids[b])
    rel = ok / len(RELATIVES)
    ok = 0
    for a, b in [("lock","law"), ("play","lead"), ("cat","bend")]:
        rec = hook.recall_context(vecs[a])
        ok += int(rec.identity == mids[a])
    dim = len(fn(corpus["lock"]))
    print(f"{name:12s}  {dim:4d}   {crowd:.3f}         {res[0.95]*100:3.0f}%      "
          f"{res[0.90]*100:3.0f}%      {rel*100:3.0f}%      {ok}/3")
