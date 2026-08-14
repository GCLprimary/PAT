"""W-5: relocation is duty of care (Phase 2 finding, probe 16 Q2).

A colliding write (overlap ~0.62) damages BOTH tenants — the incumbent's
recall margin drops too, not just the newcomer's. Relocated below the
danger line, both margins recover. Probe 16 measured: collided margins
+0.28 / +0.11; relocated +0.70 / +0.56.
"""
import numpy as np

from amem import Field, cosine
from amem import constants as K
from conftest import D, SEED_OFF, V, imprint, make_anchors, place


def build_identity(cx, cy):
    cells = place(SEED_OFF, cx, cy)
    _, orig = imprint(cells)
    return {"anchors": make_anchors(cells), "orig": orig}


def pair_margins(lib, seeds=(5, 6, 7)):
    """Probe-16 Q2: per seed, cue each tenant with half-anchors on a
    flattened stage, rebuild 4 beats, margin = own - other."""
    outs = []
    for sd in seeds:
        rng = np.random.default_rng(sd)
        ms = []
        for tgt in ("P1", "P2"):
            oth = "P2" if tgt == "P1" else "P1"
            e = Field(seed=sd, violence=V, decay=D)
            e.wipe()
            cells = np.argwhere(lib[tgt]["anchors"])
            sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2),
                                   replace=False)]
            e.deploy([(int(x), int(y)) for y, x in sel])
            for _ in range(4):
                e.beat(write_sig=False)
            ms.append(cosine(e.w, lib[tgt]["orig"]) -
                      cosine(e.w, lib[oth]["orig"]))
        outs.append(ms)
    return np.array(outs).mean(axis=0)


def test_relocation_duty_of_care():
    p1 = build_identity(5, 5)
    collide = {"P1": p1, "P2": build_identity(8, 8)}      # overlap ~0.62
    reloc = {"P1": p1, "P2": build_identity(13, 13)}      # overlap ~0.23

    ov_c = cosine(collide["P1"]["orig"], collide["P2"]["orig"])
    ov_r = cosine(reloc["P1"]["orig"], reloc["P2"]["orig"])
    assert ov_c >= K.OVERLAP_DANGER, f"collision pair overlap {ov_c:.2f} too low"
    assert ov_r < K.OVERLAP_DANGER, f"relocated pair overlap {ov_r:.2f} too high"

    m_collide = pair_margins(collide)
    m_reloc = pair_margins(reloc)

    # relocated: both tenants recall cleanly
    assert m_reloc[0] >= 0.45, f"relocated P1 margin {m_reloc[0]:+.2f} < +0.45"
    assert m_reloc[1] >= 0.45, f"relocated P2 margin {m_reloc[1]:+.2f} < +0.45"
    # collided: the INCUMBENT is damaged too — this is why relocation is
    # duty of care, not preference
    assert m_collide[0] <= 0.40, \
        f"incumbent margin {m_collide[0]:+.2f} under collision — undamaged?!"
    assert m_collide[1] < m_reloc[1], "collision cost the newcomer nothing?"
