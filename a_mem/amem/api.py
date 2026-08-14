"""Agent-facing API: the Memory class.

Recall is resonate -> select -> complete: a cue (partial anchors, a noisy
signature, or a known episode id) selects a library entry; the entry's
anchors are deployed onto a flattened stage; the field's alignment
dynamics complete the pattern. Signature selection goes through the
decode boundary (amem.decode, ruling R-1) and is never decoded into the
field (law 3); the stage holds one memory at a time (law 1); every
tenant change begins with a page-turn (law 2).

Phase 3: the classification code is the 54-dim radius-channel signature
(D-2); 9-dim signatures still classify (legacy, warns); core_mode="combo"
adds the 150-dim ring x radius code for small libraries. Completion
trajectories are logged into a runtime calibration buffer (W-3).
"""
import warnings
from dataclasses import dataclass, field

import numpy as np

from . import constants as K
from .absolute import AbsoluteField
from .clock import (AdaptiveDwell, CalibratedDwell, DeltaDwell, FixedDwell,
                    page_turn, run_dwell)
from .decode import CosineSelector, Selector
from .field import Field
from .library import Entry, Library, cells_to_mask, cosine

CORE_MODES = ("radius", "combo")
CLOCK_MODES = ("level", "calibrated", "delta")


@dataclass
class RecallResult:
    reconstruction: np.ndarray      # (grid, grid) bool trap map
    identity: str | None            # selected / judged library id
    confidence: float               # anchor-completion fraction
    dwell: int                      # beats used
    scores: dict = field(default_factory=dict)
    target: str | None = None       # sequence only: the requested id
    trajectory: list = field(default_factory=list)   # confidence per beat


def _normalize_pattern(pattern, grid):
    cells = sorted({(int(x), int(y)) for x, y in pattern})
    if not cells:
        raise ValueError("pattern is empty")
    for x, y in cells:
        if not (0 <= x < grid and 0 <= y < grid):
            raise ValueError(f"cell {(x, y)} outside {grid}x{grid} lattice")
    return cells


