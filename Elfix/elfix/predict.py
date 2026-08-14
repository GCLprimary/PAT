"""
elfix/predict.py  —  counted, inspectable next-unit prediction (the generative floor)
=====================================================================================
The leap from ANALYZER to GENERATOR — readably. Every prediction is a corpus count
you can point at (Law 6: no gradient, no opaque optimiser). Given a context, predict
the next word with a distribution, a CONFIDENCE (entropy, bits), and its PROVENANCE
(lexical bigram vs PHONOLOGICAL backoff vs unigram). `generate` continues a seed;
temperature gates commitment (the readable ancestor of recognition-gated decoding,
Tier 7).

THE PHONOLOGICAL BACKOFF (this build — making the generator ElfIX-native)
-------------------------------------------------------------------------
v1's prediction was a LEXICAL bigram with a UNIGRAM backoff: when a context was
sparse it fell straight to global word frequency — sound-blind. The phonology lived
in the representation but not in the prediction. Now a middle tier generalises from
SOUND: when the bigram context is sparse, predict the next word from the pooled
continuation of the context word's PHONOLOGICAL CLASS — its earned arc-shape (the
Tier-3/6 router route, here keyed on the morphologically-loaded final arc). "What
tends to follow words that SOUND like this." The backoff chain is now

    lexical (bigram, dense)  ->  phono (sound-class pool)  ->  unigram (frequency).

This is class-based n-gram smoothing (Brown et al. 1992), but the classes are
EARNED PHONOLOGICAL shape-classes, not distributional Brown clusters — generalising
by sound, not by orthographic frequency.

MEASURED RESULT — an honest, informative NEGATIVE (scripts/predict_backoff.py).
On held-out sparse contexts the sound-class distribution does NOT beat the
sound-blind unigram (it is ~0.3-0.5 bits/word WORSE), in every regime (context
never seen, or seen <5x) and under both keys. The reason is the finding: a word's
final-arc SOUND-CLASS mixes syntactic categories (the same vowel+nasal coda ends a
participle '-ing', a preposition 'in', and a noun 'sun'), so its pooled continuation
collapses to the global marginal — the content->function-word transition the unigram
already captures. Next-word IDENTITY is governed by SYNTAX/SEMANTICS, which the
sound of the previous word does not encode. So the phono tier is OPT-IN and OFF by
default (`phono=None`): it is kept as the inspectable apparatus and the NEGATIVE
CONTROL that produced the measurement, not because it improves prediction.

WHERE THE SIGNAL ACTUALLY IS — CARRY-CONDITIONED PREDICTION (the positive).
The phono negative said the LAST WORD's sound is not enough. The next candidate was
ACCUMULATED context: the Tier-5 leaky integrator (decaying_carry) applied to WORD
IDENTITY — a decaying CACHE of what was recently said. Topic words recur, so a slow
memory of recent words should help. It does (scripts/carry_predict.py, held-out on a
contiguous tail): −0.98 bits/word (~49% perplexity), and a sentence-shuffle control
isolates +0.42 bits of GENUINE topical persistence (the rest is local-frequency
adaptation). `CarryCache` carries this online; `predict(prev, cache=...)` interpolates
the base distribution with the cache. The rate (~0.997) + mixing (~0.4) are EARNED on
a dev split, reported on test (Law 1) — the slow "second carry" carry_revalidate
flagged. So: where local SOUND failed, ACCUMULATED word-memory over TIME succeeds —
the predictive signal is topical, exactly where the locator pointed. NOTE: this is a
PREDICTION win (conditioning on REAL recent context). In FREE generation the cache
would feed on the model's own output and self-reinforce (cache-LM pathology), so
`generate(use_carry=...)` defaults OFF — carry is for continuing real text.

WHY READABLE GENERATION (the research bet, the author's reason for being off the
gradient): a gradient model generates but hides WHY. ElfIX generates with every step
inspectable, so we can ANALYSE its outputs — and crucially, see WHERE counted/
phonological context FAILS to predict (high entropy). Those failure points are where
MEANING must live: the generator localises the semantic signal instead of us
imposing a schema. The phono backoff makes this PRECISE from the negative side: by
showing the ~10 bits/word of next-word uncertainty after a sparse context is
IRREDUCIBLE BY SOUND, it proves that residual is the (not-yet-built) semantic layer's
job — measured, not assumed. The generator fails readably, exactly where it should.

PROVENANCE: [NEW->original] over ElfIX sound-units. Counted n-gram language model
(Shannon 1948; Brown et al. 1992); class-based backoff smoothing (Brown et al. 1992;
Katz 1987) over EARNED phonological classes (routing/shape_routing, Tier 3/6); the
decaying cache is a leaky integrator (Kuhn & de Mori 1990, cache LMs) = Tier-5 carry
over word identity; confidence-gated decoding [cleankit recognition].
"""
from __future__ import annotations
import math
import random
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Iterable, Optional, Callable
from .trajectory.trajectory import Trajectory

