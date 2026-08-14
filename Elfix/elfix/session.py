"""
elfix/session.py  —  the input/output wrap: a stateful read <-> respond loop
============================================================================
The capstone that turns the measured components into one interactive thing. A
Session READS input (tag -> sound -> learn -> remember), RESPONDS (carry-conditioned
generation over the real context), and LOCALISES where meaning had to attach — all
inspectable (Law 6), all governed.

THE READ/WRITE ASYMMETRY (the contamination guard, lived):
  read(text)   = EXTERNAL input. Tag each word (attested/inferred/oov), update WORKING
                 memory (the carry) and LONG-TERM memory (ingest, source='input' — it
                 trains). Report per-word SURPRISAL: how unexpected each word was = how
                 much the model just learned, and where MEANING carried the signal the
                 counts could not (the locator, live).
  respond(n)   = the model's OWN output. Generated CONDITIONED ON THE CARRY (the real
                 read context — so it is on-topic, not the free-run 'the the the' loop),
                 then remembered as source='self' (QUARANTINED — never trains). The
                 system learns from OTHERS, never from itself.

State persists across turns: the carry decays (working memory), the acquired store
accumulates (long-term memory), the attested base stays frozen (ground knowledge) —
the three timescales, now driven by a live stream.

PROVENANCE: [NEW->original]. Composes predict (Predictor/CarryCache/AcquiredContext),
running_text-style tagging, and the Tier-5 carry. No gradients (Law 6).
"""
from __future__ import annotations
import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from .predict import (Predictor, CarryCache, EARNED_CARRY_RATE, EARNED_CARRY_BETA,
                      _sample)
from .semantic import SemanticCarry
from .syntax_tree import SyntaxTree, ConstituentController, RoleTagger
from .oov import infer_class, build_suffix_class
from .lexicon.ortho_affix import decompose
from .lexicon.compose_pron import compose

REPLACE_AT = 2          # EARNED crossover (scripts/oov_place): once a new word has been
                        # read >= twice, its own CONTEXT places it better than the
                        # morphological cold-start -> re-place it by accumulated context.


@dataclass
class ReadToken:
    word: str
    tag: str                       # 'attested' | 'inferred' | 'oov'
    n_phonemes: int
    surprisal: Optional[float]     # bits, -log2 P(word | prev); None at a cold start / oov


@dataclass
class ReadResult:
    tokens: List[ReadToken]
    mean_surprisal: float          # how surprised the model was overall (its 'effort')
    learned: int                   # in-vocab words folded into long-term memory
    grown: int = 0                 # NEW words pronounced from their shape this read