class Memory:
    """Three organs: the stage (normalized field), the anchor library
    (absolute-gauge skeletons), and the core (contraction signatures,
    classification only — through the decode boundary)."""

    def __init__(self, grid=K.GRID, seed=0, path="~/a_mem/store",
                 violence=K.VIOLENCE, decay=K.DECAY, autosave=True,
                 core_mode="radius", clock="level", selector=None):
        if core_mode not in CORE_MODES:
            raise ValueError(f"core_mode must be one of {CORE_MODES}")
        if clock not in CLOCK_MODES:
            raise ValueError(f"clock must be one of {CLOCK_MODES}")
        self.grid = grid
        self.autosave = autosave
        self.core_mode = core_mode
        self.clock_mode = clock
        self.selector: Selector = selector if selector is not None \
            else CosineSelector()
        self._rng = np.random.default_rng(seed)
        self.stage = Field(grid=grid, seed=int(self._rng.integers(2**31)),
                           violence=violence, decay=decay)
        self.scribe = AbsoluteField(grid=grid, seed=int(self._rng.integers(2**31)),
                                    violence=0.0, decay=decay)
        self.library = Library(path=path, grid=grid)
        self._clock_log = []            # W-3 runtime calibration buffer

    # ── write ────────────────────────────────────────────────────────
    def write(self, pattern, meta=None):
        """Store one memory: absolute anchor write + normalized imprint.

        Returns the new memory id. The write-time overlap report (law 6)
        is stored in the entry metadata; overlapping identities cap
        recall purity permanently, so a flagged report is a real warning.
        """
        cells = _normalize_pattern(pattern, self.grid)

        anchors = self.scribe.write_anchors(cells)

        self.stage.reset()
        self.stage.stamp(cells)
        for _ in range(K.IMPRINT_BEATS):
            self.stage.beat(write_sig=True)
        sig = self.stage.sig.copy()
        sig_rad = self.stage.sig_rad.ravel().copy()
        sig_rr = (self.stage.sig_rr.ravel().copy()
                  if self.core_mode == "combo" else None)
        imprint = self.stage.trap_map().copy()

        report = self.library.overlap_report(imprint)
        mid = self.library.new_mid()
        entry_meta = {"pattern": [[x, y] for x, y in cells],
                      "overlap_report": report}
        if meta:
            entry_meta.update(meta)
        self.library.add(Entry(mid=mid, sig=sig, sig_rad=sig_rad,
                               sig_rr=sig_rr, anchors=anchors,
                               imprint=imprint, meta=entry_meta))
        if self.autosave:
            self.library.save()
        return mid

    # ── recall ───────────────────────────────────────────────────────
    def recall(self, cue=None, signature=None, mid=None,
               beats=K.REBUILD_BEATS):
        """Resonate -> select -> complete.

        cue:       iterable of (x, y) partial-anchor cells. Selects the
                   entry whose skeleton best matches the cue; the cue
                   itself is deployed and completed.
        signature: core code (54-dim radius default; 9-dim legacy warns;
                   150-dim combo). Selection goes through the decode
                   boundary; a random half of the selected entry's
                   anchors is deployed and completed.
        mid:       known episode id (the hybrid-encoder route, D-1):
                   skip selection, deploy half-anchors, complete.
        """
        provided = [x is not None for x in (cue, signature, mid)]
        if sum(provided) != 1:
            raise ValueError("provide exactly one of cue=, signature= or mid=")
        if len(self.library) == 0:
            raise ValueError("recall on an empty library")

        if signature is not None:
            sig = np.asarray(signature, dtype=float).ravel()
            if sig.size == K.SIG_DIM:
                warnings.warn(
                    "9-dim signatures are the legacy angular code; the "
                    "radius-channel 54-dim code is the Phase 3 default",
                    stacklevel=2)
            selected, _, scores = self.selector.select(sig, self.library)
            entry = self.library.get(selected)
            deploy_cells = self._half_anchors(entry.anchors)
        elif mid is not None:
            selected = mid
            entry = self.library.get(selected)
            scores = {selected: 1.0}
            deploy_cells = self._half_anchors(entry.anchors)
        else:
            cue_cells = _normalize_pattern(cue, self.grid)
            cue_mask = cells_to_mask(cue_cells, self.grid)
            selected, _, scores = self.library.classify_cue(cue_mask)
            entry = self.library.get(selected)
            deploy_cells = cue_cells

        page_turn(self.stage)
        self.stage.deploy(deploy_cells)
        trajectory = []
        for _ in range(beats):
            self.stage.beat(write_sig=False)
            trajectory.append(self.stage.confidence(entry.anchors))
        self._clock_log.append({"kind": "recall", "target": selected,
                                "dwell": beats, "trajectory": trajectory})

        return RecallResult(
            reconstruction=self.stage.trap_map().copy(),
            identity=selected,
            confidence=trajectory[-1] if trajectory else 0.0,
            dwell=beats,
            scores=scores,
            trajectory=trajectory,
        )

    # ── serial recall ────────────────────────────────────────────────
    def sequence(self, mids, dwell=K.DWELL_DEFAULT):
        """Page-turned serial procession over stored memories.

        dwell: an int (fixed beats per tenant), a policy instance, or one
        of "adaptive" (this Memory's configured clock), "level",
        "calibrated", "delta".
        """
        policy = self._resolve_dwell(dwell)
        results = []
        for mid in mids:
            entry = self.library.get(mid)
            page_turn(self.stage)
            self.stage.deploy(self._half_anchors(entry.anchors))
            used, trajectory = run_dwell(
                self.stage, entry.anchors, policy, write_sig=False,
                c1_samples=self._c1_samples())
            self._clock_log.append({"kind": "sequence", "target": mid,
                                    "dwell": used, "trajectory": trajectory})
            recon = self.stage.trap_map().copy()
            scores = {m: cosine(self.stage.w, self.library.get(m).imprint.astype(float))
                      for m in self.library.mids()}
            holder = max(scores, key=scores.get)
            results.append(RecallResult(
                reconstruction=recon,
                identity=holder,
                confidence=trajectory[-1] if trajectory else 0.0,
                dwell=used,
                scores=scores,
                target=mid,
                trajectory=trajectory,
            ))
        return results

    # ── maintenance ──────────────────────────────────────────────────
    def forget(self, mid):
        """Remove a library entry. The stage is unaffected."""
        self.library.remove(mid)
        if self.autosave:
            self.library.save()

    def calibrate(self):
        """Measure the flat-field self-portrait on the absolute engine
        (law 4) and store it. Never superposed onto the stage."""
        portrait = self.scribe.calibrate()
        self.library.flat_sig = portrait
        if self.autosave:
            self.library.save()
        return portrait

    def stats(self):
        mids, overlap = self.library.pairwise_overlap()
        flagged = [(mids[i], mids[j], float(overlap[i, j]))
                   for i in range(len(mids)) for j in range(i + 1, len(mids))
                   if overlap[i, j] >= K.OVERLAP_DANGER]
        c1 = self._c1_samples()
        clock = {"policy": self.clock_mode, "samples": len(c1)}
        if c1:
            arr = np.asarray(c1)
            clock.update(
                c1_mean=float(arr.mean()),
                c1_quantiles=[float(np.quantile(arr, q))
                              for q in (0.25, 0.5, 0.75)])
        return {
            "budget": self.stage.defined_frac(),
            "library_size": len(self.library),
            "mids": mids,
            "overlap_matrix": overlap,
            "flagged_pairs": flagged,
            "calibrated": self.library.flat_sig is not None,
            "stage_beats": self.stage.beats,
            "core_mode": self.core_mode,
            "clock": clock,
        }

    # ── internals ────────────────────────────────────────────────────
    def _half_anchors(self, anchor_mask, fraction=K.CUE_FRACTION):
        cells = np.argwhere(anchor_mask)          # (k, 2) as (y, x)
        k = max(1, int(len(cells) * fraction))
        pick = cells[self._rng.choice(len(cells), size=k, replace=False)]
        return [(int(x), int(y)) for y, x in pick]

    def _c1_samples(self):
        return [rec["trajectory"][0] for rec in self._clock_log
                if rec["trajectory"]]

    def _resolve_dwell(self, dwell):
        if isinstance(dwell, int):
            return FixedDwell(dwell)
        if isinstance(dwell, (FixedDwell, AdaptiveDwell, CalibratedDwell,
                              DeltaDwell)):
            return dwell
        name = dwell if dwell != "adaptive" else self.clock_mode
        if name == "level":
            return AdaptiveDwell()
        if name == "calibrated":
            return CalibratedDwell()
        if name == "delta":
            return DeltaDwell()
        raise ValueError(f"unknown dwell policy: {dwell!r}")
