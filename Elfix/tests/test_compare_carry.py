import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.compare.all_pairs import attention
from elfix.carry.decaying_carry import (DecayingCarry, measure_decay_rate,
                                          EARNED_RATE)
from elfix.data_io import load_cmu

def test_attention_rows_normalised():
    W = attention([[1,0],[1,0],[0,1]])
    assert abs(sum(W[0]) - 1.0) < 1e-9
    assert W[0][1] > W[0][2]

def test_carry_recent_dominates():
    c = DecayingCarry(2, rate=0.5)
    c.update([1.0,0.0]); s = c.update([0.0,1.0])
    assert s[1] > s[0]

def test_carry_default_rate_is_earned():
    """Law 1/3: the default retention is the re-derivable phoneme-MI half-life
    rate, a real number in (0,1), not a magic constant. On the full corpus it
    reproduces EARNED_RATE; on any corpus it is a sane fraction."""
    r = measure_decay_rate(load_cmu().values())
    assert 0.0 < r < 1.0
    corpus = list(load_cmu().values())
    if len(corpus) > 50_000:
        assert abs(r - EARNED_RATE) < 0.05
