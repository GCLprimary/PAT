"""
elfix/laws.py  —  the inviolable design laws, as checkable helpers
====================================================================
The six laws from SPEC.md, with a couple of runtime asserts so violations fail
loudly rather than drift. Import and call these in tests/new code.
"""
from __future__ import annotations

LAWS = [
    "1. Earned geometry only — no constant whose value comes from outside the data.",
    "2. Absence != zero — forbidden (structural) and unattested (evidential) never collapse.",
    "3. One source of truth — derived sets are views of one ground table, asserted in test.",
    "4. Never a centre without its width.",
    "5. Ternary evidence — attested(+1) / silent(0) / evidenced-against(-1).",
    "6. Readable AND self-forming — no gradient black box in the core.",
]


def assert_has_width(unit) -> None:
    """Law 4: any reported unit position must carry a width/spread field."""
    if not hasattr(unit, "width") and not hasattr(unit, "spread"):
        raise AssertionError("Law 4 violated: a centre was reported without its width.")


def assert_earned(value_name: str, source: str) -> None:
    """Law 1 reminder: document where a constant came from. `source` must name
    a corpus measurement or articulatory fact, not an external/aesthetic origin."""
    banned = ("phi", "golden", "mersenne", "omega", "pi2", "cosmolog", "dual-13")
    if any(b in source.lower() for b in banned):
        raise AssertionError(
            f"Law 1 violated: '{value_name}' sourced from imported geometry ({source}).")


if __name__ == "__main__":
    print("\n".join(LAWS))
