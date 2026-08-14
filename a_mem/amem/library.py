"""The anchor library: the primary store.

Each entry is one memory: its 9-cell core signature (who), its exact
absolute-gauge anchor skeleton (where), and metadata including the
write-time overlap report (law 6: purity ceilings are set at write time —
Phase 1 measures and reports overlap, it does not yet separate).

The signature's only runtime job is classification by nearest cosine
against this library (law 3). Persistence is a single JSON file with
atomic replace; masks are stored as sorted cell lists.
"""
import json
import os
import tempfile
from dataclasses import dataclass, field

import numpy as np

from . import constants as K

STORE_VERSION = 2      # v2 adds the radius-channel codes; v1 stores still load


def cosine(u, v):
    u = np.asarray(u, dtype=float).ravel()
    v = np.asarray(v, dtype=float).ravel()
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        return 0.0
    return float(u @ v / (nu * nv))


def mask_to_cells(mask):
    """Bool (grid, grid) mask -> sorted list of [x, y]."""
    ys, xs = np.nonzero(mask)
    return sorted([int(x), int(y)] for x, y in zip(xs, ys))


def cells_to_mask(cells, grid):
    mask = np.zeros((grid, grid), dtype=bool)
    for x, y in cells:
        if not (0 <= x < grid and 0 <= y < grid):
            raise ValueError(f"cell {(x, y)} outside {grid}x{grid} lattice")
        mask[int(y), int(x)] = True
    return mask


@dataclass
class Entry:
    mid: str
    sig: np.ndarray            # (9,) float — legacy angular code
    anchors: np.ndarray        # (grid, grid) bool — the exact skeleton
    imprint: np.ndarray        # (grid, grid) bool — trap map at write time
    sig_rad: np.ndarray | None = None   # (54,) radius-channel code (default)
    sig_rr: np.ndarray | None = None    # (150,) ring x radius combo code
    meta: dict = field(default_factory=dict)


