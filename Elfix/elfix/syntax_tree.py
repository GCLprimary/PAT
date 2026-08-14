"""
elfix/syntax_tree.py  —  the constituent/stack mechanism (the next model class)
================================================================================
The 1st-order ceiling is HIERARCHY, not context-length (scripts/ngram_ceiling): the
flat class-bigram holds the LINEAR class sequence, but the output STALLS inside a
constituent ('president kennedy president kennedy ...') because a flat model has no
notion of phrase CLOSURE. Crossing that ceiling needs a different model class —
constituent structure: a recursive bracketer that NESTS (a tree = a stack).

This module is that mechanism, built (not just scouted — scripts/constituents did the
scouting). Two things, sharing one earned binding signal:

  SyntaxTree.parse(words) -> Node     a RECURSIVE agglomerative bracketer: repeatedly
      merge the strongest-binding adjacent span FIRST, building a binary constituent
      tree (a readable parse). This is the Tier-3 emergent-unit move (merge by
      coherence) lifted to syntax — and it PRODUCES NESTING, where a FLAT trough
      chunker failed (constituency is global/recursive, not a local contour).

  ConstituentController                an ONLINE version of the same bracketer, for
      GENERATION: it tracks the current OPEN constituent left-to-right and reports when
      a candidate would over-saturate it (re-enter a phrase that already has its head —
      the structural signature of the stall). The fix the flat bigram cannot make,
      because saturation is NON-LOCAL (it depends on how long the constituent has been
      open, not just on prev).

THE BINDING SIGNAL (earned, counted — Law 1/6)
----------------------------------------------
binding(c1, c2) = directed PMI of the adjacent class transition c1->c2: how much more
c2 follows c1 than chance, over the SyntaxScaffold's class-bigram. PMI > 0 means the
pair co-occurs adjacent MORE than chance (a constituent BOND); PMI <= 0 means LESS than
chance (a constituent BOUNDARY). So the boundary threshold is 0 — the chance line — an
EARNED principle, not a tuned constant (Law 1). The mean constituent LENGTH is earned
the same way: from the count-weighted fraction of adjacent pairs that bond.

WHAT IS / ISN'T CLOSED HERE (honest scope)
------------------------------------------
- The binding is class-pair PMI (edge-to-edge). HEADS are now EARNED and annotated on
  every node (`head_of`: content-over-functor; predicate-over-argument via RoleTagger;
  else right-headed — nominal compounds measured 90% right-headed under the symmetric
  substitutability test). THE DIVISION OF LABOUR IS A FINDING: heads NAME (category),
  edges BOND (distribution) — a saturated phrase does not keep its head's raw
  distribution (arguments transform it: '(took place)' continues like 'place'), so
  head-to-head binding measured WORSE and stays a flagged prototype (`head_aware`).
- Parse-guided generation is GATED on a structure metric, not assumed (scripts/
  parse_guided, scripts/clause_guided): the closure brake works but a flat class-window
  matches it — structural generation-control is not load-bearing. OPT-IN, honest.
- The parser's home is ANALYSIS (readable trees, categorial heads, typing the locator),
  per the measured nulls above.

PROVENANCE: [NEW->established] greedy mutual-information bracketing for unsupervised
constituency (Magerman & Marcus 1990); the agglomerative-merge move is Tier-3's
(emergent/emergent_unit.py), recursive. The online closure controller is [NEW->original].
No gradients anywhere (Law 6); every merge and every penalty is a count you can point at.
"""
from __future__ import annotations
import math
from collections import Counter
from typing import List, Optional, Iterator, Tuple, Dict


