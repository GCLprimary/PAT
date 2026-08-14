"""S-0: the sensor world v0 (builder-executed; grades forecasts S1/S2).

One synthetic alphabet — 12 discretized channels, a pattern is the
sequence of dominant-channel symbols over a dozen-odd timesteps — and
the SAME organs the language world runs on:

  EMBED   mirror.embed.BigramSpace over the 12-symbol alphabet
          (unigram + bigram counts, unit rows — the W-1 organ, new
          alphabet, zero new physics);
  A_MEM   patterns written as episodes (the cells_of adapter from the
          metabolism), recalled by noisy cue; recall is a RANKED
          PROPOSAL, never an identity claim (law 3 of Part X);
  GATE    cosine consonance at a threshold DERIVED FROM THIS WORLD —
          the sensor world is the noisy-input world the dormant cosine
          path was retained for (gate.py's docstring, Part VII); exact
          sequence equality cannot serve flipped channels, so the
          similarity floor of the tower is staffed here, with a
          re-swept theta;
  REFUSE  exhausted or under-threshold proposals refuse; a wrong
          identity above threshold is a confabulation and the battery
          demands ZERO.

S2 (no threshold transfers — the forecast's strongest claim): the
sensor theta is derived from a measured window ON SENSOR DATA — the
noisy-self consonance floor vs the cross-pattern imposter ceiling —
by `sweep_theta`, whose numbers are the provenance. The test asserts
the derivation is live (window open, theta strictly inside it) and
that the language constants (0.98 shape, 0.77 phon) were NOT imported.
"""
import numpy as np

from mirror.embed import BigramSpace

N_CHANNELS = 12
ALPHABET = tuple(f"c{i:02d}" for i in range(N_CHANNELS))
PATTERN_LEN = 12
N_KNOWN = 40
FLIPS = 2
PROPOSE_K = 12


def cells_of(vec, grid, k=24):
    idx = np.argsort(vec)[::-1][:k]
    return [(int(d) // grid, int(d) % grid) for d in idx]


class SensorWorld:
    def __init__(self, seed=17):
        self.rng = np.random.default_rng(seed)
        self.space = BigramSpace(ALPHABET)
        self.known = {}                 # name -> pattern tuple

    def new_pattern(self):
        return tuple(ALPHABET[i] for i in
                     self.rng.integers(0, N_CHANNELS, PATTERN_LEN))

    def populate(self, n=N_KNOWN):
        while len(self.known) < n:
            p = self.new_pattern()
            if p not in self.known.values():
                self.known[f"p{len(self.known):02d}"] = p
        return self.known

    def noisy(self, pattern, flips=FLIPS):
        p = list(pattern)
        idx = self.rng.choice(len(p), size=flips, replace=False)
        for i in idx:
            old = p[i]
            while p[i] == old:
                p[i] = ALPHABET[self.rng.integers(0, N_CHANNELS)]
        return tuple(p)

    def unknown_pattern(self):
        while True:
            p = self.new_pattern()
            if p not in self.known.values():
                return p

    def vec(self, pattern):
        return self.space.vec(pattern)


def sweep_theta(world, n_noisy=200, n_imposter=200):
    """S2's derivation: theta from the measured window ON SENSOR DATA.

    noisy-self consonance: cos(noisy(p), p) over known patterns;
    imposter consonance: cos(noisy(p), q) for q != p (the strongest
    wrong claim a noisy cue can make). theta = the midpoint of
    (imposter ceiling, self p5). Returns (theta, ceiling, self_p5) —
    the provenance the docstring promises."""
    names = list(world.known)
    self_cos, imp_cos = [], []
    vecs = {n: world.vec(p) for n, p in world.known.items()}
    for _ in range(n_noisy):
        n = names[world.rng.integers(len(names))]
        v = world.vec(world.noisy(world.known[n]))
        self_cos.append(float(v @ vecs[n]))
    for _ in range(n_imposter):
        n = names[world.rng.integers(len(names))]
        v = world.vec(world.noisy(world.known[n]))
        best_other = max(float(v @ vecs[m]) for m in names if m != n)
        imp_cos.append(best_other)
    ceiling = float(np.max(imp_cos))
    p5 = float(np.percentile(self_cos, 5))
    theta = round((ceiling + p5) / 2, 4)
    return theta, ceiling, p5


class SensorMemory:
    """The pipeline: a_mem proposes, the swept gate identifies."""

    def __init__(self, world, memory, theta):
        self.world = world
        self.memory = memory
        self.theta = theta
        self.grid = int(memory.grid)
        self.name_of = {}
        for name, pattern in world.known.items():
            mid = memory.write(
                cells_of(world.vec(pattern), self.grid),
                meta={"pattern": name})
            self.name_of[mid] = name

    def recognize(self, pattern):
        """-> (name | None). Ranked proposals from a_mem; the first to
        clear the SENSOR theta wins; exhaustion refuses."""
        v = self.world.vec(pattern)
        r = self.memory.recall(cue=cells_of(v, self.grid))
        if r is None or not r.scores:
            return None
        ranked = sorted(r.scores, key=r.scores.get, reverse=True)
        for mid in ranked[:PROPOSE_K]:
            name = self.name_of.get(mid)
            if name is None:
                continue
            if float(v @ self.world.vec(self.world.known[name])) \
                    >= self.theta:
                return name
        return None