class Library:
    def __init__(self, path=None, grid=K.GRID):
        self.grid = grid
        self.path = None if path is None else os.path.expanduser(str(path))
        self.entries: dict[str, Entry] = {}
        self.flat_sig = None       # calibration portrait; stored, never painted
        self._next_id = 1
        if self.path is not None and os.path.exists(self._store_file()):
            self.load()

    # ── ids ──────────────────────────────────────────────────────────
    def new_mid(self):
        mid = f"m{self._next_id:04d}"
        self._next_id += 1
        return mid

    # ── access ───────────────────────────────────────────────────────
    def __len__(self):
        return len(self.entries)

    def __contains__(self, mid):
        return mid in self.entries

    def get(self, mid):
        if mid not in self.entries:
            raise KeyError(f"unknown memory id: {mid}")
        return self.entries[mid]

    def mids(self):
        return list(self.entries)

    def add(self, entry):
        self.entries[entry.mid] = entry

    def remove(self, mid):
        if mid not in self.entries:
            raise KeyError(f"unknown memory id: {mid}")
        del self.entries[mid]

    # ── selection ────────────────────────────────────────────────────
    def _code_for(self, entry, dim):
        if dim == K.SIG_DIM:
            return entry.sig
        if dim == K.SIG_RAD_DIM:
            return entry.sig_rad
        if dim == K.SIG_RR_DIM:
            return entry.sig_rr
        raise ValueError(
            f"signature must be {K.SIG_DIM} (legacy), {K.SIG_RAD_DIM} "
            f"(radius) or {K.SIG_RR_DIM} (combo) dims, got {dim}")

    def classify(self, sig):
        """Nearest-cosine identity for a (possibly noisy) signature.

        The code gauge is chosen by dimension: 9 = legacy angular,
        54 = radius channel (the D-2 default), 150 = ring x radius combo.
        """
        if not self.entries:
            raise ValueError("cannot classify against an empty library")
        sig = np.asarray(sig, dtype=float).ravel()
        codes = {mid: self._code_for(e, sig.size)
                 for mid, e in self.entries.items()}
        missing = [mid for mid, c in codes.items() if c is None]
        if missing:
            raise ValueError(
                f"entries {missing} lack a {sig.size}-dim code "
                f"(legacy store? re-write or classify with 9-dim signatures)")
        scores = {mid: cosine(sig, c) for mid, c in codes.items()}
        best = max(scores, key=scores.get)
        return best, scores[best], scores

    def classify_cue(self, cue_mask):
        """Nearest-cosine identity for a partial-anchor cue mask."""
        if not self.entries:
            raise ValueError("cannot classify against an empty library")
        scores = {mid: cosine(cue_mask.astype(float), e.anchors.astype(float))
                  for mid, e in self.entries.items()}
        best = max(scores, key=scores.get)
        return best, scores[best], scores

    # ── write-time hygiene (law 6) ───────────────────────────────────
    def overlap_report(self, imprint):
        """Cosine of a candidate imprint against every stored imprint."""
        report = {mid: cosine(imprint.astype(float), e.imprint.astype(float))
                  for mid, e in self.entries.items()}
        worst = max(report.values(), default=0.0)
        return {"overlaps": report, "max_overlap": worst,
                "flagged": worst >= K.OVERLAP_DANGER}

    def pairwise_overlap(self):
        mids = self.mids()
        n = len(mids)
        m = np.zeros((n, n))
        for i, a in enumerate(mids):
            for j, b in enumerate(mids):
                m[i, j] = cosine(self.entries[a].imprint.astype(float),
                                 self.entries[b].imprint.astype(float))
        return mids, m

    # ── persistence ──────────────────────────────────────────────────
    def _store_file(self):
        return os.path.join(self.path, "store.json")

    def save(self):
        if self.path is None:
            return
        os.makedirs(self.path, exist_ok=True)
        payload = {
            "version": STORE_VERSION,
            "grid": self.grid,
            "next_id": self._next_id,
            "flat_sig": None if self.flat_sig is None
                        else [float(v) for v in self.flat_sig],
            "entries": {
                mid: {
                    "sig": [float(v) for v in e.sig],
                    "sig_rad": None if e.sig_rad is None
                               else [float(v) for v in e.sig_rad],
                    "sig_rr": None if e.sig_rr is None
                              else [float(v) for v in e.sig_rr],
                    "anchors": mask_to_cells(e.anchors),
                    "imprint": mask_to_cells(e.imprint),
                    "meta": e.meta,
                }
                for mid, e in self.entries.items()
            },
        }
        fd, tmp = tempfile.mkstemp(dir=self.path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=1)
            os.replace(tmp, self._store_file())
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def load(self):
        with open(self._store_file(), "r", encoding="utf-8") as f:
            payload = json.load(f)
        if payload.get("version") not in (1, STORE_VERSION):
            raise ValueError(f"unknown store version: {payload.get('version')}")
        if payload["grid"] != self.grid:
            raise ValueError(f"store grid {payload['grid']} != library grid {self.grid}")
        self._next_id = payload["next_id"]
        self.flat_sig = (None if payload["flat_sig"] is None
                         else np.array(payload["flat_sig"]))
        self.entries = {}
        for mid, rec in payload["entries"].items():
            sig_rad = rec.get("sig_rad")     # absent in v1 stores (legacy)
            sig_rr = rec.get("sig_rr")
            self.entries[mid] = Entry(
                mid=mid,
                sig=np.array(rec["sig"], dtype=float),
                sig_rad=None if sig_rad is None else np.array(sig_rad, dtype=float),
                sig_rr=None if sig_rr is None else np.array(sig_rr, dtype=float),
                anchors=cells_to_mask(rec["anchors"], self.grid),
                imprint=cells_to_mask(rec["imprint"], self.grid),
                meta=rec.get("meta", {}),
            )
