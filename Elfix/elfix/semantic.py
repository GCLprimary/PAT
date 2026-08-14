"""
elfix/semantic.py  —  the semantic layer: COUNTED distributional meaning
========================================================================
The layer the whole generative arc pointed at. The locator keeps marking high-
entropy contexts — where counted/sound context cannot decide the next word, so
MEANING must carry it. This is where meaning attaches, and it is EARNED, not
gradient-learned (Law 6): a word's meaning is the company it keeps (Firth 1957;
the distributional hypothesis — Harris 1954), counted directly from the corpus.

THE SYMMETRY THAT CLOSES THE ARC
--------------------------------
The phono backoff was class-based smoothing (Brown et al. 1992) with SOUND classes
— it FAILED, because sound shape is not a syntactic/semantic category (a vowel+nasal
coda ends '-ing', 'in' and 'sun' alike). This is the SAME machinery with
DISTRIBUTIONAL classes — words that keep the same company. Those ARE the syntactic/
semantic categories, so pooling continuations by them should succeed exactly where
sound failed. Same pooling (PhonoBackoff), different class source: that contrast is
the experiment (scripts/semantic_gate.py).

HOW A CLASS IS EARNED (self-forming, readable — Law 6/1)
-------------------------------------------------------
0. ANCHORS define the context axes (top-N frequent words). The function-word SKELETON
   (the most frequent of them) gets NO class of its own — it is syntax, not topic; a
   class that held function words would fire on every sentence (the 'sticky class').
   So anchors = axes, CONTENT words = classes.
1. The class members are the CONTENT words (signed, non-skeleton).
2. SIGNATURE: for each word, the PPMI (positive pointwise mutual information) of its
   co-occurrence with each anchor in a window — its readable distributional profile,
   capped to its top associations (denoised). PPMI surfaces DISTINCTIVE company over
   raw frequency (Church & Hanks 1990); cosine of PPMI vectors ~ word2vec similarity
   (Levy & Goldberg 2014) but COUNTED, not gradient-learned.
3. CLASS: words are clustered by cosine of their distributional vectors (sparse
   k-means on the frequent words; every word then joins its nearest class). This is
   geometric clustering of COUNTED vectors — the same family as Tier 3 (Kohonen /
   agglomerative), NOT a gradient black box (Law 6). A class is readable (its centroid's
   top anchors + its members) and carries centre + width (Law 4).
4. ABSENCE != zero (Law 2): a word with too little co-occurrence has NO reliable
   signature -> no class (None), not a forced one.

NOTE on the earlier descriptor attempt: exact top-k-anchor matching made ~20k
singleton classes (every word unique) — too sparse to pool, the same failure as the
phono 'route' key. Continuous distributional vectors need real clustering, not
exact-descriptor hashing.

NOTE on K (the class count): we tried to EARN it from the within-cluster-distance
elbow (scripts/semantic_k), but the distortion falls ~linearly with K — there is NO
clean knee, because word distribution is a CONTINUUM. So K is honestly a RESOLUTION
DIAL, not a discovered constant (Law 1 flag, not a pretended-earned elbow): finer K ->
sharper, more interpretable topics; coarser K -> more predictive generalisation. k=300
is the operating point (topic usability + the held-out +0.39-bit carry gate); tunable.

PROVENANCE: [NEW->established] distributional semantics — Harris (1954), Firth
(1957); PPMI — Church & Hanks (1990); PPMI~embeddings — Levy & Goldberg (2014);
class-based LM — Brown et al. (1992). The parallel to the phono backoff (same pooling,
classes from MEANING not SOUND) is [NEW->original].
"""
from __future__ import annotations
import math
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Iterable


def build_anchors(unigram: Counter, n_anchors: int) -> List[str]:
    """The syntactic skeleton: the top-N most frequent words (earned, not picked)."""
    return [w for w, _ in unigram.most_common(n_anchors)]


