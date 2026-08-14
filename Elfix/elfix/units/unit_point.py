"""
elfix/units/unit_point.py  —  Tier 1: a unit as centre + width
================================================================
PROVENANCE: [ElfIX] relational (why_piece15) — "never report a centre without
its width". A high-support, peaked unit pins tight; a low-support or flat one
stays honestly wide. Absence != zero at the unit level (Law 2, Law 4).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import math


@dataclass
class UnitPoint:
    centroid: List[float]
    width: float          # mean L2 distance of members to centroid
    support: int          # how many observations earned this position

    @classmethod
    def of(cls, members: List[List[float]]) -> "UnitPoint":
        if not members:
            return cls([], 0.0, 0)
        dim = len(members[0])
        cen = [sum(m[k] for m in members) / len(members) for k in range(dim)]
        width = sum(
            math.sqrt(sum((m[k] - cen[k]) ** 2 for k in range(dim)))
            for m in members
        ) / len(members)
        return cls(cen, round(width, 4), len(members))

    def is_settled(self, max_width: float) -> bool:
        """A unit is 'settled' only when its width is tight AND support is real.
        Width threshold must be earned from the data, not hand-set (Law 1)."""
        return self.support >= 3 and self.width <= max_width