MIN_CONTEXT = 5            # bigram total below this -> back off (sparse -> generalise)
DEFAULT_PHONO_MODE = "final"   # final arc-class = the rhyme/suffix shape; see route_key.
                               # 'route' (whole-word shape) is 77% singletons on the
                               # corpus -> cannot pool -> degenerates to unigram (gate).

# EARNED on a DEV split, reported on TEST (scripts/carry_predict.py): the decaying
# word-cache timescale + mixing that maximise dev likelihood. rate ~0.997 is a slow
# topical memory (half-life ~230 words); beta ~0.4 is how far prediction leans on it.
EARNED_CARRY_RATE = 0.997
EARNED_CARRY_BETA = 0.4
EARNED_FACTORED_LAM = 0.3      # dev-earned floor<->factored interpolation (gradient_compartment)


def _entropy(cnt: Counter) -> float:
    tot = sum(cnt.values()) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in cnt.values() if v)


def _sample(ranked: List[Tuple[str, float, int]], temperature: float,
            rng: random.Random) -> str:
    """Sample a word from ranked (word, prob, count) reweighted by prob**(1/T).
    T < 1 sharpens (commit); T > 1 flattens (explore)."""
    t = max(0.05, temperature)
    weights = [(w, p ** (1.0 / t)) for w, p, _ in ranked]
    z = sum(x for _, x in weights) or 1.0
    r = rng.random() * z
    acc = 0.0
    for w, x in weights:
        acc += x
        if acc >= r:
            return w
    return weights[-1][0]


# ── Phonological class keys (the sound-class a word belongs to) ───────────────
def route_key(router, phonemes: Optional[List[str]], mode: str = DEFAULT_PHONO_MODE):
    """
    A word's PHONOLOGICAL CLASS key, read off its earned arc-shape route (Tier 3/6).
      mode 'final' : the FINAL arc's route class — the rhyme/suffix shape (the
                     morphologically-loaded ending; dense, ~300 classes on the
                     corpus). The default: shapes shared across many words, so the
                     pool generalises.
      mode 'route' : the whole-word route tuple — maximally specific, but 77%
                     singleton on the corpus, so it CANNOT pool (it degenerates to
                     the lexical/unigram path). Kept for the gate's honest contrast.
    Returns None when the word has no routable arc (then there is no sound-class and
    prediction falls through to the unigram).
    """
    if not phonemes:
        return None
    ids = router.route(Trajectory.of(phonemes))
    if not ids:
        return None
    return ids[-1] if mode == "final" else tuple(ids)


def make_key_of(router, pron: Dict[str, List[str]],
                mode: str = DEFAULT_PHONO_MODE) -> Callable[[str], object]:
    """Build a word -> phonological-class-key function from the router and a
    word->phonemes map. Words absent from `pron` (or unroutable) key to None."""
    def key_of(word: str):
        return route_key(router, pron.get(word), mode)
    key_of.mode = mode                                   # for readable reporting
    return key_of


