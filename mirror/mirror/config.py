"""Path resolution for the organs mirror composes but does not own.

mirror imports the ElfIX repo (feature space, data contract) and a_mem
(episodic memory). a_mem is a normal installed package; ElfIX is a
research repo located by path:

  1. the MIRROR_ELFIX_PATH environment variable, if set;
  2. Elfix as a SIBLING of the mirror repo (the umbrella layout — all
     four project folders under one parent);
  3. ~/Elfix (the spec's original default);
  4. ~/OneDrive/Desktop/Elfix (an earlier home on this machine).

The corpus (Brown running text in the ElfIX data contract) resolves to
ElfIX's data/corpus.txt when present; otherwise mirror builds it into its
own data/ directory via meaning.build_corpus — mirror never writes into
the ElfIX repo.
"""
import os
import sys
from pathlib import Path

MIRROR_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = MIRROR_ROOT / "data"

_CANDIDATES = [
    MIRROR_ROOT.parent / "Elfix",
    Path.home() / "Elfix",
    Path.home() / "OneDrive" / "Desktop" / "Elfix",
]


def elfix_path():
    env = os.environ.get("MIRROR_ELFIX_PATH")
    candidates = ([Path(env)] if env else []) + _CANDIDATES
    for cand in candidates:
        if (cand / "elfix" / "substrate" / "features.py").exists():
            return cand
    raise FileNotFoundError(
        "ElfIX repo not found. Set MIRROR_ELFIX_PATH or place the repo at "
        + " or ".join(str(c) for c in _CANDIDATES))


def ensure_elfix_importable():
    root = str(elfix_path())
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


def cmu_path():
    p = elfix_path() / "data" / "cmu_preprocessed.txt"
    if not p.exists():
        raise FileNotFoundError(f"CMU data not found at {p}")
    return p


def corpus_path():
    """Resolve the running-text corpus; None if it must be built first."""
    for cand in (elfix_path() / "data" / "corpus.txt",
                 DATA_DIR / "corpus.txt"):
        if cand.exists():
            return cand
    return None


def corpus_build_target():
    """Where mirror builds the corpus when ElfIX doesn't carry one."""
    return DATA_DIR / "corpus.txt"
