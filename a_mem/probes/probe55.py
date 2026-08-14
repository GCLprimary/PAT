"""Probe 55: SUFFIX DISCOVERY (the creature's proposal, human-accepted,
now probed). Mechanism per PROPOSAL.md: mine candidate suffixes from
the no-such-stem tail census; audit each candidate (attestation
examines the teacher); accept only what the exactness law can carry;
retire wrongly-adopted atoms through certification.

PHASE A  candidates: phoneme tails k=2..4 over the no-such-stem class,
         scored by STEM-ATTESTATION RATE (strip tail -> pron in
         lexicon) vs a random-tail baseline. Real suffixes strip to
         real words; junk doesn't.
PHASE B  the concat/mutating split: a candidate is CONCATENATIVE when
         its pron-matched pairs also decompose ORTHOGRAPHICALLY
         (word == stemword + modal spelling). Mutating classes
         (create->creation, t->sh) are censused, flagged to a future
         stem-allomorphy lane, never guessed.
PHASE C  the harvest: certified candidates retire no-such-stem atoms
         into 'discovered:<sfx>' aliases (double-lock: pron-exact stem
         AND orthographic decomposition). Confabs required: 0.
"""
import warnings
import numpy as np
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

attested = defaultdict(set)
for base, sfx, w, rem in pairs: attested[sfx].add(tuple(rem))
ALL_REMS = set()
for s_, rs in attested.items(): ALL_REMS |= rs
MAXR = max(len(r) for r in ALL_REMS)
PRON2WORDS = defaultdict(list)
for w, p in corpus.items(): PRON2WORDS[tuple(p)].append(w)

cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"): cnt.update(l.split())
stream = [w for w, c in cnt.most_common() if c >= 2 and w in corpus and len(w) >= 4]

def stem_candidates(p):
    return [(p[:-k], p[-k:]) for k in range(1, MAXR + 1)
            if tuple(p[-k:]) in ALL_REMS and len(p) - k >= 2]

def looks_derived(p):
    return len(p) >= 5 and any(tuple(p[-k:]) in ALL_REMS
                               for k in range(1, MAXR + 1))

no_such = []
for w in stream:
    p = tuple(corpus[w])
    if looks_derived(p) and not any(s in PRON2WORDS for s, _ in stem_candidates(p)):
        no_such.append(w)
print(f"no-such-stem class recomputed: {len(no_such)} words")

# PHASE A — candidates: rate >= baseline + 15 pts, min stem 3 phonemes
rng = np.random.default_rng(5)
MINSTEM = 3
def att_rate(words, k, tail=None):
    hit = tot = 0
    for w in words:
        p = tuple(corpus[w])
        if len(p) - k < MINSTEM: continue
        if tail is not None and p[-k:] != tail: continue
        tot += 1
        hit += int(p[:-k] in PRON2WORDS)
    return hit, tot

cands = []
for k in (4, 3, 2):
    tails = Counter(tuple(corpus[w])[-k:] for w in no_such
                    if len(corpus[w]) - k >= MINSTEM)
    bh, bt = att_rate(rng.choice(no_such, 1500).tolist(), k)
    base = bh / max(bt, 1)
    for t, n in tails.most_common(60):
        if n < 50: continue
        h, tt = att_rate(no_such, k, t)
        r = h / max(tt, 1)
        if r >= base + 0.15 and h >= 40:
            cands.append((t, k, n, h, r, base))
cands.sort(key=lambda x: (-x[1], -x[3]))     # longest tails first, then yield
print(f"\nPHASE A: {len(cands)} candidates clear the audit "
      f"(rate >= baseline+15pts, yield >= 40):")
for t, k, n, h, r, base in cands[:12]:
    print(f"  tail {' '.join(t):12s} n={n:4d}  attested-stems {h:4d} "
          f"({r*100:4.1f}% vs baseline {base*100:.1f}%)")

# PHASE B/C — concat certification + harvest
print("\nPHASE B/C per candidate: modal spelling, concat-certified, mutating flag")
total_retired = 0
confabs = 0
discovered = []
pool = set(no_such)
for t, k, n, h, r, base in cands[:12]:
    prs, spell = [], Counter()
    for w in list(pool):
        p = tuple(corpus[w])
        if len(p) - k >= 2 and p[-k:] == t and p[:-k] in PRON2WORDS:
            for sw in PRON2WORDS[p[:-k]]:
                if w.startswith(sw) and len(w) > len(sw):
                    prs.append((w, sw, w[len(sw):])); spell[w[len(sw):]] += 1
                    break
    if not spell: continue
    modal, mshare = spell.most_common(1)[0]
    certified = [(w, sw) for w, sw, sp in prs if sp == modal]
    mutating = h - len(prs)          # pron-stem exists but no ortho decomposition
    ok = 0
    for w, sw in certified:
        if tuple(corpus[w]) == tuple(corpus[sw]) + t:
            ok += 1; pool.discard(w)
        else:
            confabs += 1
    total_retired += ok
    discovered.append((modal, t, ok, mutating))
    print(f"  -{modal:6s} ({' '.join(t)}): certified {ok:4d}  "
          f"mutating/no-ortho {mutating:4d}  spelling share {spell[modal]}/{sum(spell.values())}")
print(f"\nHARVEST: {total_retired} atoms retire into discovered-suffix aliases; "
      f"CONFABS {confabs} (required 0)")
print("discovered suffixes:", ", ".join(f"-{m}" for m, t, ok, mu in discovered if ok >= 40))
