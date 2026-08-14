"""Probe 31: THE PAYOFF. Does the maintained stage improve mid-document
episode recall from a_mem?
36 passages (6 Brown categories x 6, non-overlapping) written as real
episodes; 12 documents = 3 passages each (distinct categories). Reading
sentence-by-sentence, recall the CURRENT segment's episode:
  memoryless: cue = current sentence centroid
  stage:      cue = integrated stage state (blend .5, page-turn theta=.65)
  oracle:     cue = whole-segment centroid (ceiling)
Same-category distractors guaranteed (6 episodes per category).
Declared acceptance: stage > memoryless overall AND at positions >= 2.
"""
import sys, os, re, warnings, tempfile, numpy as np
from collections import Counter
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/review6/mirror")
from mirror.meaning import MeaningGeometry
from nltk.corpus import brown

g = MeaningGeometry()
cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus.txt"):
    cnt.update(l.split())
STOP = set(w for w, _ in cnt.most_common(120))

def norm_sent(sent):
    line = " ".join(sent).lower()
    line = re.sub(r"[-]+", " ", line)
    line = re.sub(r"[^a-z' ]", "", line)
    return [w for w in line.split() if w]

def centroid(words):
    vs = [g.vec(w) for w in words if w in g and w not in STOP]
    if not vs: return None
    v = np.mean(vs, axis=0); n = np.linalg.norm(v)
    return v / n if n > 0 else None

CATS = ["news", "religion", "science_fiction", "romance", "government", "hobbies"]
rng = np.random.default_rng(11)
passages = []            # (cat, sents)
for c in CATS:
    ss = [norm_sent(s) for s in brown.sents(categories=c)]
    ss = [s for s in ss if len([w for w in s if w in g and w not in STOP]) >= 3]
    starts = rng.choice(len(ss) - 5, 6, replace=False)
    for st in starts:
        passages.append((c, ss[st:st + 4]))
rng.shuffle(passages)

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K
enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
hook = EpisodeHooks(mem, encoder=enc)
ep_emb, ep_id = [], []
for cat, seg in passages[:36]:
    e = centroid([w for s in seg for w in s])
    mid = hook.write_episode(e)
    ep_emb.append(e); ep_id.append(mid)
print(f"episodes written: {len(ep_id)} (6 per category, same-cat distractors live)")

# documents: 12 docs of 3 segments with distinct categories, drawn from the 36
by_cat = {}
for i, (cat, seg) in enumerate(passages[:36]):
    by_cat.setdefault(cat, []).append(i)
docs = []
used = set()
for d in range(12):
    cats = rng.choice(CATS, 3, replace=False)
    segs = []
    for c in cats:
        free = [i for i in by_cat[c] if i not in used]
        i = free[0] if free else by_cat[c][d % 6]
        used.add(i); segs.append(i)
    docs.append(segs)

THETA, BLEND = 0.65, 0.5
def recall(cue):
    r = hook.recall_context(cue)
    return r.identity

acc = {"memoryless": np.zeros(4), "stage": np.zeros(4), "oracle": np.zeros(4)}
n_pos = np.zeros(4)
for segs in docs:
    s_state = None
    for seg_idx in segs:
        cat, seg = passages[seg_idx]
        gold = ep_id[seg_idx]
        seg_c = centroid([w for s in seg for w in s])
        for pos, sent in enumerate(seg):
            v = centroid(sent)
            if v is None: continue
            if s_state is None or float(s_state @ v) < THETA:
                s_state = v
            else:
                s_state = BLEND * s_state + (1 - BLEND) * v
                s_state /= np.linalg.norm(s_state)
            n_pos[pos] += 1
            acc["memoryless"][pos] += int(recall(v) == gold)
            acc["stage"][pos] += int(recall(s_state) == gold)
            acc["oracle"][pos] += int(recall(seg_c) == gold)

print(f"\nrecall accuracy by within-segment position (chance {100/36:.0f}%):")
print("cue          pos1   pos2   pos3   pos4   overall")
for k in ("memoryless", "stage", "oracle"):
    row = acc[k] / n_pos * 100
    ov = acc[k].sum() / n_pos.sum() * 100
    print(f"{k:11s}  " + "  ".join(f"{x:4.0f}%" for x in row) + f"   {ov:4.0f}%")
