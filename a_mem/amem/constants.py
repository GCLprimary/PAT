"""Canonical constants of the a_mem substrate.

Every number here was fixed empirically during the Alignment Field probe
campaign (suites 1-12). None are tunable aesthetics; changing them moves
the system off its validated operating point.

Float constants live here and in the engines only. harness.py and
contraction.py — the alignment-certification and contraction-decision
zone — contain no float arithmetic (enforced by tests/test_sieve.py).
"""

# ── lattice ──────────────────────────────────────────────────────────
GRID = 23                     # default stage side; must be odd
N = GRID * GRID               # cell count; uniform share u = 1/N
CENTER = (GRID - 1) // 2      # core center index (both axes)

# ── alignment families (squared integer distances) ───────────────────
FAMILY_INT = (9, 16, 25)          # the integer family
FAMILY_QUAD = (2, 8, 18, 32)      # the quadratic (diagonal) family

# ── stroke lengths (ticks per beat) ──────────────────────────────────
OUTPOUR_TICKS = 3
AUDIT_TICKS = 18
INDRAW_TICKS = 6
BURST_R = 4                   # spray reach (Chebyshev radius)

# ── absolute-gauge thresholds (fixed rulers, real zero) ──────────────
ABS_ACTIVE = 0.35             # membership / sustainment gate
ABS_RELAY = 0.30              # indraw participation
ABS_DIG = 0.60                # trap-digging gate
ABS_SRC = 0.85                # spray source gate
ABS_QUIET = 0.20              # trap-erosion gate
ABS_FLOOR = 0.001             # hard zero floor (absolute gauge only)
ABS_STAMP = 1.0               # stamp amplitude

# ── normalized-gauge thresholds (multiples of the uniform share) ─────
NORM_ACTIVE_U = 3.0
NORM_RELAY_U = 2.5
NORM_DIG_U = 6.0
NORM_SRC_U = 8.0
NORM_QUIET_U = 1.5
NORM_STAMP_U = 10.0           # stamp amplitude in units of 1/N
NORM_CUE_U = 10.0             # anchor-deployment amplitude in units of 1/N

# ── shared dynamics rates ────────────────────────────────────────────
DECAY = 0.05                  # default decay rate
VIOLENCE = 0.45               # default spray amplitude
OUTPOUR_DECAY_SCALE = 0.3     # decay softening during outpour
TRAP_SHIELD = 0.75            # traps slow decay: a -= d*a*(1 - TRAP_SHIELD*w)
TRAP_DIG_RATE = 0.014         # w += rate*(1-w) where a > dig threshold
TRAP_ERODE = 0.996            # w *= erode where a < quiet threshold
SUSTAIN_RATE = 0.022          # member sustainment boost per aligned neighbor
SPRAY_GATE_P = 0.5            # per-cell spray gate probability
SPRAY_SCALE = 0.3             # spray amplitude factor (times violence)
ANCHOR_SRC_W = 0.25           # trap depth that makes a cell a spray source
TRAP_T = 0.4                  # trap map threshold: defined means w > TRAP_T
STAMP_W0 = 0.45               # default trap depth stamped at imprint

# ── contraction mass split (dynamics, not decision) ──────────────────
CARRY_FRAC = 0.45             # fraction of activation carried inward per tick
RETAIN_FRAC = 0.6             # fraction retained at the source cell

# ── protocol lengths (probe-validated) ───────────────────────────────
ANCHOR_TICKS = 80             # quiet ticks for the absolute anchor write
IMPRINT_BEATS = 8             # normalized beats per write (signature collection)
REBUILD_BEATS = 6             # beats per single recall completion
CUE_FRACTION = 0.5            # fraction of anchors deployed as a cue

# ── clock defaults ───────────────────────────────────────────────────
DWELL_DEFAULT = 1             # beats per tenant in serial recall
ADAPTIVE_THETA = 0.7          # page-turn when confidence >= theta
ADAPTIVE_CAP = 4              # hard dwell cap for the adaptive clock

# ── write-time hygiene ───────────────────────────────────────────────
OVERLAP_DANGER = 0.45         # overlap >= this at write is flagged (law 6)

# ── the canonical aligned shapes ─────────────────────────────────────
SEED_CONSTELLATION = ((0, 0), (3, 0), (0, 4), (3, 4), (1, 1), (2, 2), (3, 3))
LINE_CONSTELLATION = ((0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3))

# ── radius channel (Phase 3, D-2): hop-age binned core codes ─────────
HOP_BINS = 6                  # hop-age bins per core cell
RING_HALF = 2                 # combo mode taps the 5x5 ring around center
SIG_DIM = 9                   # legacy angular code (3x3 core)
SIG_RAD_DIM = 9 * HOP_BINS    # 54: the default classification code (D-2)
SIG_RR_DIM = 25 * HOP_BINS    # 150: optional ring x radius combo code

# ── encoder placement (Phase 3, D-1/D-3) ─────────────────────────────
PLACE_ZONE_MIN = 2            # placement zone is 2..14 on both axes
PLACE_ZONE_MAX = 14           # (13-wide; ~9 slots at Chebyshev-5 packing)
PLACE_MIN_SEP = 5             # below this Chebyshev separation the zone is full
PLACE_RELOCATE_TRIES = 8      # candidate retries before store-with-warning

# ── clock v2 scaffolding (Phase 3, D-4) ──────────────────────────────
CLOCK_MIN_SAMPLES = 30        # calibrated policy self-tunes after this many c1s
CLOCK_QUANTILE = 0.5          # calibrated threshold = this quantile of c1
CLOCK_DELTA_FLOOR = 0.05      # delta policy: turn early iff c2-c1 < this ...
CLOCK_C1_FLOOR = 0.30         # ... and c1 > this (fast crystallization)
