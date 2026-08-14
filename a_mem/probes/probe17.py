"""Probe 17: (A) does center-plus-edges self-form at the morpheme rung?
             (B) ElfIX geometry as a_mem's embedder -- the merge test.
Uses cmu_preprocessed.txt (25k words) and ElfIX's earned sonority scale.
"""
import sys, tempfile, warnings, numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, "/home/claude/elfix/Elfix")
from elfix.substrate.features import sonority, features

np.set_printoptions(precision=3, suppress=True)

# corpus: word -> phoneme tuple
corpus = {}
for line in open("/home/claude/elfix/Elfix/data/cmu_preprocessed.txt"):
    parts = line.strip().split()
    if len(parts) >= 2:
        corpus[parts[0]] = tuple(parts[1:])
prons = list(corpus.values())

def subseq_count(seq):
    seq = tuple(seq); n = len(seq); c = 0
    for p in prons:
        for i in range(len(p) - n + 1):
            if p[i:i + n] == seq:
                c += 1; break   # count words containing it, not occurrences
    return c

AFFIX_PHON = {"un": ["AH","N"], "re": ["R","IY"], "dis": ["D","IH","S"],
              "pre": ["P","R","IY"], "mis": ["M","IH","S"],
              "ing": ["IH","NG"], "ed": ["D"], "s": ["Z"], "er": ["ER"],
              "ly": ["L","IY"], "ment": ["M","AH","N","T"],
              "ful": ["F","AH","L"], "ness": ["N","AH","S"]}

# transparent prefix+base+suffix words (base must be in corpus)
TRIS = [("un","lock","ing"), ("re","play","ing"), ("un","help","ful"),
        ("mis","read","ing"), ("re","load","ing"), ("un","fold","ing"),
        ("dis","trust","ful"), ("re","open","ing"), ("un","will","ing"),
        ("mis","lead","ing"), ("re","build","ing"), ("un","end","ing"),
        ("pre","heat","ing"), ("un","law","ful"), ("re","work","ing"),
        ("dis","agree","ment"), ("un","think","ing"), ("re","group","ing"),
        ("un","bend","ing"), ("re","fill","ing")]

print("A · HEAD-MARGIN TEST — is the base the amplitude peak?")
print("   amplitude 1: surprisal = -log2(corpus words containing segment)")
print("   amplitude 2: sonority mass (earned scale)")
w1 = w2 = n = 0
for pre, base, suf in TRIS:
    if base not in corpus: continue
    segs = {"pre": AFFIX_PHON[pre], "base": list(corpus[base]), "suf": AFFIX_PHON[suf]}
    surp = {k: -np.log2(max(subseq_count(v), 1) / len(prons)) for k, v in segs.items()}
    smass = {k: sum(sonority(ph) or 0 for ph in v) for k, v in segs.items()}
    n += 1
    w1 += int(max(surp, key=surp.get) == "base")
    w2 += int(max(smass, key=smass.get) == "base")
print(f"   n={n} words: base wins surprisal {w1}/{n} = {w1/n*100:.0f}%   "
      f"base wins sonority-mass {w2}/{n} = {w2/n*100:.0f}%")

print()
print("B · MERGE TEST — ElfIX earned features as a_mem embeddings")
PHONES = sorted({p for pr in prons for p in pr})
IDX = {p: i for i, p in enumerate(PHONES)}
def embed(pron):
    v = np.zeros(len(PHONES) + 3)
    sons = [sonority(p) or 0 for p in pron]
    for p in pron: v[IDX[p]] += 1
    v[-3] = len(pron); v[-2] = float(np.mean(sons)); v[-1] = float(np.max(sons))
    return v / np.linalg.norm(v)

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K
WORDS = ["lock","play","help","read","load","fold","trust","open","will",
         "lead","build","heat","law","work","agree","think","group","bend",
         "fill","end","cat","dog","house","water","light","stone","river",
         "cloud","grass","stone"][:28]
WORDS = [w for w in dict.fromkeys(WORDS) if w in corpus][:25]
RELATIVES = {"lock":"unlocking","play":"replaying","read":"misreading",
             "load":"reloading","help":"unhelpful","think":"unthinking",
             "build":"rebuilding","work":"reworking","open":"reopening",
             "lead":"misleading"}
enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
hook = EpisodeHooks(mem, encoder=enc)
mids = {w: hook.write_episode(embed(corpus[w])) for w in WORDS}

rng = np.random.default_rng(9)
ok = tot = 0
for w in WORDS:
    for _ in range(2):
        e = embed(corpus[w]) + rng.normal(size=len(PHONES) + 3) * 0.10
        rec = hook.recall_context(e / np.linalg.norm(e))
        ok += int(rec.identity == mids[w]); tot += 1
print(f"   noisy self-recall (sigma .10): {ok}/{tot} = {ok/max(tot,1)*100:.0f}%  (n={tot})")

ok = tot = 0
for base, rel in RELATIVES.items():
    if base in mids and rel in corpus:
        rec = hook.recall_context(embed(corpus[rel]))
        ok += int(rec.identity == mids[base]); tot += 1
print(f"   relative-form recall (e.g. 'unlocking' -> 'lock' episode): {ok}/{tot} = {ok/max(tot,1)*100:.0f}%  (n={tot})")

# minimal-pair discrimination: does sound-similarity confuse distinct episodes?
pairs = [("lock","law"), ("play","lead"), ("cat","bend")]
ok = tot = 0
for a, b in pairs:
    if a in mids and b in mids:
        rec = hook.recall_context(embed(corpus[a]))
        ok += int(rec.identity == mids[a]); tot += 1
print(f"   near-form discrimination: {ok}/{tot} correct")
