"""Probe 1 / P2 and probe 3 / P8: the parity sieve theorem — plus the
exact-arithmetic law (law 5) enforced by token scan."""
import io
import tokenize

import numpy as np

import amem.contraction
import amem.harness
from amem import AbsoluteField
from amem import constants as K
from amem.contraction import contraction_for


def test_sieve_theorem_264_264():
    """One indraw tick on a saturated absolute field splits the 528
    non-center cells exactly in half by parity: 264 pass, 264 strand."""
    e = AbsoluteField(seed=2)
    e.a[:] = 1.0
    e.w[:] = 0.8
    e.last_passed = e.last_rejected = 0
    e._indraw_tick(write_sig=False)
    assert e.last_passed == 264
    assert e.last_rejected == 264


def test_contraction_map_structure():
    con = contraction_for(K.GRID)
    c = con.center
    fate = con.journey_fate()

    # the center is nobody's journey
    assert fate[c, c] == 0
    # every non-center core-zone cell has already arrived
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                assert fate[c + dy, c + dx] == 1
    # outside the core zone, odd parity strands immediately
    for y in range(K.GRID):
        for x in range(K.GRID):
            rx, ry = x - c, y - c
            if max(abs(rx), abs(ry)) > 1 and (rx + ry) % 2 != 0:
                assert fate[y, x] == 2
    # arrivals + strandings account for every non-center cell
    assert int((fate == 1).sum()) + int((fate == 2).sum()) == K.N - 1

    # signature index geometry: mass can never land on the core center
    assert not (con.sig_at_src == 4).any()


def test_no_float_arithmetic_in_decision_modules():
    """Law 5: alignment certification and contraction decisions are
    integer-only. No float literals, no true division, in harness.py or
    contraction.py."""
    for module in (amem.harness, amem.contraction):
        with open(module.__file__, "r", encoding="utf-8") as f:
            source = f.read()
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.NUMBER:
                s = tok.string.lower()
                assert "." not in s and "e" not in s and "j" not in s, \
                    f"float literal {tok.string!r} in {module.__name__}"
            if tok.type == tokenize.OP:
                assert tok.string != "/", \
                    f"true division in {module.__name__}"
