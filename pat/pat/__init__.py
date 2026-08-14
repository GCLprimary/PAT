"""agent: the shell — a creature composed from a_mem and mirror.

It perceives input, recalls against what it actually knows, acts from a
five-verb repertoire, refuses everything else by name, and learns only
at teachable moments — refusal plus confirmation, with receipts.
"""
from .chapters import (Chapter, ChapterAddresser, Circulation, cells_of,
                       deserialize, receipts_of, serialize, synthesize)
from .discovery import (discover, no_such_stem_class, register,
                        retire_atoms, write_artifact)
from .loop import Agent, ClauseResponse, Response, render
from .organs import Organs, get_organs
from .reading import ReadingSession
from .repertoire import Act, ExactRouter, Repertoire, Router, VERBS

__version__ = "0.1.0"

__all__ = [
    "Agent", "Response", "ClauseResponse", "render",
    "Organs", "get_organs", "ReadingSession",
    "Chapter", "ChapterAddresser", "Circulation", "synthesize",
    "receipts_of", "serialize", "deserialize", "cells_of",
    "Repertoire", "Act", "Router", "ExactRouter", "VERBS",
    "__version__",
]
