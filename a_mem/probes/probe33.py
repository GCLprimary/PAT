"""Probe 33: THE SHELL. perceive -> recall -> act -> write -> next.
Closed world: 60 word-tasks. Agent starts knowing 10 of 30 bases (episodes
in a_mem). Stream interleaves bare new bases (teachable on refusal: the
world confirms, the agent WRITES the episode) with derived forms of all 30.
Memory ON: refusals of bare unknowns become episodes; later relatives
become analyzable. Memory OFF: identical agent, no writes.
Acceptance: ON beats OFF by >= 30 points on the final third; confabulation
ZERO in both arms; every ON gain traces to a written episode.
"""
import sys, os, warnings, tempfile, numpy as np
from collections import defaultdict
warnings.filterwarnings("ignore")
os.environ["MIRROR_ELFIX_PATH"] = "/home/claude/elfix/Elfix"
sys.path.insert(0, "/home/claude/probe")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

from amem.api import Memory
from amem.hooks import EpisodeHooks
from amem.encoder import Encoder
import amem.constants as K

byb = defaultdict(dict)
for base, sfx, w, rem in pairs:
    byb[base][sfx] = w
rng2 = np.random.default_rng(23)
cands = sorted([b for b, d in byb.items() if len(d) >= 2 and len(b) >= 4])
rng2.shuffle(cands)
BASES = cands[:30]
KNOWN0 = set(BASES[:10])
NEW = BASES[10:]

# task stream: each new base appears bare once, its derived forms after;
# known bases contribute derived forms throughout; shuffled with constraint.
tasks = []
for b in NEW:
    tasks.append(("bare", b, b))
for b in BASES:
    for sfx, w in list(byb[b].items())[:2]:
        tasks.append(("derived", b, w))
rng2.shuffle(tasks)
# enforce bare-before-derived for NEW bases
seen = set()
ordered = []
deferred = defaultdict(list)
for t in tasks:
    kind, b, w = t
    if kind == "derived" and b in NEW and b not in seen:
        deferred[b].append(t); continue
    ordered.append(t)
    if kind == "bare":
        seen.add(b); ordered += deferred.pop(b, [])
tasks = ordered[:60]
print(f"stream: {len(tasks)} tasks; start knowing {len(KNOWN0)}/{len(BASES)} bases")

THETA = 0.98
def run_agent(memory_on):
    enc = Encoder(grid=47, zone_min=2, zone_max=37, min_sep=K.PLACE_MIN_SEP, seed=0)
    mem = Memory(grid=47, seed=5, path=tempfile.mkdtemp())
    hook = EpisodeHooks(mem, encoder=enc)
    known = {}
    for b in KNOWN0:
        known[b] = hook.write_episode(vec(corpus[b], "shape"))
    bound_cache = {}
    def bound(b, s):
        if (b, s) not in bound_cache and s in modal_phon:
            bound_cache[(b, s)] = predict(corpus[b], s, "shape", "SEAM")
        return bound_cache.get((b, s))
    log = []
    writes = 0
    for kind, gold_b, w in tasks:
        obs = vec(corpus[w], "shape")
        s1 = {b: float(obs @ vec(corpus[b], "shape")) for b in known}
        best_b = max(s1, key=s1.get) if s1 else None
        act = ("REFUSE", None, None)
        if best_b and s1[best_b] >= THETA:
            act = ("BARE", best_b, None)
        else:
            s2 = {}
            for b in known:
                for s in SUFFIXES:
                    v = bound(b, s)
                    if v is not None:
                        s2[(b, s)] = float(obs @ v)
            if s2:
                k2 = max(s2, key=s2.get)
                if s2[k2] >= THETA:
                    act = ("DERIVED", k2[0], k2[1])
        correct = (kind == "bare" and act[0] == "BARE" and act[1] == gold_b) or \
                  (kind == "derived" and act[0] == "DERIVED" and act[1] == gold_b)
        confab = (act[0] != "REFUSE") and not correct and \
                 not (kind == "derived" and act[0] == "BARE" and act[1] == gold_b)
        safe_refusal = act[0] == "REFUSE" and gold_b not in known
        log.append((correct, confab, act[0]))
        # the WRITE half of the loop: a refused bare unknown is a teachable moment
        if memory_on and kind == "bare" and act[0] == "REFUSE":
            known[gold_b] = hook.write_episode(obs)
            writes += 1
    return log, writes

for arm in (True, False):
    log, writes = run_agent(arm)
    n = len(log)
    third = n // 3
    acc_all = np.mean([c for c, _, _ in log]) * 100
    acc_final = np.mean([c for c, _, _ in log[-third:]]) * 100
    confabs = sum(cf for _, cf, _ in log)
    refs = sum(a == "REFUSE" for _, _, a in log)
    tag = "memory ON " if arm else "memory OFF"
    print(f"{tag}: overall {acc_all:.0f}%  final-third {acc_final:.0f}%  "
          f"refusals {refs}  confabulations {confabs}  episodes written {writes}")