def _cooccurrence(utterances: Iterable[List[str]], vocab, anchors: set, window: int):
    """Co-occurrence of each word with each ANCHOR inside +/-window. Returns
    cooc[word] -> Counter(anchor), anchor marginal, word marginal, total N."""
    cooc: Dict[str, Counter] = defaultdict(Counter)
    amarg: Counter = Counter()
    wmarg: Counter = Counter()
    n = 0
    for utt in utterances:
        ws = [w for w in utt if w in vocab]
        for i, w in enumerate(ws):
            lo, hi = max(0, i - window), min(len(ws), i + window + 1)
            for j in range(lo, hi):
                if j == i:
                    continue
                a = ws[j]
                if a in anchors:
                    cooc[w][a] += 1
                    amarg[a] += 1
                    wmarg[w] += 1
                    n += 1
    return cooc, amarg, wmarg, n


def _ppmi_signature(cw: Counter, wtot: int, amarg: Counter, n: int,
                    cap: int) -> Dict[str, float]:
    """L2-normalized PPMI of one word with its anchors, capped to its top `cap`
    associations (denoise). PPMI = max(0, log2 P(w,a)/(P(w)P(a)))."""
    sig = {}
    for a, c in cw.items():
        if c and amarg[a]:
            pmi = math.log2((c * n) / (wtot * amarg[a]))
            if pmi > 0:
                sig[a] = pmi
    if len(sig) > cap:
        sig = dict(sorted(sig.items(), key=lambda kv: -kv[1])[:cap])
    norm = math.sqrt(sum(v * v for v in sig.values())) or 1.0
    return {a: v / norm for a, v in sig.items()}


def _dot(v: Dict[str, float], c: Dict[str, float]) -> float:
    return sum(val * c.get(a, 0.0) for a, val in v.items())


def _kmeans(words: List[str], vecs: Dict[str, Dict[str, float]],
            k: int, iters: int, seed: int):
    """Sparse-cosine k-means over normalized PPMI vectors. Deterministic given seed.
    Returns (centroids, assignment word->cluster-id). No gradients — geometric."""
    import random as _random
    rng = _random.Random(seed)
    centroids = [dict(vecs[w]) for w in rng.sample(words, min(k, len(words)))]
    assign: Dict[str, int] = {}
    for _ in range(iters):
        members: List[List[str]] = [[] for _ in centroids]
        for w in words:
            v = vecs[w]
            best_j, best = 0, -2.0
            for j, c in enumerate(centroids):
                s = _dot(v, c)
                if s > best:
                    best, best_j = s, j
            assign[w] = best_j
            members[best_j].append(w)
        for j, mem in enumerate(members):
            if not mem:
                continue                          # keep an empty cluster's old centroid
            acc: Dict[str, float] = defaultdict(float)
            for w in mem:
                for a, val in vecs[w].items():
                    acc[a] += val
            nrm = math.sqrt(sum(x * x for x in acc.values())) or 1.0
            centroids[j] = {a: x / nrm for a, x in acc.items()}
    return centroids, assign