class Session:
    """A live read <-> respond loop over the ladder, holding state across turns."""

    def __init__(self, predictor: Predictor, cmu: Dict[str, List[str]], store=None,
                 space=None, scaffold=None, carry_rate: float = EARNED_CARRY_RATE,
                 beta: float = EARNED_CARRY_BETA, learn: bool = True, factored: bool = False):
        self.p = predictor
        if factored and space is not None and scaffold is not None and predictor.factored is None:
            predictor.attach_factored(space, scaffold)   # deploy the +0.81-bit factored base
        self.cmu = cmu                       # attested pronunciations (for tagging)
        self.store = store                   # optional InferredStore (inferred prons)
        self.carry = CarryCache(carry_rate)  # working memory: recent WORDS
        # the TOPIC: recent distributional CLASSES (the semantic layer, +0.53 bits)
        self.sem_carry = SemanticCarry(space, predictor.unigram) if space is not None else None
        self.space = space
        self.scaffold = scaffold             # the grammatical class-bigram (SyntaxScaffold)
        self._tree: Optional[SyntaxTree] = None   # lazily-built constituent parser (shares the
                                                  # scaffold); the binder is costly, so cache it
        self.roles: Optional[RoleTagger] = None   # lazily-built predicate/argument tagger (POS
                                                  # from functor context) — types the locator
        # suffix -> dominant class, for placing a NEW word from its shape (a WEAK
        # cold-start guess: scripts/oov_gate measured morphology->class only ~15% of
        # the way to the true class, so real placement comes from CONTEXT, below).
        self.suffix_dom = build_suffix_class(space, cmu.__contains__) if space else None
        self.beta = beta
        self.learn = learn
        self.history: List[str] = []
        self.surprises: List[Tuple[str, float]] = []   # (word, surprisal) read so far
        self.grown_ctx: Dict[str, list] = {}           # grown word -> [anchor cooc, count]
        self.replaced = 0                              # grown words re-placed by context

    # ── tagging (attested ground truth wins; then inferred; else oov) ─────────────
    def _tag(self, w: str) -> Tuple[Optional[List[str]], str]:
        if w in self.cmu:
            return self.cmu[w], "attested"
        if self.store is not None:
            pron, src = self.store.lookup(w)
            if src.startswith("inferred"):
                return pron, "inferred"
        return None, "oov"

    def _grow(self, w: str) -> Optional[List[str]]:
        """Close the loop on a NEW word: PRONOUNCE it from its shape (decompose into a
        known stem + suffix, compose with the earned allomorphy — Half A's validated
        job), register it in the store, add it to the predictable vocab, and place it
        in a (weak, morphological) class so the topic layer can hold it. After this the
        word is a first-class citizen whose real PLACEMENT comes from CONTEXT (the
        acquired store + its true distribution), not the weak morphology bridge."""
        if self.store is None or w in self.p.vocab:
            return None
        for stem, suf in decompose(w, self.cmu.__contains__):
            pron = compose(self.cmu[stem], suf)
            if pron is not None:
                self.store.propose(w, pron, stem, suf, f"read:{stem}+{suf}")
                self.p.vocab.add(w)                      # the lexicon grows as it reads
                if self.space is not None and w not in self.space.word_class:
                    cid, _ = infer_class(w, self.space, self.cmu.__contains__,
                                         self.suffix_dom)
                    if cid is not None:                  # weak cold-start placement
                        self.space.word_class[w] = cid
                        self.space.class_words[cid].append(w)
                    self.grown_ctx[w] = [Counter(), 0]   # track to RE-PLACE by context
                return list(pron)
        return None

    def _replace_grown(self, words: List[str]) -> None:
        """RE-PLACE grown OOV words by their ACCUMULATED context (the validated
        distributional method): the morphological cold-start is only a first guess —
        once a word has been read >= REPLACE_AT times, its own company places it better
        (scripts/oov_place). Updates the space's class view (re-derivable, never the
        attested core)."""
        if self.space is None or not self.grown_ctx:
            return
        win = self.space.params["window"]
        aset = self.space.anchor_set
        for i, w in enumerate(words):
            slot = self.grown_ctx.get(w)
            if slot is None:
                continue
            acc, _ = slot
            for j in range(max(0, i - win), min(len(words), i + win + 1)):
                if j != i and words[j] in aset:
                    acc[words[j]] += 1
            slot[1] += 1
            if slot[1] >= REPLACE_AT:
                pcid, _ = self.space.place(acc, sum(acc.values()))
                if pcid is not None and pcid != self.space.class_of(w):
                    old = self.space.word_class.get(w)
                    if old is not None and w in self.space.class_words.get(old, []):
                        self.space.class_words[old].remove(w)
                    self.space.word_class[w] = pcid
                    self.space.class_words[pcid].append(w)
                    self.replaced += 1

    # ── READ: tag, measure surprise, remember (working + long-term), learn ───────
    def read(self, text: str) -> ReadResult:
        words = [w for w in text.lower().split() if w]
        prev = next((w for w in reversed(self.history) if w in self.p.vocab), None)
        toks: List[ReadToken] = []
        grown = 0
        for w in words:
            pron, tag = self._tag(w)
            if tag == "oov" and (g := self._grow(w)) is not None:
                pron, tag, grown = g, "inferred", grown + 1   # pronounced a new word
            surp = None
            if prev is not None and prev in self.p.vocab and w in self.p.vocab:
                surp = -math.log2(self.p.prob(prev, w))
                self.surprises.append((w, surp))
            toks.append(ReadToken(w, tag, len(pron) if pron else 0, surp))
            if w in self.p.vocab:
                self.carry.observe(w)        # working memory: the word
                if self.sem_carry is not None:
                    self.sem_carry.observe(w)  # topic memory: the word's class
            prev = w
        learned = self.p.ingest(words, source="input") if self.learn else 0   # long-term
        self._replace_grown(words)              # refine grown OOV by accumulated context
        self.history.extend(words)
        surps = [t.surprisal for t in toks if t.surprisal is not None]
        return ReadResult(toks, sum(surps) / len(surps) if surps else 0.0, learned, grown)

    # ── RESPOND: carry-conditioned continuation over the REAL context ────────────
    def respond(self, n: int = 12, temperature: float = 0.6, rng_seed: int = 0,
                beta: float = 0.2, sem_beta: float = 0.15,
                sem_adapt: Optional[Tuple[float, float]] = (0.6, 9.0), no_repeat: int = 8,
                fn_penalty: float = 0.25, grammar: float = 1.0,
                position_bias: float = 0.0, boundaries: bool = False,
                constituency: float = 0.0, controller=None,
                remember: bool = True) -> List[Tuple[str, float, str]]:
        """Continue the conversation, conditioning each step on the carry (recent WORDS)
        AND the topic (recent CLASSES, the semantic layer). The topic stays anchored to
        the READ context (the sem_carry is NOT fed the reply — it does not drift onto its
        own output). The reply is remembered as source='self' -> QUARANTINED.

        GENERATION LEVERS (heuristics that trade perplexity for content/coherence — the
        floor is perplexity-OPTIMAL, scripts/adaptive_topic, so lifting it is a different
        objective). The defaults are the measured-best config (scripts/generate_quality:
        content 36%->84%, on-topic 63%->84%, repeat 11%->1%); they are tunable knobs like
        temperature, NOT earned constants:
          sem_adapt=(bc_max, h_ref)  lean on the TOPIC at high-entropy blind spots.
          no_repeat=W                down-weight any word emitted in the last W steps
                                     (breaks the carry's repetition cycles). Tuned to 8:
                                     a 4-window was too short for longer responses (the
                                     topic re-primes the same word at distance ~6); 8
                                     lifts content-diversity 0.62->0.71, on-topic 75->80%,
                                     content held -- an existing knob, not new machinery.
          fn_penalty<1               down-weight FUNCTION words (the earned skeleton) to
                                     push output toward content.
          grammar>0                  bias each candidate by the class-BIGRAM (SyntaxScaffold)
                                     P(class(w)|class(prev))**grammar — put function words
                                     back WHERE grammar wants them ('of the', 'to find').
          position_bias>0            bias each candidate by its class's sentence POSITION
                                     (subjects early, objects late — the measured arc).
          boundaries=True            end sentences by the arc's end-model -> bounded output
                                     (a '.' token marks each break).
          constituency>0             the PARSE-GUIDED lever (elfix.syntax_tree): penalise a
                                     candidate that would re-enter the OPEN constituent
                                     with a repeated class — the non-local closure signal
                                     the flat class-bigram cannot see, the structural fix
                                     for the 'president kennedy president kennedy' stall.
                                     Opt-in (default off) until its structure gate earns it
                                     on (scripts/parse_guided).
          controller                 inject a constituency controller (ConstituentController
                                     or any reset/observe/penalty_signal object) instead of
                                     the default — used by the gate to swap in a flat-window
                                     control. None builds the default from the scaffold."""
        prev = next((w for w in reversed(self.history) if w in self.p.vocab), None)
        if prev is None:
            return []
        rng = random.Random(rng_seed)
        out: List[Tuple[str, float, str]] = []
        recent: List[str] = []
        sb = sem_beta if self.sem_carry is not None else 0.0
        sa = sem_adapt if self.sem_carry is not None else None
        skel = self.space.skeleton if self.space is not None else set()
        use_gram = grammar > 0 and self.scaffold is not None
        use_pos = position_bias > 0 and self.scaffold is not None
        use_bound = boundaries and self.scaffold is not None
        use_con = constituency > 0 and (controller is not None or self.scaffold is not None)
        if use_con:
            if controller is None:
                if self._tree is None:           # the binder is costly: build the tree once
                    self._tree = SyntaxTree(self.scaffold)
                controller = ConstituentController(self._tree)
            controller.reset()                   # fresh constituent state for this response
        mean_len = self.scaffold.mean_len if self.scaffold is not None else 12.0
        pos_in_sent = 0
        for _ in range(n):
            ranked, h, level = self.p.predict(prev, k=20, cache=self.carry, beta=beta,
                                              sem_cache=self.sem_carry, sem_beta=sb,
                                              sem_adapt=sa)
            if not ranked:
                break
            frac = min(1.0, pos_in_sent / mean_len)
            cand = []
            for word, pr, c in ranked:
                if word == prev:                 # no ADJACENT repeat (dissimilation)
                    continue
                if no_repeat and word in recent:
                    pr *= 0.05                    # break carry-driven cycles
                if fn_penalty != 1.0 and word in skel:
                    pr *= fn_penalty              # push toward content words
                if use_gram:
                    pr *= self.scaffold.trans(prev, word) ** grammar   # grammatical shape
                if use_pos:
                    pr *= self.scaffold.pos_fit(word, frac) ** position_bias  # subject->object arc
                if use_con:
                    pr *= controller.penalty_signal(word) ** constituency  # don't over-saturate a phrase
                cand.append((word, pr, c))
            w = _sample(cand or ranked, temperature, rng)
            out.append((w, h, level))
            self.carry.observe(w)
            if use_con:
                controller.observe(w)            # fold the emitted word into the open constituent
            recent.append(w)
            if no_repeat and len(recent) > no_repeat:
                recent.pop(0)
            prev = w
            pos_in_sent += 1
            if use_bound and rng.random() < self.scaffold.end_prob(w, pos_in_sent):
                out.append((".", 0.0, "boundary"))     # the sentence completes here
                prev = ""                              # a fresh sentence start (-> backoff)
                pos_in_sent = 0
                if use_con:
                    controller.reset()                 # a new sentence -> a fresh constituent
                # keep `recent` across the boundary: the no-repeat window must still
                # block a topic word from recurring every sentence ('selma . selma').
        said = [w for w, _, _ in out if w != "."]
        self.history.extend(said)
        if remember and said:
            self.p.ingest(said, source="self")   # learn from others, NEVER from yourself
        return out

    # ── the semantic locator, live: where meaning carried the signal ─────────────
    def locator(self, k: int = 5) -> List[Tuple[str, float]]:
        """The most SURPRISING words read so far — where counted/sound context could
        NOT predict the next word, so MEANING must have carried it. The system points
        at where the semantic layer has to explain, by failing readably."""
        return sorted(self.surprises, key=lambda x: -x[1])[:k]

    def topics(self, n: int = 3) -> List[str]:
        """The currently-active distributional classes — a readable name for what the
        conversation is ABOUT right now (the semantic carry). [] if no space attached."""
        return self.sem_carry.active_topics(n) if self.sem_carry is not None else []

    def _ensure_roles(self) -> Optional[RoleTagger]:
        """Lazily earn the predicate/argument tagger (POS from functor context) when a
        space is attached — built from the predictor's word-bigram, so it is free of any
        extra corpus pass. Cached. None if there is no space (no anchors to bridge from)."""
        if self.roles is None and self.space is not None:
            self.roles = RoleTagger(self.p.bigram, self.space.skeleton, self.space.anchors[0])
        return self.roles

    def locator_typed(self, k: int = 5) -> List[Tuple[str, float, Optional[str], Optional[str]]]:
        """The locator, with each surprising word TYPED two ways: by its distributional
        CLASS (what topic/company) and by its earned PART OF SPEECH (predicate vs argument
        — the RoleTagger, POS from functor context, the distinction the topical classes do
        NOT carry). Not just WHERE meaning attached (high surprisal) but WHAT KIND of word
        carried the signal — e.g. an unexpected ARGUMENT is a new entity/topic; an
        unexpected PREDICATE is a new relation/event. Returns [(word, surprisal, type,
        role)]: `type` the class anchor-frame ('{open, door, behind}') or None; `role`
        'predicate' / 'argument' or None (a functor / too-rare word / no space)."""
        roles = self._ensure_roles()
        out = []
        for w, h in self.locator(k):
            t = None
            if self.space is not None:
                cid = self.space.class_of(w)
                if cid is not None:
                    t = "{" + ", ".join(self.space.class_anchors(cid, 3)) + "}"
            role = None
            if roles is not None:
                sc = roles.score(w)
                if sc is not None:
                    role = "predicate" if sc >= 0.5 else "argument"
            out.append((w, h, t, role))
        return out


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    from elfix.running_text import load_utterances

    from elfix.semantic import SemanticSpace, SyntaxScaffold
    from elfix.lexicon.inferred_store import InferredStore
    cmu = load_cmu()
    utts = load_utterances()
    p = Predictor(utts[:40000], set(cmu.keys()))     # the base model
    print("(earning the distributional classes + syntactic scaffold...)")
    space = SemanticSpace(utts[:40000], set(cmu.keys()), unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:40000], set(cmu.keys()))
    s = Session(p, cmu, store=InferredStore(cmu), space=space, scaffold=scaffold)

    stream = [" ".join(u) for u in utts[40000:40003]]
    print("\n=== a SESSION: read -> learn + remember + TOPIC -> respond ===\n")
    for i, line in enumerate(stream, 1):
        r = s.read(line)
        print(f"read {i}: {line[:66]}{'...' if len(line) > 66 else ''}")
        print(f"   {len(r.tokens)} words, mean surprisal {r.mean_surprisal:.1f} bits, "
              f"learned {r.learned}; topic now {', '.join(s.topics(2))}")
        reply = s.respond(n=20, temperature=0.5, rng_seed=i,
                          boundaries=True, position_bias=1.5)   # bounded, subject-arced
        print(f"   respond: {' '.join(w for w, _, _ in reply)}\n")

    print("=== the TYPED semantic locator (where meaning attached, and WHAT KIND) ===")
    for w, h, t, role in s.locator_typed():
        kind = f"{role} {t}" if role else (t or "function/uncl.")
        art = "an" if role == "argument" else "a"
        print(f"   '{w}' ({h:.0f} bits) -- {art} {kind} word counted context could not predict")
    print(f"\nstate: working memory {len(s.carry.weights)} words; topic "
          f"{len(s.sem_carry.weights)} active classes; long-term store +"
          f"{s.p.acquired.seen_ext:,} transitions; attested base frozen.")

    # ── closing the loop: a NEW word, handled end-to-end from its shape ───────────
    print("\n=== OOV: read a word never seen, pronounce it, make it a citizen ===")
    # a real novel inflection of a known stem (not in CMU)
    new_word = next((st + "ing" for st in ("kayak", "blog", "google", "tweet", "email",
                     "refactor", "downsize") if st in cmu and st + "ing" not in cmu),
                    None)
    if new_word:
        before = new_word in s.p.vocab
        r = s.read(f"she kept {new_word} all afternoon and then {new_word} again")
        tok = next(t for t in r.tokens if t.word == new_word)
        print(f"   read a sentence with '{new_word}' (in vocab before? {before})")
        print(f"   -> grown {r.grown}: tagged '{tok.tag}', {tok.n_phonemes} phonemes "
              f"composed from its stem+ing; now in vocab? {new_word in s.p.vocab}")
        nxt = s.p.predict(new_word, k=3)[0]
        print(f"   it is now PREDICTABLE from the context it arrived in: "
              f"'{new_word}' -> {', '.join(w for w, _, _ in nxt)}")
        print(f"   read twice -> RE-PLACED by context ({s.replaced} word moved from its "
              f"morphological\n    cold-start to its context class -- crossover at 2 reads, "
              f"scripts/oov_place).")
        print("   (pronounced from SOUND/shape for the first sighting; placed by "
              "DISTRIBUTION\n    once it has evidence -- the competence map, applied to the "
              "new word itself.)")
