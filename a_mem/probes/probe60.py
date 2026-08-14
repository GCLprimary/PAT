"""Probe 60: THE COMPASS (the user's dial, measured).
The cone forgets order -- the homoshape collision class is the scar.
The compass claims order can be FOLDED, not forgotten: each phoneme
occurrence is stamped with its heading on two dials of coprime
periods (8 -- the drawn compass -- and 7); the fold is an order-free
BAG of (phone, station8, station7) triples; the Chinese Remainder
Theorem decodes each occurrence's exact position (mod 56), and the
sequence reassembles. Measures:
  1. the collision census: same-counts different-order families
  2. separation under the compass fold (expect 100%)
  3. EXACT invertibility: decode(fold(w)) == pron(w), whole lexicon
"""
import warnings
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

P8, P7 = 8, 7                       # the drawn dial and its coprime partner
def fold(p):                        # order-free container, order-recoverable content
    return frozenset(Counter((ph, i % P8, i % P7) for i, ph in enumerate(p)).items())
def decode(bag, n):
    slots = [None] * n
    for (ph, r8, r7), c in bag:
        # CRT: find i mod 56 with i%8==r8, i%7==r7
        i0 = next(i for i in range(56) if i % P8 == r8 and i % P7 == r7)
        for k in range(c):
            pos = i0 + 56 * k       # repeats of the same residue pair stack by period
            if pos < n and slots[pos] is None: slots[pos] = ph
    return tuple(slots)

sig = defaultdict(list)
for w, p in corpus.items():
    if len(p) < 56: sig[tuple(sorted(p))].append((w, tuple(p)))
fams = {k: v for k, v in sig.items() if len({pr for _, pr in v}) >= 2}
orders = sum(len({pr for _, pr in v}) for v in fams.values())
print(f"1. homoshape census: {len(fams)} colliding count-signatures, "
      f"{orders} distinct orderings sharing them "
      f"(e.g., {[w for w, _ in list(fams.values())[0]][:3]})")

sep = tot = 0
for v in fams.values():
    prs = list({pr for _, pr in v})
    for i in range(len(prs)):
        for j in range(i + 1, len(prs)):
            tot += 1
            sep += int(fold(prs[i]) != fold(prs[j]))
print(f"2. separation under the compass: {sep}/{tot} colliding pairs "
      f"({sep/tot*100:.1f}%) now distinct")

ok = n = 0
for w, p in corpus.items():
    if len(p) >= 56: continue
    n += 1
    ok += int(decode(fold(tuple(p)), len(p)) == tuple(p))
print(f"3. invertibility: decode(fold(w)) == pron(w) for {ok}/{n} lexicon "
      f"words ({ok/n*100:.2f}%) -- order folded, not forgotten")
