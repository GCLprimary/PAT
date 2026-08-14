"""G-4/G-5: the selective generator — the reversed mirror (probes 24, 27, 28).

Analysis runs observation -> parts -> refuse-if-unknown. Generation runs
prompt -> audited continuation -> refuse-if-unattested. Probe 24's v1
(step-wise audit) FAILED selectivity (gap -5: it refused good prompts
more than salad) and stays in the repo as evidence; v2 is built from its
three lessons:

  1. PROMPT-RUNG REFUSAL. An unattested prompt — no trigram context with
     support >= 2 AND a broken internal bigram chain — refuses before a
     single word is emitted. Silent backoff past an unattested prompt is
     forbidden.
  2. WHOLE-CONTINUATION REFLECTION. Beam over trigram continuations
     (depth 6, width 8; backoff to bigram only mid-walk), then score each
     WHOLE continuation by topical coherence to the prompt (mean dense
     cosine of content words).
  3. ANTI-RUT. A continuation reusing any bigram is discarded (the flood
     check). The best survivor must clear theta_m or the generator
     refuses.

THE DUAL-CORPUS LAW (probes 22 + 27): the PROPOSER volume-scales — its
counts come from the largest registered corpus stack. The MEANING
geometry coherence-scales — it stays on the coherent default (Brown
dense). Volume proposes; coherence judges. Wiring them from the same
corpus repeats a measured mistake in one direction or the other.

G-5 (gated): path_action scores a continuation's mean squared step
through the dense space (probe 28: real sentences trace lower-action
paths than their own shuffles, 81%). The composite score
coherence - lambda*action ships behind audit="v3" and is promoted to
default ONLY by the inequality (gap AND coherence >= v2, salad 100%).
"""
from collections import Counter, defaultdict

import numpy as np

from .meaning import SOURCES, combine_sources, ensure_corpus

THETA_M = 0.15
BEAM_DEPTH = 6
BEAM_WIDTH = 8
STOP_K = 120
MIN_SENT = 6
LAMBDA_DEFAULT = 0.1


def load_sents(path=None, min_len=MIN_SENT):
    """Proposer sentences. Default: the largest registered corpus stack
    (the dual-corpus law's volume side)."""
    if path is None:
        path = combine_sources(list(SOURCES))
    with open(path, encoding="utf-8") as f:
        return [line.split() for line in f if len(line.split()) >= min_len]


def load_default_prompt_corpus():
    """Brown sentences (for probe-protocol prompt construction)."""
    with open(ensure_corpus(), encoding="utf-8") as f:
        return [line.split() for line in f if len(line.split()) >= MIN_SENT]


def _stack_rest_sents():
    """The pinned stack's non-Brown remainder, when the pinned
    corpus_big.txt embeds the pinned Brown corpus as a prefix (the
    artifact relationship of the probe machine's stack). None when the
    prefix relation doesn't hold — callers fall back to the registry."""
    from .config import DATA_DIR
    big_path = DATA_DIR / "corpus_big.txt"
    brown_path = DATA_DIR / "corpus.txt"
    if not (big_path.exists() and brown_path.exists()):
        return None
    brown = open(brown_path, encoding="utf-8").read().splitlines()
    big = open(big_path, encoding="utf-8").read().splitlines()
    if len(big) <= len(brown) or big[:len(brown)] != brown:
        return None
    return [l.split() for l in big[len(brown):]
            if len(l.split()) >= MIN_SENT]