class ClassBinder:
    """The earned binding strength of an adjacent class transition: directed class-pair
    PMI over a SyntaxScaffold's class-bigram. Positive = a constituent BOND (above
    chance), non-positive = a BOUNDARY (below chance). All counted (Law 6).
    """

    def __init__(self, scaffold, floor: float = -6.0, class_verb=None):
        self.sc = scaffold
        self.floor = floor
        self.class_verb = class_verb or {}          # cid -> verb-ness (RoleTagger.class_scores)
        # marginals of the directed class-bigram: left[c1] = #(c1 ->), right[c2] = #(-> c2)
        self.N = sum(sum(r.values()) for r in scaffold.bg.values()) or 1
        self.left = {c: sum(r.values()) for c, r in scaffold.bg.items()}
        self.right: Counter = Counter()
        for c, r in scaffold.bg.items():
            for c2, k in r.items():
                self.right[c2] += k
        # the fraction of adjacent pairs that BOND (PMI > 0), count-weighted -> p_bond.
        # earns the mean constituent length analytically (see mean_constituent_len).
        bonded = 0
        for c, r in scaffold.bg.items():
            for c2, k in r.items():
                if self._pmi(c, c2) > 0.0:
                    bonded += k
        self.p_bond = bonded / self.N

    def headness(self, c) -> float:
        """Continuation entropy of a class (bits) — a DIAGNOSTIC, no longer the head rule.
        (It was the first content-content tiebreak and was MEASURED WRONG: adjectives have
        high continuation entropy, so it made 'blue' head '(blue eyes)'. The in-valence
        signal failed before it — connectives receive bonds from many classes, ranking
        functors as heads, backwards. Both kept out of head_of; earned rules replaced them.)"""
        r = self.sc.bg.get(c)
        if not r:
            return 0.0
        tot = sum(r.values())
        return -sum((k / tot) * math.log2(k / tot) for k in r.values() if k)

    def head_of(self, c1, c2):
        """The CATEGORIAL head of the constituent formed by bonding c1 then c2 — what KIND
        of thing the phrase is. Three EARNED rules (each measured, scratch headhood probes):
          1. functor vs content: the CONTENT word heads ('the dog' -> dog) — the skeleton rule.
          2. exactly one child predicate-classed (class_verb >= 0.5): the PREDICATE heads —
             the categorial fact; note the substitutability probe shows a saturated VP does
             NOT keep the verb's raw distribution (arguments TRANSFORM it: '(took place)'
             continues like 'place', not like bare 'took'), so this head is CATEGORIAL only.
          3. otherwise: the RIGHT child — earned: nominal compounds are 90% right-headed
             under the SYMMETRIC substitutability test ('(white house)' accepts 'house''s
             contexts at 0.94 vs 'white''s 0.04), with the exceptions themselves correct
             (title constructions: '(president kennedy)' -> president).
        IMPORTANT SCOPE (the head-aware finding): the head is for ANALYSIS (category).
        DISTRIBUTION propagates by the EDGES — the left edge governs leftward bonds, the
        right edge rightward — which is why edge-based parsing (the default) measured
        better than head-to-head binding. Heads name; edges bond."""
        f1, f2 = c1[0] == "fn", c2[0] == "fn"
        if f1 != f2:
            return c2 if f1 else c1                 # rule 1: the content word heads
        if c1[0] == "cl" and c2[0] == "cl":
            v1 = self.class_verb.get(c1[1])
            v2 = self.class_verb.get(c2[1])
            if v1 is not None and v2 is not None and (v1 >= 0.5) != (v2 >= 0.5):
                return c1 if v1 >= 0.5 else c2      # rule 2: the predicate heads (categorial)
        return c2                                   # rule 3: right-headed (earned, 90%)

    def _pmi(self, c1, c2) -> float:
        j = self.sc.bg.get(c1, {}).get(c2, 0)
        if j == 0:
            return self.floor
        return math.log2((j * self.N) / (self.left[c1] * self.right[c2]))

    def binding(self, c1, c2) -> float:
        """Directed PMI bits of c1 -> c2 (the constituent bond strength)."""
        return self._pmi(c1, c2)

    def mean_constituent_len(self) -> float:
        """EARNED mean constituent length. If each adjacent gap is a BOND with the
        corpus probability p (count-weighted fraction with PMI>0), a maximal run of
        bonds has, in expectation, p/(1-p) internal gaps -> 1/(1-p) words. So the mean
        constituent length is 1/(1 - p_bond) — earned from the binding distribution,
        no tuned constant (independence is an approximation, flagged)."""
        return 1.0 / (1.0 - min(self.p_bond, 0.999))


