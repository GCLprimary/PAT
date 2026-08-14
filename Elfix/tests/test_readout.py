from elfix.readout.recognition import (recognition_ratio,
    score_to_temperature, recognition_temperature)

def test_temperature_endpoints():
    assert score_to_temperature(1.0) == 0.3
    assert score_to_temperature(0.0) == 2.0

def test_low_evidence_low_score():
    known = {"a","b","c"}
    assert recognition_ratio(list("ab"), lambda s: s in known, 10) == 0.2

def test_recognition_temperature_composes():
    known = {"a"}
    t = recognition_temperature(list("aaaaaaaaaa"), lambda s: s in known, 10)
    assert t == 0.3
