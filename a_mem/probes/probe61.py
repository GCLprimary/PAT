"""Probe 61: THE DYADIC TOWER (ad quadratum as clockwork, measured).
The nesting halves exactly one dimension up, so the natural dial
ladder is 2, 4, 8, ... : reading position mod 2^k is reading its
binary expansion coarse-to-fine -- bit-planes, one per nesting level.
Checks:
  1. TANGENCY AS ARITHMETIC: the dials nest -- residue mod 4 must
     equal (residue mod 8) mod 4, everywhere. Zero slack, asserted.
  2. bit-plane decode: level-k dial = k-th bit of position, shown.
  3. invertibility of the tower fold (dyadic 8 x coprime 7): 100%
     round-trip across the lexicon, same theorem, new ladder.
  4. headroom: longest pron vs the mod-56 window.
  5. locality: shared high dials = same dyadic neighborhood --
     positions agreeing mod 8 sit exactly 8k apart, counted.
"""
import warnings
from collections import Counter
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

# 1 + 2: nesting consistency and bit-planes over every position used
maxlen = max(len(p) for p in corpus.values())
for i in range(maxlen):
    assert i % 4 == (i % 8) % 4 and i % 2 == (i % 4) % 2      # tangency
    bits = (i % 2, (i % 4) >> 1, (i % 8) >> 2)                # the three planes
    assert bits == tuple((i >> k) & 1 for k in range(3))
print(f"1. tangency holds at every position 0..{maxlen-1}: "
      f"mod-4 == mod-8 reduced, mod-2 == mod-4 reduced (zero slack)")
print(f"2. bit-planes verified: dial level k reads bit k of position "
      f"(coarse-to-fine, one nesting per bit)")

def fold(p):
    return frozenset(Counter((ph, i % 8, i % 7) for i, ph in enumerate(p)).items())
def decode(bag, n):
    slots = [None] * n
    for (ph, r8, r7), c in bag:
        i0 = next(i for i in range(56) if i % 8 == r8 and i % 7 == r7)
        for k in range(c):
            pos = i0 + 56 * k
            if pos < n and slots[pos] is None: slots[pos] = ph
    return tuple(slots)
ok = n = 0
for w, p in corpus.items():
    if len(p) >= 56: continue
    n += 1
    ok += int(decode(fold(tuple(p)), len(p)) == tuple(p))
print(f"3. tower fold invertibility: {ok}/{n} = {ok/n*100:.2f}%")
print(f"4. headroom: longest pron {maxlen} phones vs window 56 "
      f"({'inside' if maxlen < 56 else 'OVERFLOW'}; margin {56-maxlen})")

pairs8 = sum(1 for i in range(maxlen) for j in range(i+1, maxlen)
             if i % 8 == j % 8 and (j - i) % 8 != 0)
print(f"5. locality: positions sharing the full dyadic reading differ by "
      f"exact multiples of 8 -- violations found: {pairs8} (must be 0)")
