"""a_mem demo: write three memories, recall one autonomously from a noisy
signature alone, then run a page-turned serial procession.

Runs from a fresh checkout:  python examples/demo_cli.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from amem import Field, Memory
from amem import constants as K

CONSTELLATION = K.SEED_CONSTELLATION
LINE = ((0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3))


def place(offsets, cx, cy):
    return [(cx + dx, cy + dy) for dx, dy in offsets]


def render(mask, label):
    print(f"  {label}")
    for y in range(K.GRID):
        print("    " + "".join("#" if mask[y, x] else "." for x in range(K.GRID)))


def main():
    t0 = time.time()
    store = tempfile.mkdtemp(prefix="a_mem_demo_")
    print(f"store: {store}\n")

    mem = Memory(seed=7, path=store)

    print("=" * 60)
    print("WRITE - three memories (anchor write + normalized imprint)")
    print("=" * 60)
    patterns = {
        "NW constellation": place(CONSTELLATION, 3, 3),
        "SE constellation": place(CONSTELLATION, 15, 14),
        "NE line": place(LINE, 12, 3),
    }
    mids = {}
    for name, cells in patterns.items():
        mid = mem.write(cells, meta={"label": name})
        entry = mem.library.get(mid)
        report = entry.meta["overlap_report"]
        mids[name] = mid
        print(f"  {mid}  {name:18s} anchors={int(entry.anchors.sum()):2d}  "
              f"imprint={int(entry.imprint.sum()):2d} cells  "
              f"max write-overlap={report['max_overlap']:.2f}"
              f"{'  << FLAGGED' if report['flagged'] else ''}")

    portrait = mem.calibrate()
    print(f"\n  calibration self-portrait (ring, dark center):")
    for row in np.round(portrait.reshape(3, 3), 2):
        print(f"    {row}")

    print()
    print("=" * 60)
    print("AUTONOMOUS RECALL - noisy signature -> classify -> complete")
    print("=" * 60)
    target = "SE constellation"
    # a different episode of the same pattern: same identity, new noise
    noisy = Field(seed=77, violence=K.VIOLENCE, decay=K.DECAY)
    noisy.stamp(patterns[target])
    for _ in range(K.IMPRINT_BEATS):
        noisy.beat()
    print(f"  cue: signature of a NOISY re-experience of '{target}'")
    rec = mem.recall(signature=noisy.sig)
    label = mem.library.get(rec.identity).meta["label"]
    ok = "correct" if rec.identity == mids[target] else "WRONG"
    print(f"  selected: {rec.identity} ({label}) - {ok}")
    print(f"  scores: " + "  ".join(f"{m}:{s:+.2f}" for m, s in rec.scores.items()))
    print(f"  confidence={rec.confidence:.2f}  dwell={rec.dwell} beats")
    render(mem.library.get(rec.identity).imprint, "stored imprint:")
    render(rec.reconstruction, "reconstruction (rebuilt from half-anchors):")

    print("=" * 60)
    print("SERIAL PROCESSION - page-turn every tenant change (law 2)")
    print("=" * 60)
    order = [mids["NW constellation"], mids["SE constellation"],
             mids["NE line"], mids["NW constellation"]]
    for res in mem.sequence(order, dwell=1):
        good = "ok " if res.identity == res.target else "BAD"
        print(f"  target {res.target} -> stage holds {res.identity}  [{good}]"
              f"  confidence={res.confidence:.2f}  dwell={res.dwell}")

    print()
    print("adaptive clock (theta=%.1f, cap=%d):" % (K.ADAPTIVE_THETA, K.ADAPTIVE_CAP))
    for res in mem.sequence(order[:3], dwell="adaptive"):
        good = "ok " if res.identity == res.target else "BAD"
        print(f"  target {res.target} -> {res.identity}  [{good}]  dwell={res.dwell}")

    print()
    print("=" * 60)
    print("PERSISTENCE - reload the library from disk")
    print("=" * 60)
    mem2 = Memory(seed=99, path=store)
    st = mem2.stats()
    print(f"  reloaded {st['library_size']} memories, calibrated={st['calibrated']}")
    rec2 = mem2.recall(signature=noisy.sig)
    print(f"  same noisy cue after reload -> {rec2.identity} "
          f"({'correct' if rec2.identity == mids[target] else 'WRONG'})")

    print(f"\ndone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
