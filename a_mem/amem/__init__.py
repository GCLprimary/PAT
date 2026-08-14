"""a_mem: associative memory for software agents.

Three organs, each with a measured role:
  the Field (stage)     — normalized homeostatic lattice, residency = 1
  the Anchor Library    — exact absolute-gauge skeletons, the primary store
  the Core              — contraction signatures, classification only

Public entry point: Memory.
"""
from . import constants
from .absolute import AbsoluteField
from .api import Memory, RecallResult
from .clock import (AdaptiveDwell, CalibratedDwell, DeltaDwell, FixedDwell,
                    page_turn)
from .decode import CosineSelector, Selector
from .encoder import (Encoder, EmbeddingIndex, NumpyEmbeddingIndex,
                      PlacementFull)
from .field import Field
from .hooks import EpisodeHooks
from .library import Entry, Library, cosine

__version__ = "0.2.0"

__all__ = [
    "Memory", "RecallResult", "Field", "AbsoluteField",
    "Library", "Entry", "cosine",
    "FixedDwell", "AdaptiveDwell", "CalibratedDwell", "DeltaDwell",
    "page_turn",
    "Selector", "CosineSelector",
    "Encoder", "EmbeddingIndex", "NumpyEmbeddingIndex", "PlacementFull",
    "EpisodeHooks",
    "constants", "__version__",
]