class PhonoBackoff:
    """
    Sound-class smoothing for sparse contexts — the phonological backoff distribution.

    A word's PHONOLOGICAL CLASS is its earned arc-shape signature (router route,
    Tier 3/6). The backoff distribution for a context word `prev` is the POOLED
    continuation of every word in `prev`'s sound-class: "what tends to follow words
    that sound like `prev`." Counted and readable (Law 6); it generalises from SOUND,
    sitting above the sound-blind unigram it would otherwise fall to.

    Why pooling the continuations IS the class-transition model: the pooled
    distribution equals  P(next | class c) = Σ_c' P(next | next-class c') P(c' | c),
    the class-bigram marginalised over the next class — i.e. the very
    'P(next-class | class)' signal the router carries (learn_ops), folded into one
    counted distribution over words.

    PROVENANCE: [NEW->established] class-based n-gram smoothing (Brown et al. 1992),
    backoff (Katz 1987) — but the classes are EARNED PHONOLOGICAL shape-classes
    (routing/shape_routing, Tier 3/6), not distributional Brown clusters. The sound
    grounding is the novelty, and its predictive lift is the falsifiable claim.
    """

    def __init__(self, bigram: Dict[str, Counter], vocab: Iterable[str],
                 key_of: Callable[[str], object], min_mass: int = MIN_CONTEXT):
        self.mode = getattr(key_of, "mode", "custom")
        self.min_mass = min_mass
        self.word_class: Dict[str, object] = {}
        self.class_words: Dict[object, List[str]] = defaultdict(list)
        self.class_cont: Dict[object, Counter] = defaultdict(Counter)
        for w in vocab:
            c = key_of(w)
            if c is None:
                continue                       # no sound-class -> not pooled (-> unigram)
            self.word_class[w] = c
            self.class_words[c].append(w)
        # pool the bigram continuations of every word, by its sound-class
        for w, cnt in bigram.items():
            c = self.word_class.get(w)
            if c is not None:
                self.class_cont[c].update(cnt)

    def class_of(self, prev: str):
        """The phonological class key of `prev`, or None if it has no sound-class."""
        return self.word_class.get(prev)

    def continuation(self, prev: str) -> Optional[Counter]:
        """The pooled next-word counts of `prev`'s sound-class, or None when `prev`
        has no class or the pool is too thin to trust (< min_mass) — in which case
        prediction falls through to the unigram (absence != a confident zero)."""
        c = self.word_class.get(prev)
        if c is None:
            return None
        cont = self.class_cont.get(c)
        if not cont or sum(cont.values()) < self.min_mass:
            return None
        return cont


class CarryCache:
    """
    A decaying memory of recent words — the Tier-5 leaky integrator (decaying_carry)
    applied to WORD IDENTITY instead of feature points. Each `observe` decays every
    weight by `rate` and adds the new word; `prob` reads the recency-weighted
    distribution. This is a cache language model (Kuhn & de Mori 1990): topic words
    recur, so a slow memory of what was recently said carries genuine predictive
    signal (measured: scripts/carry_predict.py). Stateful and causal — feed it only
    the past. `reset()` at a hard discontinuity (e.g. a new document).

    >>> c = CarryCache(rate=0.5)
    >>> c.observe("a"); c.observe("b")
    >>> c.prob("b") > c.prob("a")      # the recent word dominates
    True
    >>> round(c.prob("a") + c.prob("b"), 9)
    1.0
    """

    def __init__(self, rate: float = EARNED_CARRY_RATE, prune: float = 1e-3):
        if not (0.0 <= rate < 1.0):
            raise ValueError("rate must be in [0, 1)")
        self.rate = rate
        self.prune = prune
        self.weights: Dict[str, float] = {}
        self.total: float = 0.0

    def observe(self, word: str) -> None:
        """Fold a word into the memory: decay all, drop the faded, add the new."""
        for k in list(self.weights):
            self.weights[k] *= self.rate
            if self.weights[k] < self.prune:
                del self.weights[k]
        self.weights[word] = self.weights.get(word, 0.0) + (1.0 - self.rate)
        self.total = sum(self.weights.values())

    def prob(self, word: str) -> float:
        """Recency-weighted probability of `word` (0 if not in the live memory)."""
        return self.weights.get(word, 0.0) / self.total if self.total > 0 else 0.0

    def reset(self) -> None:
        self.weights = {}
        self.total = 0.0


ACQUIRE_CONFIRM = 2          # external-input occurrences to confirm a transition
                             # (a transition seen >=2x is corroborated, not a nonce;
                             #  same justification as InferredStore's CONFIRM_AT).