class Node:
    """A node in a binary constituent tree (a parse). A LEAF wraps one word; an INTERNAL
    node wraps two children merged at a binding strength. `lclass`/`rclass` are the
    syntactic classes at the node's two EDGES (what a neighbour binds to) — the v1
    carries both edges rather than a single projected HEAD (head-awareness is the
    flagged refinement, scripts/constituents). Readable: str() is the bracketing."""
    __slots__ = ("word", "left", "right", "lclass", "rclass", "head", "binding")

    def __init__(self, word: Optional[str] = None, left: "Node" = None,
                 right: "Node" = None, lclass=None, rclass=None, head=None,
                 binding: Optional[float] = None):
        self.word = word
        self.left = left
        self.right = right
        self.lclass = lclass
        self.rclass = rclass
        self.head = head                # the projected HEAD class (head-aware parse; else None)
        self.binding = binding          # the PMI at which this node was merged (None=leaf)

    @property
    def is_leaf(self) -> bool:
        return self.word is not None

    @property
    def words(self) -> List[str]:
        """The span this node covers, left to right."""
        if self.is_leaf:
            return [self.word]
        return self.left.words + self.right.words

    def head_word(self) -> Optional[str]:
        """The LEXICAL head of this constituent: descend into whichever child projected
        this node's head class. '(the (white house))' -> 'house'; '((the dog) barks)' ->
        'barks' (when the verb class is decisive). None if heads were not annotated."""
        if self.is_leaf:
            return self.word
        if self.head is None:
            return None
        for child in (self.left, self.right):
            if child.head == self.head:
                return child.head_word()
        return self.right.head_word()               # right-headed fallback (earned default)

    def constituents(self) -> Iterator[Tuple[str, ...]]:
        """Every MULTI-word constituent in the tree (each internal node's span), as a
        tuple of words. The bracketing the parse claims — what a gate checks."""
        if self.is_leaf:
            return
        yield tuple(self.words)
        yield from self.left.constituents()
        yield from self.right.constituents()

    def __str__(self) -> str:
        if self.is_leaf:
            return self.word
        return "(" + str(self.left) + " " + str(self.right) + ")"

    def __repr__(self) -> str:
        return f"Node({self})"


class SyntaxTree:
    """The recursive agglomerative bracketer: parse an utterance into a binary
    constituent tree by merging the strongest-binding adjacent span FIRST.

    >>> from elfix.syntax_tree import SyntaxTree
    >>> class _Sc:                         # a stub scaffold with a hand-set class-bigram
    ...     def sclass(self, w): return ('w', w)
    ...     bg = {('w','the'): {('w','dog'): 100},     # 'the' only ever precedes 'dog'
    ...           ('w','dog'): {('w','barks'): 50},    # 'barks' also reached from 'cats',
    ...           ('w','cats'): {('w','barks'): 100}}  # so 'dog barks' binds less tightly
    >>> t = SyntaxTree(_Sc())
    >>> str(t.parse(['the', 'dog', 'barks']))   # 'the dog' binds tightest -> brackets first
    '((the dog) barks)'
    """

    def __init__(self, scaffold, binder: Optional[ClassBinder] = None, class_verb=None):
        self.sc = scaffold
        self.binder = binder if binder is not None else ClassBinder(scaffold,
                                                                    class_verb=class_verb)

    def parse(self, words: List[str], vocab=None, head_aware: bool = False) -> Optional[Node]:
        """Greedy agglomerative bracketing -> a binary constituent tree (a parse).
        `vocab` (a set or membership-callable) optionally filters to known words.

        Every node is annotated with its CATEGORIAL head (binder.head_of — the earned
        rules: content-over-functor, predicate-over-argument, else right-headed). That is
        NAMING. BONDING is separate: the default binds by the EDGES (right edge of the
        left span to left edge of the right span), which is the measured-correct
        distributional interface. `head_aware=True` instead binds HEAD-to-HEAD — kept as
        the prototype it is (MEASURED slightly worse: binding by heads chains the tree,
        because a saturated phrase does not keep its head's raw distribution — arguments
        transform it). Heads name; edges bond."""
        if vocab is not None:
            inv = vocab.__contains__ if not callable(vocab) else vocab
            words = [w for w in words if inv(w)]
        units: List[Node] = [Node(word=w, lclass=self.sc.sclass(w), rclass=self.sc.sclass(w),
                                  head=self.sc.sclass(w)) for w in words]
        if not units:
            return None
        while len(units) > 1:
            bi, best = 0, -math.inf
            for i in range(len(units) - 1):
                b = (self.binder.binding(units[i].head, units[i + 1].head) if head_aware
                     else self.binder.binding(units[i].rclass, units[i + 1].lclass))
                if b > best:
                    best, bi = b, i
            l, r = units[bi], units[bi + 1]
            units[bi:bi + 2] = [Node(left=l, right=r, lclass=l.lclass, rclass=r.rclass,
                                     head=self.binder.head_of(l.head, r.head), binding=best)]
        return units[0]


