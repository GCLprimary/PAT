"""W-5: the serial-position law (Phase 2 finding, probe 16 Q3).

Sequential writes onto a SHARED field produce primacy + recency: newest
and oldest survive, the middle sinks (measured over 6 seeds: newest 0.69,
oldest 0.43, middle 0.21, std <= 0.04). The clarifying half: the same
episodes written per-episode through the encoder show no age gradient —
the U-curve is a shared-region phenomenon, and the page-per-episode
architecture neutralizes it.
"""
import numpy as np

from amem import EpisodeHooks, Field, Memory
from amem import constants as K
from conftest import D, SEED_OFF, V, imprint, place

POSITIONS = [(3, 3), (15, 14), (3, 14), (14, 3), (9, 9)]
SEEDS = (5, 9, 13, 21, 33, 47)


def test_shared_field_u_curve():
    origs = [imprint(place(SEED_OFF, cx, cy))[1] for cx, cy in POSITIONS]
    surv = np.zeros((len(SEEDS), 5))
    for si, sd in enumerate(SEEDS):
        e = Field(seed=sd, violence=V, decay=D)
        for cx, cy in POSITIONS:
            e.stamp(place(SEED_OFF, cx, cy))
            for _ in range(4):
                e.beat(write_sig=False)
        for age, orig in enumerate(reversed(origs)):   # age 0 = newest
            surv[si, age] = float((e.w > K.TRAP_T)[orig > 0].mean())
    u = surv.mean(axis=0)
    newest, oldest, middle = u[0], u[4], float(u[1:4].mean())

    # the U-shape itself
    assert newest > middle, f"no recency: newest {newest:.2f} <= middle {middle:.2f}"
    assert oldest > middle, f"no primacy: oldest {oldest:.2f} <= middle {middle:.2f}"
    # probe-16 bands (+-0.1)
    assert abs(newest - 0.69) <= 0.1, f"newest {newest:.2f} outside 0.69+-0.1"
    assert abs(oldest - 0.43) <= 0.1, f"oldest {oldest:.2f} outside 0.43+-0.1"
    assert abs(middle - 0.21) <= 0.1, f"middle {middle:.2f} outside 0.21+-0.1"


def test_separation_neutralizes_u_curve():
    """Clarifying half: five episodes written per-episode via the W-2
    encoder show middle-age recall completion within 0.15 of newest.
    (Spec: if this half fails, that is a finding — flag, don't force.)"""
    per_age = []
    for s in range(4):
        mem = Memory(seed=s, path=None)
        hooks = EpisodeHooks(mem)
        rng = np.random.default_rng(50 + s)
        embs = [rng.normal(size=32) for _ in range(5)]
        mids = [hooks.write_episode(e) for e in embs]
        completions = []
        for mid in mids:                       # write order: 0 oldest
            rec = mem.recall(mid=mid)
            imp = mem.library.get(mid).imprint
            completions.append(float(rec.reconstruction[imp].mean()))
        per_age.append(completions)
    per_age = np.array(per_age).mean(axis=0)   # index 0 oldest .. 4 newest
    newest = per_age[4]
    middle = float(per_age[1:4].mean())
    assert middle >= newest - 0.15, \
        (f"middle completion {middle:.2f} more than 0.15 below newest "
         f"{newest:.2f} — separation did NOT neutralize the U-curve (finding!)")
