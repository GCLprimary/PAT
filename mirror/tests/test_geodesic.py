"""G-5 sentinel (probe 28): real sentences trace lower-action paths
through the dense meaning space than their own shuffles (>= 75% of 300
sentences; measured 81-83%). The probe-28 structure must keep existing
under any meaning-geometry change.
"""
from collections import Counter

import numpy as np

from mirror.generate import load_default_prompt_corpus


def test_real_beats_own_shuffle(geometry):
    sents = [s for s in load_default_prompt_corpus() if len(s) >= 8]
    rng = np.random.default_rng(5)
    cnt = Counter()
    for s in sents:
        cnt.update(s)
    stop = set(w for w, _ in cnt.most_common(120))

    def action(words):
        vs = [geometry.vec(w) for w in words
              if w in geometry and w not in stop]
        if len(vs) < 4:
            return None
        steps = [np.linalg.norm(vs[i + 1] - vs[i])
                 for i in range(len(vs) - 1)]
        return float(np.mean(np.square(steps)))

    real, shuf = [], []
    for s in sents:
        if len(real) >= 300:
            break
        r = action(s)
        if r is None:
            continue
        sh = list(s)
        rng.shuffle(sh)
        r2 = action(sh)
        if r2 is None:
            continue
        real.append(r)
        shuf.append(r2)
    beats = float(np.mean(np.array(real) < np.array(shuf)))
    print(f"\naction: real {np.mean(real):.3f}  shuffled {np.mean(shuf):.3f}  "
          f"real-beats-shuffle {beats:.0%} (n={len(real)})")
    assert beats >= 0.75, f"geodesic structure eroded: {beats:.0%} < 75%"