class ConstituentController:
    """Parse-guided generation: an ONLINE bracketer that flags when the next word would
    OVER-SATURATE the current open constituent — the structural signature of the stall
    ('president kennedy president kennedy ...': re-entering a phrase that already has its
    head). The signal a FLAT class-bigram cannot represent, because saturation is
    NON-LOCAL — it depends on how long the constituent has stayed open, not just on prev.

    Use: observe() each emitted word to track the open constituent; penalty_signal()
    scores a candidate in (0, 1] (1 = neutral, < 1 = would over-saturate). The caller
    folds it in as `pr *= signal ** strength` (a generation LEVER like grammar, not an
    earned constant) and reset()s at a sentence boundary.

    THE RULE (the closure constraint): a candidate that would CLOSE the constituent
    (binding <= 0, the earned chance boundary) is never penalized — closure is exactly
    what breaks the stall. A candidate that would ATTACH (binding > 0) but REPEATS a
    class already in the open constituent is penalized (no two same-type heads in one
    phrase), the harder the more such heads are already there. So the generator is pushed
    to CLOSE the phrase (-> the grammar lever can then route to the owed predicate), not
    to keep stacking same-type heads. The brake is SCOPED TO THE OPEN CONSTITUENT — a
    class may freely RECUR across a phrase boundary (where the constituent reset), which
    is exactly what a flat class-window cannot do and where the parse earns its keep
    (scripts/parse_guided measures this against a flat-window control).

    NOTE (the saturation red herring, scripts/parse_guided): an earlier version only
    braked once the phrase exceeded the earned mean LENGTH. It was near-inert — the
    generator's content words mostly BOUNDARY off each other (sub-chance adjacency, the
    OCP/dissimilation finding), so the open constituent rarely reaches that length. The
    real signal is the repeated HEAD within whatever phrase is open, not its length.
    `mean_constituent_len` is kept (earned, readable) but is not the brake threshold.
    """

    def __init__(self, tree: SyntaxTree, boundary: float = 0.0):
        self.tree = tree
        self.binder = tree.binder
        self.sc = tree.sc
        self.boundary = boundary                                   # PMI chance line (earned)
        self.sat_len = self.binder.mean_constituent_len()          # earned, readable (not the brake)
        self.open: List = []                                       # classes in the open constituent

    def reset(self) -> None:
        """Start a fresh constituent (call at a sentence boundary)."""
        self.open = []

    def observe(self, word: str) -> None:
        """Fold an emitted word into the running parse: if it BOUNDARIES off the open
        constituent (binding <= chance) the constituent CLOSES and a new one starts."""
        c = self.sc.sclass(word)
        if self.open and self.binder.binding(self.open[-1], c) <= self.boundary:
            self.open = []                          # the previous constituent closed
        self.open.append(c)

    def penalty_signal(self, cand_word: str) -> float:
        """Score a candidate against the open constituent: 1.0 unless attaching it would
        REPEAT a class already in the open phrase, then 1/(1+already-present) — the brake,
        graded by how saturated the phrase is with that class. Function words are never
        penalized (they route by grammar); a candidate that CLOSES the phrase never is."""
        c = self.sc.sclass(cand_word)
        if not self.open or c[0] == "fn":
            return 1.0
        if self.binder.binding(self.open[-1], c) <= self.boundary:
            return 1.0                              # candidate CLOSES the phrase -> encourage
        rep = self.open.count(c)                    # same-type heads already in this phrase
        return 1.0 if rep == 0 else 1.0 / (1.0 + rep)


