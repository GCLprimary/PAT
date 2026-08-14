"""R-2: the stamped register bank (probe 36) — long-distance binding.

A register opens carrying features and the EXACT √2 stamp of its
position; a close binds to the most-recent-open register by exact stamp
comparison — stack behavior earned from arithmetic, not from a stack.
Because stamps never repeat (the aperiodic ruler), nesting is decidable
at any distance: measured 100% at every gap 2–40 where fixed windows go
structurally blind past their width and an unstamped bank falls to
chance (~50%) the moment dependencies nest.

`peek()` consults the most-recent-open register without closing it —
the read path for checkers (the agreement register uses this shape).
"""
from dataclasses import dataclass, field

from .rulers import Stamp


@dataclass
class Register:
    features: dict
    stamp: Stamp
    open: bool = True
    closed_by: Stamp | None = None


class RegisterBank:
    def __init__(self):
        self.registers = []

    def open(self, features, stamp):
        reg = Register(dict(features), stamp)
        self.registers.append(reg)
        return reg

    def _most_recent_open(self):
        best = None
        for reg in self.registers:
            if reg.open and (best is None or best.stamp < reg.stamp):
                best = reg
        return best

    def peek(self):
        """Consult without closing (checkers use this)."""
        return self._most_recent_open()

    def close(self, stamp):
        """Bind to the most-recent-open register, by exact stamps."""
        reg = self._most_recent_open()
        if reg is None:
            return None
        reg.open = False
        reg.closed_by = stamp
        return reg

    def open_count(self):
        return sum(1 for r in self.registers if r.open)


class UnstampedBank:
    """The comparison run: same interface, no ordering — a close picks
    uniformly among open registers. Kept so the nested-stream tests can
    show what the stamps are FOR (~50% on nested pairs, i.e. chance)."""

    def __init__(self, rng):
        self.registers = []
        self.rng = rng

    def open(self, features, stamp):
        reg = Register(dict(features), stamp)
        self.registers.append(reg)
        return reg

    def close(self, stamp):
        candidates = [r for r in self.registers if r.open]
        if not candidates:
            return None
        reg = candidates[int(self.rng.integers(len(candidates)))]
        reg.open = False
        reg.closed_by = stamp
        return reg
