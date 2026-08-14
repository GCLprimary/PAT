"""Session fixtures: the organs are expensive to build, build them once."""
import numpy as np
import pytest

from mirror import Embedder, MeaningGeometry, Transform, mine_pairs


@pytest.fixture(scope="session")
def embedder():
    return Embedder()


@pytest.fixture(scope="session")
def transform(embedder):
    return Transform(embedder).fit(mine_pairs(embedder.corpus))


@pytest.fixture(scope="session")
def geometry():
    return MeaningGeometry()


def angle_noise(e, c, rng):
    """Fixed-angle perturbation: cos(noisy, e) = c exactly (probe 18)."""
    g = rng.normal(size=len(e))
    g -= (g @ e) * e
    g /= np.linalg.norm(g)
    v = e * c + g * np.sqrt(1 - c * c)
    return v / np.linalg.norm(v)