class RoleTagger:
    """Earn a PREDICATE(verb) / ARGUMENT(noun) score for content words from their FUNCTOR
    context — the POS distinction the TOPICAL distributional classes do NOT carry (verbs
    and nouns cluster by topic, not part-of-speech; a class-level N-V 2-colouring washes
    out, scripts-measured). A 2-hop bridge from the single most-frequent word (anchor-0 =
    'the', a determiner), fully earned, counted, no gradient (Law 6):

      hop1  noun_seed(w)    = how often content word w follows 'the'  (nouns follow determiners)
      hop2  nominal_ness(f) = mean noun_seed of the words functor f precedes
                              (-> determiners score high, auxiliaries/pronouns low)
      hop3  verb_score(w)   = mass of w's predecessors that are NON-nominal (verbal) functors

    The raw verb_score is min-max calibrated on a robust [5th,95th]-percentile range so a
    pure noun ~0 and a pure verb ~1 (even 'the' has nominal_ness < 0.5, compressing the raw
    scale). `score(w)` returns the calibrated value in [0,1] or None (functor / too rare);
    `is_predicate(w)` thresholds at 0.5.

    PROVENANCE: [NEW->established] distributional POS induction from closed-class context
    (cf. Brown et al. 1992; Schütze 1995), here a counted 2-hop bridge from one earned anchor.
    """

    def __init__(self, bigram, skeleton, det_anchor, min_count: int = 5):
        prevf = {}                                   # content word -> Counter(preceding functor)
        for prev, row in bigram.items():
            if prev in skeleton:                     # a functor predecessor
                for w, k in row.items():
                    if w not in skeleton:            # a content successor
                        prevf.setdefault(w, Counter())[prev] += k
        # hop 1: noun_seed = fraction of a word's functor-predecessors that are the anchor
        noun_seed = {}
        for w, pf in prevf.items():
            t = sum(pf.values())
            if t >= min_count:
                noun_seed[w] = pf.get(det_anchor, 0) / t
        # hop 2: a functor is nominal if the words it precedes are noun-like (high noun_seed)
        fol_acc: Dict[str, float] = {}
        fol_tot: Dict[str, float] = {}
        for w, pf in prevf.items():
            if w in noun_seed:
                for f, k in pf.items():
                    fol_acc[f] = fol_acc.get(f, 0.0) + k * noun_seed[w]
                    fol_tot[f] = fol_tot.get(f, 0.0) + k
        self.nominal_ness = {f: fol_acc[f] / fol_tot[f] for f in fol_tot if fol_tot[f] >= 20}
        # hop 3: verb_score = mass of predecessors that are VERBAL (1 - nominal_ness)
        raw = {}
        for w, pf in prevf.items():
            t = sum(pf.values())
            if t >= min_count:
                raw[w] = sum(k * (1.0 - self.nominal_ness.get(f, 0.5))
                             for f, k in pf.items()) / t
        # calibrate to a robust range so pure nouns ~0, pure verbs ~1
        vals = sorted(raw.values())
        if vals:
            lo = vals[int(0.05 * (len(vals) - 1))]
            hi = vals[int(0.95 * (len(vals) - 1))]
        else:
            lo, hi = 0.0, 1.0
        span = (hi - lo) or 1.0
        self._raw = raw
        self.verb = {w: min(1.0, max(0.0, (v - lo) / span)) for w, v in raw.items()}

    def score(self, word: str) -> Optional[float]:
        """Calibrated verb_score in [0,1] (1=predicate/verb, 0=argument/noun), or None for
        a functor / too-rare word with no reliable functor context."""
        return self.verb.get(word)

    def is_predicate(self, word: str) -> bool:
        """Whether `word` is verb-like (a predicate). False for nouns and unscored words."""
        v = self.verb.get(word)
        return v is not None and v >= 0.5

    def class_scores(self, space, unigram) -> Dict[int, float]:
        """Lift the word-level verb_score to CLASS level: frequency-weighted mean over a
        class's scored members. MEASURED honest blur: the topical classes mix POS, so only
        the extremes are decisive (~54 clearly-noun + ~73 clearly-verb of 300; the middle
        ~blurred) — which is exactly why the class-level N-V 2-colouring washed out. Used
        by ClassBinder.head_of rule 2, whose decisive-threshold + right-head fallback is
        designed for this blur. Returns {class_id: verb-ness in [0,1]} (absent if no
        member is scored — Law 2)."""
        out: Dict[int, float] = {}
        for cid, mem in space.class_words.items():
            num = den = 0.0
            for w in mem:
                s = self.verb.get(w)
                if s is not None:
                    f = unigram.get(w, 1)
                    num += f * s
                    den += f
            if den:
                out[cid] = num / den
        return out


