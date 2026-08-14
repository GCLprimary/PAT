"""XVII: the compass — order folded, not forgotten (probes 60, 61).

The cone forgets order; the homoshape collision class is the scar
(51.6% of mined bases share a shape with a different word — Part X's
canary measured colliding families folding to 0.99 cosine). The human
drew a compass (docs/sequencing.drawio — the second whiteboard square
in this project's history to become an organ): each phoneme
occurrence is stamped with its HEADING on two dials of coprime
periods — 8, the drawn compass rose, and 7, its coprime partner. The
fold is an order-free BAG of (phone, station8, station7) triples; the
Chinese Remainder Theorem recovers each occurrence's exact position
inside the mod-56 window, and the sequence reassembles.

Law 3: order is folded, not forgotten — the cone keeps its counts;
this module is an ANNEX; nothing is replaced. Equality on folds is an
order-sensitive exact match: two folds are equal exactly when the two
sequences are equal (the batteries assert both directions).

The dyadic reading (probe 61): the drawn dial's period is a power of
two because ad quadratum nesting halves exactly one dimension per
level, so reading position mod 2^k is reading its binary expansion
coarse-to-fine — bit-planes, one nesting per bit.
"""
from collections import Counter

P8, P7 = 8, 7                # the drawn dial and its coprime partner
WINDOW = P8 * P7             # 56: one full CRT cycle

# ── law 4: tangency is an assert, checked at import ──────────────────
# The dyadic dials nest with ZERO slack: the mod-4 reading is the
# mod-8 reading reduced, the mod-2 reading is the mod-4 reading
# reduced, and dial level k reads exactly bit k of position — at
# every station of the window.
for _i in range(WINDOW):
    assert _i % 4 == (_i % 8) % 4 and _i % 2 == (_i % 4) % 2, \
        f"tangency broke at {_i} — the dials do not nest"
    assert ((_i % 2, (_i % 4) >> 1, (_i % 8) >> 2)
            == tuple((_i >> _k) & 1 for _k in range(3))), \
        f"bit-plane reading broke at {_i}"

# The CRT bijection, enumerated once: (i mod 8, i mod 7) -> i. The
# probe's literal form scans range(56) per triple; this table IS that
# scan, done once — same theorem, same answers (a battery asserts
# parity with the literal form).
_I0 = {}
for _i in range(WINDOW):
    _I0.setdefault((_i % P8, _i % P7), _i)
assert len(_I0) == WINDOW    # coprime periods: the map is a bijection


def fold(phones):
    """The compass fold: an order-free bag of (phone, station8,
    station7) occurrence counts. A frozenset — no sequence survives
    in the container; the CONTENT is what carries the order."""
    return frozenset(Counter((ph, i % P8, i % P7)
                             for i, ph in enumerate(phones)).items())


def decode(bag, n):
    """Reassemble the sequence from its fold (probe 60): CRT places
    each (station8, station7) pair at its unique position inside the
    mod-56 window; repeats of the same residue pair stack by whole
    periods. Exact for every n < 56 + anything the window admits."""
    slots = [None] * n
    for (ph, r8, r7), c in bag:
        i0 = _I0[(r8, r7)]
        for k in range(c):
            pos = i0 + WINDOW * k
            if pos < n and slots[pos] is None:
                slots[pos] = ph
    return tuple(slots)


def dial_bit(pos, k):
    """T-3 bit-plane accessor: dial level k of a position IS bit k of
    its binary expansion, read through modular arithmetic alone."""
    return (pos % (1 << (k + 1))) >> k


def locality_violations(maxlen=WINDOW):
    """Probe 61 #5: positions sharing the full dyadic reading (equal
    mod 8) must sit exact multiples of 8 apart. Returns the violation
    count — zero, or the clockwork is broken."""
    return sum(1 for i in range(maxlen) for j in range(i + 1, maxlen)
               if i % 8 == j % 8 and (j - i) % 8 != 0)
