"""The decode boundary (Phase 2 ruling R-1).

Phase 1 removed the signature-decode path from the physics entirely
(law 3: the core selects, it never paints). This module keeps the
boundary *reintroducible*: everything the recall path does with a
signature goes through a Selector, and the only shipped Selector is
pure identity selection — nearest cosine against the library, no
spatial decoding anywhere.

If a future phase ever revisits decoding, it happens by providing a
different Selector here — never by touching the field engines.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class Selector(Protocol):
    """select(signature, library) -> (mid, score, scores). Must not touch
    any field state: selection is a pure read of the library."""

    def select(self, signature, library):
        ...


class CosineSelector:
    """The identity-only default: nearest cosine, gauge chosen by the
    signature's dimension (9 legacy / 54 radius / 150 combo)."""

    def select(self, signature, library):
        return library.classify(signature)


DEFAULT_SELECTOR = CosineSelector
