"""Shared creature-level fixtures. The organ bundle loads once per
session; the pinned fixture files are verified against their checksums
before any battery runs (law 3)."""
import hashlib
import json
from pathlib import Path

import pytest

from pat import get_organs

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="session")
def organs():
    return get_organs()


@pytest.fixture(scope="session", autouse=True)
def verify_checksums():
    """Law 3: the batteries run on the pinned artifacts or not at all."""
    checks = json.loads((FIX / "checksums.json").read_text(encoding="utf-8"))
    from mirror.config import DATA_DIR as MIRROR_DATA
    for name, expected in checks.items():
        path = (MIRROR_DATA / name.split("/", 1)[1]
                if name.startswith("mirror/") else FIX / name)
        actual = sha256(path)
        assert actual == expected, \
            f"pinned artifact {name} changed (checksum mismatch) — " \
            f"regeneration is a probe, not a refresh"


@pytest.fixture(scope="session")
def learning_stream():
    return json.loads((FIX / "learning_stream.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="session")
def composition():
    return json.loads((FIX / "composition_inputs.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="session")
def relatives():
    return json.loads((FIX / "relatives.json").read_text(encoding="utf-8"))
