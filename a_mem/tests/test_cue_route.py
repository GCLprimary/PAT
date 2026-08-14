"""W-5 / R-2: the cue route on the shipped package (probe 16 Q1).

k = 12 bank, partial-anchor cues drawn from each pattern's own cells at
fractions 0.50 and 0.25. Probe 16 measured 100% / 100%; assert >= 95%.
"""
import numpy as np

from amem import Memory
from conftest import LINE_OFF, SEED_OFF, place


def test_cue_route_k12(tmp_path):
    mem = Memory(seed=5, path=str(tmp_path / "store"))
    bank = []
    for cx, cy in [(3, 3), (15, 14), (3, 14), (14, 3),
                   (9, 3), (3, 9), (14, 9), (9, 14)]:
        bank.append(place(SEED_OFF, cx, cy))
    for cx, cy in [(2, 2), (11, 16), (2, 16), (11, 2)]:
        bank.append(place(LINE_OFF, cx, cy))
    mids = [mem.write(p) for p in bank]

    for frac, floor in ((0.5, 0.95), (0.25, 0.95)):
        ok = tot = 0
        for i, (mid, cells) in enumerate(zip(mids, bank)):
            for s in range(3):
                rng = np.random.default_rng(100 + 10 * i + s)
                k = max(2, int(round(len(cells) * frac)))
                cue = [cells[j] for j in rng.choice(len(cells), size=k,
                                                    replace=False)]
                res = mem.recall(cue=cue)
                ok += int(res.identity == mid)
                tot += 1
        acc = ok / tot
        assert acc >= floor, f"cue fraction {frac}: accuracy {acc:.2f} < {floor}"