class SemanticSpace:
    """Earned distributional word classes: a word's meaning is its counted company.

    Words with enough evidence get a PPMI SIGNATURE over frequency anchors and a CLASS
    (a cosine cluster of those signatures). Classes are readable (centroid anchors +
    members) and carry centre + width (Law 4). All counted; no gradients (Law 6).
    """

    def __init__(self, utterances, vocab, n_anchors: int = 600, window: int = 2,
                 min_count: int = 5, sig_cap: int = 40, n_cluster_words: int = 2500,
                 k: int = 300, iters: int = 10, seed: int = 0, n_skeleton: int = 80,
                 unigram: Optional[Counter] = None):
        # k is a RESOLUTION DIAL, not an earned constant: the distortion-vs-K curve has
        # no clean elbow (scripts/semantic_k) — word distribution is a continuum. 300
        # balances topic sharpness vs the carry-gate lift; tunable (Law 1 flag).
        utterances = list(utterances)
        if unigram is None:
            unigram = Counter(w for utt in utterances for w in utt if w in vocab)
        self.params = dict(n_anchors=n_anchors, window=window, k=k, sig_cap=sig_cap,
                           n_cluster_words=n_cluster_words, n_skeleton=n_skeleton)
        self.anchors = build_anchors(unigram, n_anchors)
        self.anchor_set = set(self.anchors)
        # the function-word SKELETON (most frequent) defines the context axes but gets
        # NO semantic class itself — it is syntax, not topic. Excluding it stops a class
        # filling with function words and firing on every sentence (the 'sticky class').
        self.skeleton = set(self.anchors[:n_skeleton])
        cooc, amarg, wmarg, n = _cooccurrence(utterances, vocab, set(self.anchors), window)
        self.amarg, self.n, self.sig_cap = amarg, n, sig_cap   # kept for online placement
        # PPMI signatures for every word with enough co-occurrence (else absent, Law 2)
        self.signatures: Dict[str, Dict[str, float]] = {}
        for w, cw in cooc.items():
            if wmarg[w] >= min_count:
                sig = _ppmi_signature(cw, wmarg[w], amarg, n, sig_cap)
                if sig:
                    self.signatures[w] = sig
        # cluster the FREQUENT CONTENT words; then every content word joins its nearest
        signed = [w for w in self.signatures if w not in self.skeleton]
        clust_words = sorted(signed, key=lambda w: -unigram[w])[:n_cluster_words]
        self.centroids, _ = _kmeans(clust_words, self.signatures, k, iters, seed)
        self.word_class: Dict[str, int] = {}
        self.class_words: Dict[int, List[str]] = defaultdict(list)
        for w in signed:
            v = self.signatures[w]
            cid = max(range(len(self.centroids)), key=lambda j: _dot(v, self.centroids[j]))
            self.word_class[w] = cid
            self.class_words[cid].append(w)

    def class_of(self, word: str) -> Optional[int]:
        """The distributional class id of `word`, or None if it has no reliable
        signature (too little evidence — absent, not a forced zero, Law 2)."""
        return self.word_class.get(word)

    def signature(self, cooc: Counter, total: int) -> Dict[str, float]:
        """The PPMI signature of an arbitrary word's accumulated anchor co-occurrence
        — the same recipe as the built ones, for placing a word seen at run time."""
        return _ppmi_signature(cooc, total, self.amarg, self.n, self.sig_cap)

    def nearest(self, sig: Dict[str, float]) -> Optional[int]:
        """The class whose centroid this signature is closest to (cosine)."""
        if not sig:
            return None
        return max(range(len(self.centroids)), key=lambda j: _dot(sig, self.centroids[j]))

    def place(self, cooc: Counter, total: int) -> Tuple[Optional[int], Dict[str, float]]:
        """Place a word in its nearest class from its ACCUMULATED anchor co-occurrence
        — DISTRIBUTIONAL placement, the validated method. Used to REFINE an OOV word's
        weak morphological cold-start once it has read enough context. Returns
        (class_id|None, signature)."""
        sig = self.signature(cooc, total)
        return self.nearest(sig), sig

    def width(self, cid: int) -> float:
        """Mean cosine distance of a class's members to its centroid (Law 4)."""
        mem = self.class_words.get(cid, [])
        c = self.centroids[cid]
        return sum(1.0 - _dot(self.signatures[w], c) for w in mem) / len(mem) if mem else 0.0

    def class_anchors(self, cid: int, k: int = 4) -> List[str]:
        """The centroid's top anchors — the readable 'company' that names the class."""
        return [a for a, _ in sorted(self.centroids[cid].items(),
                                     key=lambda kv: -kv[1])[:k]]

    def describe_class(self, cid) -> str:
        """Readable class card: its anchor-frame, members, size and width (Law 6/4)."""
        if cid is None or cid not in self.class_words:
            return "absent"
        mem = self.class_words[cid]
        ex = ", ".join(mem[:6])
        return (f"~{{{', '.join(self.class_anchors(cid))}}} ({len(mem)} words, "
                f"width {self.width(cid):.2f}): {ex}{' ...' if len(mem) > 6 else ''}")