class ClauseController:
    """Parse-guided generation, CLAUSE level: track whether the current clause has its
    PREDICATE yet, and brake argument-stacking while a verb is OWED — the structural fix
    for the all-argument stall ('president kennedy senator johnson …': a subject NP that
    never closes into a predicate). This is the half the head-unaware ConstituentController
    could not do: it needs the earned predicate/argument distinction (RoleTagger), which
    the topical classes do not carry.

    THE RULE ('don't run past an open subject until a verb is owed'): once an ARGUMENT has
    been emitted and NO predicate yet, a further argument is braked (the stall) and a
    predicate is free (relatively boosted). After a verb, arguments are free again (the
    object). reset() at a sentence boundary. Same reset/observe/penalty_signal interface as
    ConstituentController, so it plugs into Session.respond(controller=…).
    """

    def __init__(self, roles: RoleTagger, brake: float = 0.3):
        self.roles = roles
        self.brake = brake
        self.reset()

    def reset(self) -> None:
        self.has_arg = False
        self.has_verb = False

    def observe(self, word: str) -> None:
        r = self.roles.score(word)
        if r is None:
            return                                   # functors don't fill the clause core
        if r >= 0.5:
            self.has_verb = True                     # a predicate landed -> clause has its verb
        else:
            self.has_arg = True                      # an argument (subject/object) is present

    def penalty_signal(self, cand_word: str) -> float:
        r = self.roles.score(cand_word)
        if r is None:
            return 1.0                               # functors route by grammar, not here
        if self.has_arg and not self.has_verb:       # a subject is open, a verb is OWED
            return 1.0 if r >= 0.5 else self.brake   # let the predicate through; brake another arg
        return 1.0


def _bracket_dirs(words, sclass, binder, choose):
    """Bracket `words`; return, for each leaf index, the DIRECTION of its first merge
    ('R' = attached to its right complement, 'L' = to its left). `choose` picks the merge
    from the edge-bindings — the PMI parser picks the max, the random baseline at random
    — so the two are compared like-for-like. (Function words attach to their complement
    on the right: a good parser merges det/prep RIGHTWARD.)"""
    units = [(i, i + 1, sclass(w), sclass(w)) for i, w in enumerate(words)]  # lo,hi,lclass,rclass
    first_dir = {}
    while len(units) > 1:
        binds = [binder.binding(units[i][3], units[i + 1][2]) for i in range(len(units) - 1)]
        bi = choose(binds)
        l, r = units[bi], units[bi + 1]
        first_dir.setdefault(l[1] - 1, "R")     # right edge of left unit merges rightward
        first_dir.setdefault(r[0], "L")         # left edge of right unit merges leftward
        units[bi:bi + 2] = [(l[0], r[1], l[2], r[3])]
    return first_dir


