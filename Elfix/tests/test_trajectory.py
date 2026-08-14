from elfix.trajectory.trajectory import Trajectory
from elfix.emergent.emergent_unit import geometry_boundaries

def test_plant_is_one_syllable_arch():
    t = Trajectory.of(["p","l","AE","n","t"])
    assert t.contour == [1.0,4.0,5.0,3.0,1.0]
    assert t.syllable_count() == 1

def test_running_two_syllables():
    t = Trajectory.of(["r","AH","n","IH","NG"])
    assert t.syllable_count() == 2

def test_morpheme_boundary_recovered_for_cats():
    # cat + s -> boundary before the final s (index 3)
    assert 3 in geometry_boundaries(["k","AE","t","s"])