class SyntaxScaffold:
    """
    The grammatical skeleton: a class-BIGRAM over a SYNTACTIC classing — each function
    word (the skeleton) is its OWN class (the/of/to are distinct syntactic roles), and
    content words keep their distributional class. Measured to carry ~0.57 bits of
    structure (scripts/syntax_scaffold): prev's class predicts the NEXT class strongly
    ('of'->determiner, 'to'->verb, noun->preposition) even though it is NULL for the next
    word's IDENTITY. This is the 'what KIND of word follows what' that the word-bigram
    lacks — used to bias generation toward grammar. Counted; no gradients (Law 6).
    """

    def __init__(self, space: SemanticSpace, utterances, vocab, alpha: float = 0.5):
        self.space = space
        self.skel = space.skeleton
        self.alpha = alpha
        self.bg: Dict[object, Counter] = defaultdict(Counter)
        self.uni: Counter = Counter()
        # SENTENCE-arc structure (same pass): where each class sits in a sentence (the
        # measured subject->predicate arc) and where sentences END (the boundary signal).
        pos_sum: Dict[object, float] = defaultdict(float)
        pos_n: Counter = Counter()
        end_n: Counter = Counter()
        lens: Counter = Counter()
        for utt in utterances:
            cs = [self.sclass(w) for w in utt if w in vocab]
            self.uni.update(cs)
            for x, y in zip(cs, cs[1:]):
                self.bg[x][y] += 1
            L = len(cs)
            if L:
                lens[L] += 1
                for i, c in enumerate(cs):
                    pos_sum[c] += (i / (L - 1)) if L > 1 else 0.5
                    pos_n[c] += 1
                    end_n[c] += (i == L - 1)
        self.tot = {c: sum(r.values()) for c, r in self.bg.items()}
        self.NC = sum(self.uni.values())
        self.NCL = len(self.uni)
        self.meanpos = {c: pos_sum[c] / pos_n[c] for c in pos_n}      # class -> mean position
        self.endrate = {c: end_n[c] / self.uni[c] for c in pos_n}     # class -> P(ends a sentence)
        self._mean_end = (sum(end_n.values()) / (sum(pos_n.values()) or 1)) or 0.1
        self.mean_len = sum(L * k for L, k in lens.items()) / (sum(lens.values()) or 1)

    def pos_fit(self, word: str, frac: float, sigma: float = 0.3) -> float:
        """How position-appropriate `word`'s class is at sentence-fraction `frac` (0=start,
        1=end): 1.0 at its mean position, falling off by `sigma`. The subject->predicate
        arc — subjects early, objects late — as a generation bias."""
        mp = self.meanpos.get(self.sclass(word))
        return 1.0 if mp is None else math.exp(-((mp - frac) ** 2) / (2 * sigma * sigma))

    def end_prob(self, prev_word: str, length: int) -> float:
        """Probability a sentence ENDS after `prev_word` at this `length`: a length hazard
        rising around the mean sentence length, boosted when prev's class is a typical
        sentence-ender ('him', 'said', 'them')."""
        base = 1.0 / (1.0 + math.exp(-(length - self.mean_len) / 3.0))
        mod = self.endrate.get(self.sclass(prev_word), self._mean_end) / (self._mean_end or 1)
        return min(0.95, base * mod)

    def sclass(self, w: str):
        """A word's SYNTACTIC class: ('fn', w) for a function word, ('cl', id) for a
        content word, ('unk',) if unclassed."""
        if w in self.skel:
            return ("fn", w)
        cid = self.space.class_of(w)
        return ("cl", cid) if cid is not None else ("unk",)

    def _puni(self, c):
        return (self.uni.get(c, 0) + self.alpha) / (self.NC + self.alpha * self.NCL)

    def trans(self, prev_word: str, next_word: str) -> float:
        """P(class(next) | class(prev)) — the grammatical likelihood of the transition
        (Dirichlet-backed to the class unigram)."""
        c, cn = self.sclass(prev_word), self.sclass(next_word)
        tot = self.tot.get(c, 0)
        pu = self._puni(cn)
        if tot == 0:
            return pu
        return (self.bg[c].get(cn, 0) + self.alpha * pu) / (tot + self.alpha)

    def seq_bits(self, words: List[str]) -> float:
        """Mean -log2 P(class | prev-class) of a word sequence — its grammatical-
        transition cost (lower = the class-sequence is more like real English)."""
        if len(words) < 2:
            return 0.0
        return sum(-math.log2(self.trans(a, b))
                   for a, b in zip(words, words[1:])) / (len(words) - 1)


def make_semantic_key_of(space: SemanticSpace):
    """Word -> distributional-class key, for the pooling machinery (PhonoBackoff).
    The semantic counterpart of make_key_of: same pooling, classes from MEANING.
    (NOTE: prev-class pooling is a measured NULL — scripts/semantic_gate. The class's
    PREDICTIVE value is topical, via SemanticCarry below, not this.)"""
    def key_of(word: str):
        return space.class_of(word)
    key_of.mode = "semantic"
    return key_of


