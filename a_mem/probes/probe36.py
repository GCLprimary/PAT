"""Probe 36: THE DUAL RULER (linear ad quadratum) + stamped registers.
Each cell contributes to two paths: side ruler 4n, diagonal ruler 4*sqrt2*n
(constant baked-in differential 4(sqrt2-1)); exact arithmetic in Z[sqrt2]
as integer pairs (m, n) = m + n*sqrt2 -- no float ever evaluated.
Stamped RegisterBank: open() records the exact stamp; close() binds to the
most-recent-open register (exact integer comparison) -> stack behavior.
MEASURED: single dependency 100% at gaps 2-40 (distance-blind);
nested deps: unstamped bank ~50% (chance), STAMPED 100% at every gap;
fixed windows structurally blind past their width.
Core:
    def stamp(i): return (4*i, 4*i)          # exact Z[sqrt2] pair
    j = argmax(stamp_m of open registers)    # most-recent-open, exact
"""