class AcquiredContext:
    """
    Long-term distributional memory LEARNED FROM INPUT — the distributional sibling of
    `lexicon.InferredStore`, governed by the same laws so the model can train on input
    WITHOUT corrupting its ground truth (Law 2/3/5; the contamination trap the spec
    flags). It holds (prev -> next) transition evidence learned online, in a store
    SEPARATE from the attested base, distinguishing two sources:

      external input ('input'): real text -> can CONFIRM (>= ACQUIRE_CONFIRM) and is
                                 USED in prediction.
      self-generated ('self'):  the model's own output -> QUARANTINED. Recorded for
                                 audit, but NEVER used in prediction and NEVER able to
                                 confirm itself. This is the no-compounding guard: the
                                 model cannot bootstrap its own guesses into knowledge.

    The three InferredStore guarantees, mirrored for distributions:
      - never SHADOW attested  : the Predictor reads the attested base first; acquired
                                 only fills contexts the base is sparse/silent on.
      - never COMPOUND         : self-generated transitions are quarantined (above).
      - never COLLAPSE         : acquired counts stay separate; the effective model is a
                                 re-derivable VIEW (attested + acquired), never written
                                 back into the attested counts.

    Evidence is ternary (Law 5), absence distinct from zero (Law 2): a transition is
    'confirmed' (corroborated external), 'malleable' (seen once, or only self-
    generated), or 'absent' (never seen — not the same as malleable-at-low-count).
    """

    def __init__(self):
        self.ext: Dict[str, Counter] = defaultdict(Counter)   # external input transitions
        self.gen: Dict[str, Counter] = defaultdict(Counter)   # self-generated (quarantined)
        self.ext_unigram: Counter = Counter()                 # external word frequencies
        self.gen_unigram: Counter = Counter()                 # self-generated (quarantined)
        self.ext_uni_total = 0
        self.seen_ext = 0
        self.seen_gen = 0

    def ingest_utterance(self, ws: List[str], source: str = "input") -> None:
        """Fold one utterance's words + transitions into the store, by source."""
        if source == "self":                                  # quarantined branch
            for w in ws:
                self.gen_unigram[w] += 1
            for a, b in zip(ws, ws[1:]):
                self.gen[a][b] += 1
            self.seen_gen += max(0, len(ws) - 1)
        else:                                                 # external input (trains)
            for w in ws:
                self.ext_unigram[w] += 1
            self.ext_uni_total += len(ws)
            for a, b in zip(ws, ws[1:]):
                self.ext[a][b] += 1
            self.seen_ext += max(0, len(ws) - 1)

    def continuation(self, prev: str) -> Optional[Counter]:
        """The prediction distribution from EXTERNAL acquired evidence ONLY (self-
        generated is quarantined — the contamination guard). None if empty."""
        c = self.ext.get(prev)
        return c if c and sum(c.values()) else None

    def state(self, prev: str, nxt: str) -> str:
        """Ternary evidence for one transition: confirmed / malleable / absent."""
        if self.ext.get(prev, {}).get(nxt, 0) >= ACQUIRE_CONFIRM:
            return "confirmed"
        if self.ext.get(prev, {}).get(nxt, 0) > 0 or self.gen.get(prev, {}).get(nxt, 0) > 0:
            return "malleable"
        return "absent"


class FactoredBase:
    """The class-FACTORED base distribution (Brown et al. 1992's class LM, with ElfIX's
    EARNED distributional classes):

        P(w | prev)  =  P(class(w) | class(prev))  x  P(w | class(w), prev)
                          [scaffold class-bigram]     [within-class bigram share]

    Category by the syntactic scaffold's class-bigram; word by its share of the previous
    word's transitions RESTRICTED to its class, backed off (add-one, folded INSIDE the
    class-internal unigram share so the distribution is strictly positive and exactly
    normalized). Unclassed words are a real UNK class — never a free category (the leak
    that, unpaid, faked the win). MEASURED +0.81 bits/word over the word-bigram floor, a
    pure GENERALIZATION win (sparse contexts +1.78, dense -0.25 -> interpolate with the
    floor at the dev-earned lambda; scripts/gradient_compartment). Counted; no gradient
    (Law 6). Reads the ATTESTED bigram only (frozen); the floor it is interpolated with
    carries the acquired/adaptive signal, so the split is clean: factored generalizes,
    floor adapts.
    """

    def __init__(self, predictor: "Predictor", space, scaffold, a: float = 1.0):
        self.p, self.space, self.sc, self.a = predictor, space, scaffold, a
        self.uni_c_tot = {cid: (sum(predictor.unigram.get(m, 0) for m in mem) or 1)
                          for cid, mem in space.class_words.items()}
        self.unk = [w for w in predictor.unigram
                    if w not in space.word_class and w not in space.skeleton]
        self.unk_tot = sum(predictor.unigram.get(w, 0) for w in self.unk) or 1
        self._rowsum: Dict = {}

    def _members(self, w, c):
        if c[0] == "cl":
            return self.space.class_words.get(c[1], [w]), self.uni_c_tot.get(c[1], 1)
        if c[0] == "unk":
            return self.unk, self.unk_tot
        return [w], 1                                   # a functor: category == the word

    def _row_mass(self, prev, c, mem) -> float:
        """prev's attested bigram mass over the class members, cached per (prev, class)."""
        key = (prev, c)
        v = self._rowsum.get(key)
        if v is None:
            row = self.p.bigram.get(prev, {})
            v = sum(row.get(m, 0) for m in mem)
            self._rowsum[key] = v
        return v

    def p_within(self, prev: str, w: str) -> float:
        c = self.sc.sclass(w)
        mem, utot = self._members(w, c)
        if len(mem) == 1:
            return 1.0                                  # a singleton class: category IS the word
        row = self.p.bigram.get(prev, {})
        share = (self.p.unigram.get(w, 0) + 1) / (utot + len(mem))
        return (row.get(w, 0) + self.a * share) / (self._row_mass(prev, c, mem) + self.a)

    def prob(self, prev: str, w: str) -> float:
        """The factored P(w | prev) — a proper distribution over the vocabulary."""
        return self.sc.trans(prev, w) * self.p_within(prev, w)