class SemanticCarry:
    """
    A decaying memory of recent CLASSES — the TOPIC, as the semantic generalisation of
    predict.CarryCache (which tracks exact word identity). When a word is observed, its
    distributional class is activated; `prob(w)` then primes ANY word of an active
    class, weighted by that word's frequency share of the class. So an on-topic word the
    exact-word cache never saw still gets predicted.

    MEASURED (scripts/semantic_carry): +0.53 bits/word OVER the word-cache alone — the
    distributional classes carry topical signal beyond exact recurrence. This is the
    semantic layer's predictive home (prev-class pooling was the null). Stateful and
    causal; `reset()` at a hard discontinuity.

    PROVENANCE: [NEW->original] — a class-level cache LM (cf. Kuhn & de Mori 1990) over
    EARNED distributional classes. No gradients (Law 6).
    """

    def __init__(self, space: SemanticSpace, unigram: Counter,
                 rate: float = 0.99, prune: float = 1e-3):
        self.space = space
        self.unigram = unigram
        self.rate = rate
        self.prune = prune
        self.class_tot = {c: (sum(unigram[w] for w in mem) or 1)
                          for c, mem in space.class_words.items()}
        self._tot = sum(unigram.values()) or 1
        self.weights: Dict[int, float] = {}
        self.total = 0.0

    def _info(self, word: str) -> float:
        """Self-information of a word (bits): -log2 P(word). Content/rare words carry
        more -> they should drive the topic; common words barely nudge it (earned)."""
        c = self.unigram.get(word, 0)
        return -math.log2(c / self._tot) if c else 0.0

    def observe(self, word: str) -> None:
        """Decay all class activations; activate the observed word's class, WEIGHTED by
        the word's self-information (so the topic tracks content, not frequency)."""
        for c in list(self.weights):
            self.weights[c] *= self.rate
            if self.weights[c] < self.prune:
                del self.weights[c]
        cw = self.space.class_of(word)
        if cw is not None:
            self.weights[cw] = self.weights.get(cw, 0.0) + (1.0 - self.rate) * self._info(word)
        self.total = sum(self.weights.values())

    def prob(self, word: str) -> float:
        """Topical prior on `word`: (activation of its class) x (its share of the class)."""
        c = self.space.class_of(word)
        if c is None or self.total <= 0:
            return 0.0
        wc = self.weights.get(c, 0.0)
        if wc <= 0:
            return 0.0
        return (wc / self.total) * (self.unigram.get(word, 0) / self.class_tot.get(c, 1))

    def top_members(self, n_classes: int = 3, per_class: int = 6) -> List[str]:
        """The frequent members of the most-active classes — the on-topic words to
        SURFACE as candidates in generation (the exact-word cache would miss them)."""
        active = sorted(self.weights, key=lambda c: -self.weights[c])[:n_classes]
        out: List[str] = []
        for c in active:
            out.extend(sorted(self.space.class_words.get(c, []),
                              key=lambda w: -self.unigram.get(w, 0))[:per_class])
        return out

    def active_topics(self, n: int = 3) -> List[str]:
        """A readable name for the current topic: the anchor-frames of the top classes."""
        active = sorted(self.weights, key=lambda c: -self.weights[c])[:n]
        return ["{" + ", ".join(self.space.class_anchors(c, 3)) + "}" for c in active]

    def reset(self) -> None:
        self.weights = {}
        self.total = 0.0


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    from elfix.running_text import load_utterances

    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    space = SemanticSpace(utts, vocab)
    print(f"distributional classes: {len(space.class_words):,} over "
          f"{len(space.word_class):,} words ({len(space.anchors)} anchors)\n")

    print("a few earned classes (their anchor-frame, members, width):")
    big = sorted(space.class_words, key=lambda k: -len(space.class_words[k]))
    for cid in big[:8]:
        print("  " + space.describe_class(cid))
    print("\nwords and the company they keep (their class):")
    for w in ("dog", "ran", "quickly", "president", "three", "paris", "she"):
        cid = space.class_of(w)
        mates = [m for m in space.class_words.get(cid, []) if m != w][:6] if cid is not None else []
        print(f"  {w:>10} -> class {cid}: {', '.join(mates) if mates else 'absent'}")
