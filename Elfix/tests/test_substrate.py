from elfix.substrate.features import features, sonority, inventory
from elfix.substrate.vectors import vector, DIM

def test_p_b_differ_only_in_voicing():
    p, b = features("p"), features("b")
    assert p.place == b.place and p.manner == b.manner and p.voiced != b.voiced

def test_total_unknown_returns_none():
    assert features("zzz") is None and vector("zzz") is None

def test_sonority_order():
    assert sonority("p") < sonority("s") < sonority("n") < sonority("l") < sonority("AE")

def test_vector_dim_and_vowel_flag():
    assert len(vector("p")) == DIM
    assert vector("IY")[1] == 1.0 and vector("p")[1] == 0.0

def test_inventory_nonempty():
    assert len(inventory()) >= 38