def split_sents(sents, seed=5, frac=0.95):
    """Probe train/held split. Returns (train, held, rng) — the rng is
    handed back mid-stream so salad prompts draw from the probe's exact
    continuation of it."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(sents))
    cut = int(len(sents) * frac)
    train = [sents[i] for i in idx[:cut]]
    held = [sents[i] for i in idx[cut:]]
    return train, held, rng


class Proposer:
    """Trigram/bigram/unigram counts — the volume side."""

    def __init__(self, sents):
        self.uni = Counter()
        self.bi = defaultdict(Counter)
        self.tri = defaultdict(Counter)
        for s in sents:
            self.uni.update(s)
            for a, b in zip(s, s[1:]):
                self.bi[a][b] += 1
            for a, b, c in zip(s, s[1:], s[2:]):
                self.tri[(a, b)][c] += 1
        self.stop = set(w for w, _ in self.uni.most_common(STOP_K))

    def salad_vocab(self, n=3000, skip=300):
        return [w for w, _ in self.uni.most_common(n)[skip:]]


def canonical_setup(geometry, theta_m=THETA_M, audit="v2", lam=LAMBDA_DEFAULT,
                    n_prompts=100):
    """The acceptance protocol in one place (tests + demo share it).

    Prompts are probe-27 canonical: Brown sentences split 95/5 with
    rng(5); in-domain prompts are held Brown openings, salad prompts are
    the probe's continuation of the same rng stream. The proposer is the
    largest registry stack WITH Brown's held 5% excluded (no leakage of
    prompt sentences into proposer counts).

    Returns (generator, prompts_id, prompts_ood).
    """
    brown = load_default_prompt_corpus()
    brown_train, brown_held, rng = split_sents(brown)
    rest_sents = _stack_rest_sents()
    if rest_sents is None:
        rest = combine_sources(["gutenberg", "reuters"])
        with open(rest, encoding="utf-8") as f:
            rest_sents = [line.split() for line in f
                          if len(line.split()) >= MIN_SENT]
    proposer = Proposer(brown_train + rest_sents)
    gen = Generator(proposer, geometry, theta_m=theta_m, audit=audit, lam=lam)
    prompts_id = [tuple(s[:3]) for s in brown_held[:n_prompts]]
    vocab = proposer.salad_vocab()
    prompts_ood = [tuple(rng.choice(vocab, 3, replace=False))
                   for _ in range(n_prompts)]
    return gen, prompts_id, prompts_ood


class Generator:
    def __init__(self, proposer, geometry, theta_m=THETA_M,
                 depth=BEAM_DEPTH, width=BEAM_WIDTH,
                 audit="v2", lam=LAMBDA_DEFAULT):
        if audit not in ("v2", "v3"):
            raise ValueError("audit must be 'v2' or 'v3'")
        self.p = proposer
        self.g = geometry
        self.theta_m = theta_m
        self.depth = depth
        self.width = width
        self.audit = audit
        self.lam = lam

    # ── the meaning side (coherence judges) ──────────────────────────
    def topic_vec(self, words):
        vs = [self.g.vec(w) for w in words
              if w in self.g and w not in self.p.stop]
        if not vs:
            return None
        v = np.mean(vs, axis=0)
        n = np.linalg.norm(v)
        return v / n if n > 0 else None

    def coherence(self, cont, tv):
        ws = [w for w in cont if w in self.g and w not in self.p.stop]
        if tv is None or not ws:
            return -1.0
        return float(np.mean([self.g.vec(w) @ tv for w in ws]))

    def path_action(self, cont):
        """G-5 (probe 28): mean squared step through the dense space of
        the continuation's content words. 0 when fewer than two."""
        vs = [self.g.vec(w) for w in cont
              if w in self.g and w not in self.p.stop]
        if len(vs) < 2:
            return 0.0
        steps = [np.linalg.norm(vs[i + 1] - vs[i]) for i in range(len(vs) - 1)]
        return float(np.mean(np.square(steps)))

    def _score(self, cont, tv):
        c = self.coherence(cont, tv)
        if self.audit == "v3":
            return c - self.lam * self.path_action(cont)
        return c

    # ── the proposer side (volume proposes) ──────────────────────────
    def prompt_attested(self, prompt):
        p = tuple(prompt)
        tri_hit = ((p[-2], p[-1]) in self.p.tri and
                   sum(self.p.tri[(p[-2], p[-1])].values()) >= 2)
        bigs = all(p[i + 1] in self.p.bi.get(p[i], {})
                   for i in range(len(p) - 1))
        return tri_hit or bigs

    def beams(self, prompt):
        outs = [(list(prompt), set())]
        for _ in range(self.depth):
            nxt = []
            for path, used in outs:
                ctx = (path[-2], path[-1])
                cands = self.p.tri.get(ctx)
                pool = (cands.most_common(3) if cands else
                        (self.p.bi[path[-1]].most_common(2)
                         if path[-1] in self.p.bi else []))
                for w, _ in pool:
                    bg = (path[-1], w)
                    if bg in used:          # anti-rut: no bigram twice
                        continue
                    nxt.append((path + [w], used | {bg}))
            outs = nxt[:self.width * 3]
            outs = outs[:self.width]
            if not outs:
                break
        return [p[len(prompt):] for p, _ in outs]

    # ── the loop, reversed ───────────────────────────────────────────
    def generate(self, prompt):
        """-> (continuation | None, status)."""
        prompt = list(prompt)
        if not self.prompt_attested(prompt):
            return None, "REFUSE_PROMPT"
        tv = self.topic_vec(prompt)
        bs = self.beams(prompt)
        if not bs:
            return None, "REFUSE_NO_BEAM"
        scores = [self._score(c, tv) for c in bs]
        best = bs[int(np.argmax(scores))]
        # the refusal gate stays on raw coherence in both audits, so the
        # v3 flag can never weaken salad refusal (promotion requires it)
        if self.coherence(best, tv) < self.theta_m:
            return None, "REFUSE_AUDIT"
        return best, "OK"