class Predictor:
    """A counted next-word model over ElfIX's (sound-represented) words. Bigram with
    a PHONOLOGICAL backoff (sound-class pool) and a unigram floor; optionally
    conditioned on a CarryCache of recent words (accumulated context); and able to
    LEARN FROM INPUT into a governed AcquiredContext (the attested base stays frozen).
    Every prediction carries its evidence, confidence, and provenance level."""

    def __init__(self, utterances: Iterable[List[str]], vocab,
                 phono: Optional[PhonoBackoff] = None):
        self.bigram: Dict[str, Counter] = defaultdict(Counter)
        self.unigram: Counter = Counter()
        for utt in utterances:
            ws = [w for w in utt if w in vocab]
            self.unigram.update(ws)
            for a, b in zip(ws, ws[1:]):
                self.bigram[a][b] += 1
        self.phono = phono
        self.vocab = vocab                        # the predictable inventory (frozen)
        self._uni_total = sum(self.unigram.values())
        self.acquired = AcquiredContext()         # long-term memory learned from input
        self.factored: Optional[FactoredBase] = None   # opt-in class-factored base (attach_factored)
        self.factored_lam = EARNED_FACTORED_LAM

    def ingest(self, utterance: List[str], source: str = "input") -> int:
        """LEARN FROM INPUT: fold this utterance into the acquired store, SEPARATE from
        the frozen attested base (the contamination trap, Law 2/3/5). source='input' is
        external text — it ENTERS the predicting view; source='self' is the model's own
        generation — QUARANTINED (recorded for audit, never predicted from, never self-
        confirming). The attested counts are never written. Returns # in-vocab words."""
        ws = [w for w in utterance if w in self.vocab]
        self.acquired.ingest_utterance(ws, source)
        return len(ws)

    def _p_uni(self, nxt: str, alpha: float) -> float:
        """Add-alpha unigram prob over the ADAPTED view (attested + external-acquired
        word frequencies). The attested counts are always fully present (never lost);
        input only ADDS — so attested evidence is never shadowed, only supplemented."""
        a = self.acquired
        tot = self._uni_total + a.ext_uni_total
        V = len(self.unigram) or 1
        return (self.unigram.get(nxt, 0) + a.ext_unigram.get(nxt, 0) + alpha) \
            / (tot + alpha * V)

    def _eff_bigram(self, prev: str) -> Counter:
        """The effective transition counts for `prev`: attested + EXTERNAL acquired (a
        re-derivable VIEW — never written back; self-generated is excluded)."""
        att = self.bigram.get(prev)
        ext = self.acquired.ext.get(prev)
        if not ext:
            return att if att is not None else Counter()
        c = Counter(att) if att else Counter()
        c.update(ext)
        return c

    def _base_dist(self, prev: str) -> Tuple[Counter, str]:
        """The base next-word distribution + provenance, BEFORE the carry prior: the
        attested+acquired VIEW if it has context evidence (level 'lexical' when attested
        carries it, 'acquired' when input learning does), else the phono pool, else
        the unigram floor."""
        eff = self._eff_bigram(prev)
        if eff and sum(eff.values()) >= MIN_CONTEXT:
            att = self.bigram.get(prev)
            level = "lexical" if (att and sum(att.values()) >= MIN_CONTEXT) else "acquired"
            return eff, level
        if self.phono is not None and (pc := self.phono.continuation(prev)) is not None:
            return pc, "phono"
        return self.unigram, "backoff"

    def attach_phono(self, router, pron: Dict[str, List[str]],
                     mode: str = DEFAULT_PHONO_MODE,
                     min_mass: int = MIN_CONTEXT) -> PhonoBackoff:
        """Build + attach the phonological backoff (sound-class smoothing). After
        this, predict() inserts a 'phono' tier between lexical and unigram: a sparse
        context is predicted from the pooled continuation of its earned sound-class.
        `pron` maps word -> phonemes (e.g. the CMU dict); `router` is a ShapeRouter.

        OPT-IN by design: MEASURED not to beat the unigram for next-word prediction
        (scripts/predict_backoff.py), so the default Predictor leaves it off. Attach
        it to inspect the mechanism / the 'phono' provenance level, not to lower loss."""
        self.phono = PhonoBackoff(self.bigram, list(self.unigram),
                                  make_key_of(router, pron, mode), min_mass)
        return self.phono

    def attach_factored(self, space, scaffold, lam: float = EARNED_FACTORED_LAM) -> "FactoredBase":
        """Attach the class-FACTORED base distribution (Brown 1992 class LM, earned
        classes). After this, prob() and predict() interpolate the floor with the factored
        model at `lam` (floor) : 1-`lam` (factored) — the dev-earned mix that measured
        +0.81 bits/word over the word-bigram floor (scripts/gradient_compartment). OPT-IN:
        the default Predictor leaves it off, so bare behaviour and every existing gate are
        unchanged; attach it to DEPLOY the measured win (prediction, generation, and the
        locator's surprisals all shift, so they get re-gated)."""
        self.factored = FactoredBase(self, space, scaffold)
        self.factored_lam = lam
        return self.factored

    def _pbase(self, prev: str, w: str, dist: Counter, tot: int) -> float:
        """The base P(w|prev): the normalized bigram share, interpolated with the factored
        model when attached (floor generalizes via factored, adapts via the bigram)."""
        b = dist.get(w, 0) / tot
        if self.factored is None:
            return b
        return self.factored_lam * b + (1 - self.factored_lam) * self.factored.prob(prev, w)

    def predict(self, prev: str, k: int = 5, cache: Optional[CarryCache] = None,
                beta: float = EARNED_CARRY_BETA, sem_cache=None, sem_beta: float = 0.0,
                sem_adapt: Optional[Tuple[float, float]] = None):
        """Ranked next-word candidates (word, prob, count), the entropy of the base
        distribution in bits (CONFIDENCE of the context evidence), and the provenance
        level: 'lexical' (bigram), 'phono' (sound-class pool — sparse context
        generalised by sound), or 'backoff' (unigram frequency).

        The provenance level may be 'acquired' when the prediction is carried by what
        the model has LEARNED FROM INPUT (the attested base was sparse there).

        Two optional topical priors reweight the ranking (level gains a tag):
          `cache`     (CarryCache, weight `beta`)     — recency of exact WORDS ('+carry')
          `sem_cache` (SemanticCarry, weight `sem_beta`) — recency of CLASSES, the TOPIC
                      ('+topic'); it also SURFACES on-topic words as candidates that the
                      base/word-cache would miss (the measured +0.53-bit semantic win).
        Blend: P(next) = (1-beta-sem_beta) P_base + beta P_word + sem_beta P_topic. The
        reported entropy stays the BASE evidence's; count is the base raw count.

        `sem_adapt=(bc_max, h_ref)` makes the topic weight RISE with the base entropy H:
        sem_beta = bc_max * min(1, H/h_ref) — lean on topic at blind spots, ignore it
        when the bigram is confident. MEASURED to HURT perplexity (scripts/adaptive_topic:
        the true next word at a blind spot is usually a function word, not a topical one),
        so it is a GENERATION lever (push output toward content), NEVER used for scoring
        (`prob` does not call this)."""
        dist, level = self._base_dist(prev)
        tot = sum(dist.values()) or 1
        h = _entropy(dist)
        fac = "+factored" if self.factored is not None else ""
        if sem_adapt is not None and sem_cache is not None:
            bc_max, h_ref = sem_adapt
            sem_beta = bc_max * min(1.0, h / h_ref) if h_ref else bc_max
        use_w = cache is not None and cache.total > 0 and beta > 0
        use_s = sem_cache is not None and getattr(sem_cache, "total", 0) > 0 and sem_beta > 0
        if use_w or use_s:
            pool = set(w for w, _ in dist.most_common(max(k, 20)))
            if use_w:
                pool |= set(cache.weights)
            if use_s:
                pool |= set(sem_cache.top_members())     # surface on-topic candidates
            base_wt = max(0.0, 1.0 - (beta if use_w else 0.0) - (sem_beta if use_s else 0.0))
            def _mix(w):
                s = base_wt * self._pbase(prev, w, dist, tot)
                if use_w:
                    s += beta * cache.prob(w)
                if use_s:
                    s += sem_beta * sem_cache.prob(w)
                return s
            blended = sorted(((w, _mix(w)) for w in pool), key=lambda x: -x[1])[:k]
            tag = level + ("+carry" if use_w else "") + ("+topic" if use_s else "") + fac
            return [(w, p, dist.get(w, 0)) for w, p in blended], h, tag
        if self.factored is not None:                    # rescore the bigram pool by the factored base
            pool = [w for w, _ in dist.most_common(max(k, 50))]
            ranked = sorted(((w, self._pbase(prev, w, dist, tot), dist.get(w, 0))
                             for w in pool), key=lambda x: -x[1])[:k]
            return ranked, h, level + fac
        ranked = [(w, c / tot, c) for w, c in dist.most_common(k)]
        return ranked, h, level

    def prob(self, prev: str, nxt: str, alpha: float = 0.1,
             k_backoff: float = 5.0) -> float:
        """Smoothed P(nxt | prev) under the CURRENT model (attested + acquired VIEW;
        carry excluded) — for held-out scoring of learning-from-input. A bigram count
        (attested + external-acquired) backed off to the adapted unigram by a Dirichlet
        pseudo-count `k_backoff`: a thin context leans on the (robust) unigram, a rich
        one on the bigram — so low-count acquired evidence can only help, not mislead.
        Shares `_base_dist`/`_eff_bigram` with predict(), so scoring and ranking agree.
        When the FACTORED base is attached, the result is the dev-earned interpolation
        lam*floor + (1-lam)*factored (the deployed +0.81-bit win)."""
        p_uni = self._p_uni(nxt, alpha)
        dist, level = self._base_dist(prev)
        if level == "backoff":                    # no context evidence -> unigram
            base = p_uni
        else:
            bt = sum(dist.values())
            base = (dist.get(nxt, 0) + k_backoff * p_uni) / (bt + k_backoff)
        if self.factored is not None:
            return self.factored_lam * base + (1 - self.factored_lam) * self.factored.prob(prev, nxt)
        return base

    def transition_evidence(self, prev: str, nxt: str) -> str:
        """Provenance of a (prev -> next) transition (Law 5): 'attested' (in the frozen
        base), 'acquired:confirmed' / 'acquired:malleable' (learned from input), or
        'absent'. Self-generated transitions never reach confirmed (the guard)."""
        if self.bigram.get(prev, Counter()).get(nxt, 0) > 0:
            return "attested"
        s = self.acquired.state(prev, nxt)
        return "absent" if s == "absent" else "acquired:" + s

    def generate(self, seed: str, n: int = 12, temperature: float = 0.6,
                 rng_seed: int = 0, use_carry: bool = False,
                 carry_rate: float = EARNED_CARRY_RATE,
                 beta: float = EARNED_CARRY_BETA) -> List[Tuple[str, float, str]]:
        """Continue from `seed` for n steps. Returns (word, step_entropy, level) per
        step — the whole trajectory is inspectable: at each word you see how uncertain
        the context evidence was and whether it spoke from lexical context, the
        phonological backoff, or unigram frequency.

        `use_carry` is OFF by default here ON PURPOSE. The cache's measured win
        (carry_predict.py) is for PREDICTION over REAL context — `predict(prev,
        cache=...)` fed the true past. In FREE generation the cache would accumulate the
        model's OWN output and self-reinforce (the classic cache-LM pathology: 'the the
        the ...'), so it is opt-in here for inspection only. Use carry to PREDICT/
        continue real text, not to free-run."""
        rng = random.Random(rng_seed)
        cache = CarryCache(carry_rate) if use_carry else None
        out = [(seed, 0.0, "seed")]
        cur = seed
        if cache is not None:
            cache.observe(seed)
        for _ in range(n):
            ranked, h, level = self.predict(cur, k=20, cache=cache, beta=beta)
            if not ranked:
                break
            cur = _sample(ranked, temperature, rng)
            out.append((cur, h, level))
            if cache is not None:
                cache.observe(cur)
        return out

    def context_uncertainty(self, min_count: int = 50):
        """The semantic locator: for every sufficiently-attested context word, the
        entropy of what follows it. LOW-entropy contexts are structure the counts
        already capture (collocations); HIGH-entropy contexts are where local/sound
        context cannot decide the next word — where MEANING must attach. Returns
        [(prev, entropy, total)] sorted by entropy."""
        out = []
        for prev, cnt in self.bigram.items():
            tot = sum(cnt.values())
            if tot >= min_count:
                out.append((prev, _entropy(cnt), tot))
        out.sort(key=lambda x: x[1])
        return out

    def locator(self, max_lexical: int = MIN_CONTEXT):
        """
        The semantic locator as a NEGATIVE CONTROL (needs an attached phono backoff).
        For each sparse context (lexical mass < max_lexical), report the entropy of
        the UNIGRAM (what frequency alone knows) and of the pooled SOUND-CLASS (what
        generalising by sound adds). The measured finding (scripts/predict_backoff):
        the sound-class entropy does NOT fall below the unigram — pooling by sound
        does not sharpen the next-word distribution. So the residual uncertainty is
        not phonological; it is the semantic layer's, localised here by sound's
        failure to reduce it. Returns [(prev, n_lexical, h_unigram, h_phono)] sorted
        by h_phono descending (most semantically open first); h_phono is None when
        the context has no usable sound-class.
        """
        if self.phono is None:
            raise ValueError("locator needs a phono backoff; call attach_phono first")
        h_uni = _entropy(self.unigram)
        out = []
        for prev in self.phono.word_class:
            n = sum(self.bigram[prev].values()) if prev in self.bigram else 0
            if n >= max_lexical:
                continue
            pc = self.phono.continuation(prev)
            out.append((prev, n, h_uni, _entropy(pc) if pc is not None else None))
        out.sort(key=lambda x: (x[3] is not None, x[3] if x[3] is not None else 0.0),
                 reverse=True)
        return out


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    from elfix.running_text import load_utterances
    from elfix.routing.shape_routing import ShapeRouter

    cmu = load_cmu()
    vocab = set(cmu.keys())
    p = Predictor(load_utterances(), vocab)        # the working model: lexical -> unigram
    print(f"bigram contexts: {len(p.bigram):,}   vocab seen: {len(p.unigram):,}\n")

    print("=== inspectable free generation (each step: word [entropy bits, source]) ===")
    for seed, temp in (("the", 0.6), ("united", 0.4), ("president", 0.6)):
        traj = p.generate(seed, n=10, temperature=temp)   # carry OFF for free-running
        line = " ".join(w for w, _, _ in traj)
        print(f"\n  seed '{seed}' (T={temp}):  {line}")
        print("    step detail: " + "  ".join(
            f"{w}[{h:.1f},{lv[:3]}]" for w, h, lv in traj[1:5]))

    print("\n=== carry-conditioned PREDICTION over real context (the measured win) ===")
    print("    the cache = recent words; it reweights prediction toward the live topic")
    ctx = ["new", "york", "city", "york", "york"]      # a topical run of real words
    cache = CarryCache()
    for w in ctx:
        if w in p.unigram:
            cache.observe(w)
    plain = [w for w, _, _ in p.predict("the", k=6)[0]]
    condd = [w for w, _, _ in p.predict("the", k=6, cache=cache)[0]]
    print(f"    after 'the'  (no carry):              {', '.join(plain)}")
    print(f"    after 'the'  (carry, topic={ctx[:3]}+):  {', '.join(condd)}")
    print("    -> the topical words the model just heard are pulled into the "
          "prediction\n       (rigorously: +0.42 bits topical on held-out text, "
          "scripts/carry_predict.py).")

    # ── the phonological backoff: BUILT and MEASURED (an honest negative) ─────────
    router = ShapeRouter([Trajectory.of(ph) for ph in cmu.values()])
    p.attach_phono(router, cmu)            # opt-in; off by default (measured no-lift)
    print(f"\n=== the phonological backoff (opt-in): {len(p.phono.class_words):,} "
          f"sound-classes, mode '{p.phono.mode}' ===")
    print("  MEASURED not to beat the unigram for next-word prediction "
          "(scripts/predict_backoff).")
    print("  The mechanism, shown on a sparse context (its sound-class pool):")
    for prev in p.phono.word_class:
        n = sum(p.bigram[prev].values()) if prev in p.bigram else 0
        if 1 <= n < MIN_CONTEXT and p.phono.continuation(prev) is not None:
            ranked, h, level = p.predict(prev, k=4)
            mates = [w for w in p.phono.class_words[p.phono.class_of(prev)]
                     if w != prev][:5]
            print(f"    '{prev}' (only {n} lexical) -> {level} (H={h:.2f}): "
                  + ", ".join(f"{w} {pr:.0%}" for w, pr, _ in ranked))
            print(f"        sound-class mates (mixed categories): {', '.join(mates)}")
            break

    print("\n=== the semantic locator (negative control): sound can't lower it ===")
    loc = [r for r in p.locator() if r[3] is not None]
    h_uni = loc[0][2] if loc else 0.0
    print(f"  unigram entropy (sound-blind floor): {h_uni:.2f} bits")
    print("  sparse contexts where even the SOUND-CLASS stays wide -> MEANING decides:")
    for prev, n, _, hp in loc[:5]:
        print(f"    '{prev}' (n={n}): sound-class H={hp:.2f} bits  (>= unigram floor)")
