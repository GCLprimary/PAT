"""Probe 34: RESPOND TO USER INPUT — the complexity curve.
Closed word-world, four repertoire actions + alien verbs:
  analyze <w> | what relates to <w> | remember <base> | do you know <b>
  aliens: translate <w>, rhyme <w>  -> must REFUSE (contained)
Inputs: 1..6 clauses joined by and/then. 12 inputs per k. 25% carry one
alien clause. Teach-then-use patterns injected (TEACH clause i, ANALYZE
a derived form of it at clause j>i).
Metrics: per-clause accuracy vs k; teach->use success; alien containment
(other clauses unaffected, alien refused); confabulation (must be 0).
"""
import sys, os, warnings, tempfile, numpy as np
from collections import defaultdict
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/probe"); sys.path.insert(0, "/home/claude/review6/mirror")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])
from mirror.meaning import MeaningGeometry
from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K

g = MeaningGeometry()
byb = defaultdict(dict)
for base, sfx, w, rem in pairs: byb[base][sfx] = w
rng = np.random.default_rng(31)
cands = sorted([b for b, d in byb.items() if len(d) >= 2 and len(b) >= 4])
rng.shuffle(cands)
BASES = cands[:40]
KNOWN0, TEACHABLE = set(BASES[:15]), BASES[15:]
MEANW = [w for w in ("water","music","school","church","river","fire","road","heart") if w in g]

class Agent:
    def __init__(self):
        enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
        self.hook = EpisodeHooks(Memory(grid=47, seed=5, path=tempfile.mkdtemp()), encoder=enc)
        self.known = {}
        for b in KNOWN0: self.known[b] = self.hook.write_episode(vec(corpus[b], "shape"))
        self.bc = {}
    def bound(self, b, s):
        if (b, s) not in self.bc and s in modal_phon:
            self.bc[(b, s)] = predict(corpus[b], s, "shape", "SEAM")
        return self.bc.get((b, s))
    def handle(self, clause):
        toks = clause.split()
        verb = toks[0]
        arg = toks[-1]
        if verb == "analyze":
            if arg not in corpus: return ("REFUSE", "unknown form")
            obs = vec(corpus[arg], "shape")
            s1 = {b: float(obs @ vec(corpus[b], "shape")) for b in self.known}
            if s1 and max(s1.values()) >= 0.98:
                return ("BARE", max(s1, key=s1.get))
            s2 = {(b, s): float(obs @ self.bound(b, s)) for b in self.known
                  for s in SUFFIXES if self.bound(b, s) is not None}
            if s2 and max(s2.values()) >= 0.98:
                k2 = max(s2, key=s2.get); return ("DERIVED", k2[0], k2[1])
            return ("REFUSE", "no analysis stands")
        if verb == "relates":
            if arg in g: return ("NEIGHBORS", tuple(g.neighbors(arg, k=3)))
            return ("REFUSE", "word not in meaning vocabulary")
        if verb == "remember":
            if arg in corpus and arg not in self.known:
                self.known[arg] = self.hook.write_episode(vec(corpus[arg], "shape"))
                return ("LEARNED", arg)
            return ("KNOWN", arg) if arg in self.known else ("REFUSE", "cannot learn that")
        if verb == "know":
            return ("YES", arg) if arg in self.known else ("NO", arg)
        return ("REFUSE", f"'{verb}' is not something I do")

def make_input(k, rng):
    clauses, gold = [], []
    alien_at = rng.integers(0, k) if rng.random() < 0.25 else -1
    teach_pair = None
    if k >= 3 and rng.random() < 0.5:
        b = TEACHABLE[rng.integers(len(TEACHABLE))]
        forms = list(byb[b].items())
        if forms:
            i = rng.integers(0, k - 1)
            teach_pair = (i, b, forms[0][1], forms[0][0])
    for i in range(k):
        if i == alien_at:
            w = MEANW[rng.integers(len(MEANW))]
            clauses.append(f"{'translate' if rng.random()<.5 else 'rhyme'} {w}")
            gold.append(("ALIEN",)); continue
        if teach_pair and i == teach_pair[0]:
            clauses.append(f"remember {teach_pair[1]}"); gold.append(("LEARNED", teach_pair[1])); continue
        if teach_pair and i == teach_pair[0] + 1 + rng.integers(0, max(1, k - teach_pair[0] - 1)) and i > teach_pair[0]:
            clauses.append(f"analyze {teach_pair[2]}")
            gold.append(("DERIVED", teach_pair[1], teach_pair[3])); teach_pair = None; continue
        r = rng.random()
        if r < 0.4:
            b = BASES[rng.integers(15)]
            forms = list(byb[b].items())
            sfx, w = forms[rng.integers(len(forms))]
            clauses.append(f"analyze {w}"); gold.append(("DERIVED", b, sfx))
        elif r < 0.6:
            w = MEANW[rng.integers(len(MEANW))]
            clauses.append(f"relates to {w}"); gold.append(("NEIGHBORS",))
        elif r < 0.8:
            b = BASES[rng.integers(15)]
            clauses.append(f"know {b}"); gold.append(("YES", b))
        else:
            b = TEACHABLE[rng.integers(len(TEACHABLE))]
            clauses.append(f"remember {b}"); gold.append(("LEARNEDOK", b))
    return clauses, gold

stats = {k: [0, 0] for k in range(1, 7)}
thread_ok = thread_n = 0
alien_ref = alien_n = 0
clean_acc_with_alien = [0, 0]
confab = 0
for k in range(1, 7):
    for _ in range(12):
        agent_input, gold = make_input(k, rng)
        A = Agent() if k == 1 and _ == 0 else A  # persistent agent across all inputs
        has_alien = any(gd[0] == "ALIEN" for gd in gold)
        for cl, gd in zip(agent_input, gold):
            out = A.handle(cl)
            if gd[0] == "ALIEN":
                alien_n += 1; alien_ref += int(out[0] == "REFUSE"); continue
            if gd[0] == "NEIGHBORS": ok = out[0] == "NEIGHBORS" and len(out[1]) == 3
            elif gd[0] == "LEARNED": ok = out[0] in ("LEARNED", "KNOWN")
            elif gd[0] == "LEARNEDOK": ok = out[0] in ("LEARNED", "KNOWN")
            elif gd[0] == "DERIVED": ok = out[:3] == ("DERIVED", gd[1], gd[2])
            elif gd[0] == "YES": ok = out[0] == "YES"
            else: ok = False
            if gd[0] == "DERIVED" and out[0] == "DERIVED" and not ok: confab += 1
            stats[k][0] += int(ok); stats[k][1] += 1
            if has_alien: clean_acc_with_alien[0] += int(ok); clean_acc_with_alien[1] += 1
            if gd[0] == "DERIVED" and gd[1] in TEACHABLE:
                thread_n += 1; thread_ok += int(ok)

print("per-clause accuracy vs input length k:")
for k in range(1, 7):
    c, n = stats[k]
    print(f"  k={k}: {c}/{n} = {c/max(n,1)*100:.0f}%")
print(f"teach->use within input: {thread_ok}/{thread_n}")
print(f"alien clauses refused: {alien_ref}/{alien_n}; clean clauses in alien-bearing inputs: "
      f"{clean_acc_with_alien[0]}/{clean_acc_with_alien[1]} = "
      f"{clean_acc_with_alien[0]/max(clean_acc_with_alien[1],1)*100:.0f}%")
print(f"confabulations (wrong analysis asserted): {confab}")