if __name__ == "__main__":
    import sys
    import random
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu
    from elfix.running_text import load_utterances
    from elfix.semantic import SemanticSpace, SyntaxScaffold

    from elfix.predict import Predictor

    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    print("(earning distributional classes + syntactic scaffold + roles...)")
    p = Predictor(utts[:50000], vocab)
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:50000], vocab)
    roles = RoleTagger(p.bigram, space.skeleton, space.anchors[0])
    tree = SyntaxTree(scaffold, class_verb=roles.class_scores(space, p.unigram))
    binder = tree.binder
    print(f"binder: p_bond {binder.p_bond:.2f} -> earned mean constituent length "
          f"{binder.mean_constituent_len():.2f} words\n")

    print("RECURSIVE agglomerative bracketing of real sentences (merge tightest bond first;")
    print("each parse annotated with its earned CATEGORIAL head — heads name, edges bond):")
    shown = 0
    for u in utts[50000:50400]:
        if 5 <= len(u) <= 10 and all(w in vocab for w in u):
            node = tree.parse(u)
            print(f"   {node}   [head: {node.head_word()}]")
            shown += 1
            if shown == 8:
                break

    def lab(c):
        if c[0] == "fn":
            return "'" + c[1] + "'"
        return "{" + ",".join(space.class_words[c[1]][:2]) + "}" if c[0] == "cl" else "unk"

    pairs = [(binder.binding(c1, c2), c1, c2) for c1 in scaffold.bg for c2 in scaffold.bg[c1]
             if scaffold.bg[c1][c2] >= 100]
    print("\nthe tightest class-bonds (merged FIRST = the grammatical units):")
    for b, c1, c2 in sorted(pairs, reverse=True)[:8]:
        print(f"   {b:+.1f}  {lab(c1)} -> {lab(c2)}")

    # ── PROXY: function words (determiners, prepositions) attach to their COMPLEMENT on
    # the right ('the dog', 'of kennedy'). Does the parser merge them RIGHTWARD more than
    # a random bracketing? (A right-attachment measure — robust to the det-over-whole-NP
    # caveat that makes a strict 2-word-constituent proxy crude.)
    rng = random.Random(0)
    pmi_r = pmi_tot = rnd_r = rnd_tot = 0
    for u in utts[50000:53000]:
        ws = [w for w in u if w in vocab]
        if not (4 <= len(ws) <= 14):
            continue
        # function words with a content word to their right (det/prep + head), not final
        targets = [i for i in range(len(ws) - 1)
                   if scaffold.sclass(ws[i])[0] == "fn" and scaffold.sclass(ws[i + 1])[0] != "fn"]
        if not targets:
            continue
        dp = _bracket_dirs(ws, scaffold.sclass, binder, lambda b: max(range(len(b)), key=b.__getitem__))
        dr = _bracket_dirs(ws, scaffold.sclass, binder, lambda b: rng.randrange(len(b)))
        for i in targets:
            pmi_tot += 1
            rnd_tot += 1
            pmi_r += dp.get(i) == "R"             # det/prep first-merged with its right head
            rnd_r += dr.get(i) == "R"
    pmi_rate, rnd_rate = pmi_r / pmi_tot, rnd_r / rnd_tot
    above = pmi_rate > rnd_rate + 0.05
    print(f"\nPROXY (function word first-merges RIGHTWARD, onto its complement):")
    print(f"   PMI parser {pmi_rate:.0%}  vs  random bracketing {rnd_rate:.0%}   "
          f"({pmi_tot:,} det/prep+X bonds)")
    print(f"   ==> {'ABOVE chance' if above else 'AT/BELOW chance'}: the greedy class-PMI "
          f"bracketer nails the EXTREME\n       collocations (see the tightest-bonds table: "
          f"'more than', 'has been', 'blue eyes')\n       but is ~chance on ORDINARY det/prep "
          f"attachment -- a STARTING parser, not a strong\n       one. (The proxy is also crude: "
          f"it lumps right-attaching det/prep with left-\n       attaching auxiliaries. Rigorous "
          f"validation needs a treebank; the downstream use\n       is gated in "
          f"scripts/parse_guided. Head-awareness is the flagged refinement.)")
