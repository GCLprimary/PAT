"""Tests for the constituent/stack mechanism (elfix/syntax_tree.py): the class-pair PMI
binder, the recursive agglomerative bracketer (SyntaxTree), and the online closure
controller. The binder/parser/controller are unit-tested with a STUB scaffold (a hand-set
class-bigram) so the structure is exact and deterministic, independent of the clustering;
one end-to-end test runs the lever through the real pipeline on a tiny corpus."""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.session import Session
from elfix.syntax_tree import (SyntaxTree, ClassBinder, ConstituentController, Node,
                               RoleTagger, ClauseController)


class StubScaffold:
    """A scaffold stub: a hand-set class-bigram + an identity-ish sclass. Content words
    map to ('cl', w); listed function words to ('fn', w). Lets us drive the binder/parser/
    controller with exact, controlled bindings (no clustering)."""

    def __init__(self, bg, fn=()):
        self.bg = bg
        self._fn = set(fn)

    def sclass(self, w):
        return ("fn", w) if w in self._fn else ("cl", w)


def test_binder_pmi_positive_for_bonds_floor_for_unseen():
    # x,y mutually follow each other (a bond); x->x is never seen (a boundary).
    bg = {("cl", "x"): {("cl", "y"): 100}, ("cl", "y"): {("cl", "x"): 100}}
    b = ClassBinder(StubScaffold(bg))
    assert b.binding(("cl", "x"), ("cl", "y")) > 0          # a seen, above-chance bond
    assert b.binding(("cl", "x"), ("cl", "x")) == b.floor   # unseen -> the floor (boundary)
    assert b.mean_constituent_len() > 1.0                   # earned length is a real span


def test_parser_brackets_tightest_bond_first():
    # 'x y' binds tighter than 'y z' (y->z is diluted: z is also reached from w), so the
    # agglomerative bracketer merges (x y) FIRST -> ((x y) z).
    bg = {("cl", "x"): {("cl", "y"): 100},
          ("cl", "y"): {("cl", "z"): 50},
          ("cl", "w"): {("cl", "z"): 100}}
    t = SyntaxTree(StubScaffold(bg))
    node = t.parse(["x", "y", "z"])
    assert isinstance(node, Node)
    assert str(node) == "((x y) z)"
    assert node.words == ["x", "y", "z"]                    # leaves preserve order
    assert ("x", "y") in set(node.constituents())          # the tight pair is a constituent
    assert str(node).count("(") == str(node).count(")")    # balanced
    assert t.parse([]) is None                             # empty -> no tree


def test_parser_filters_to_vocab():
    bg = {("cl", "x"): {("cl", "y"): 100}}
    t = SyntaxTree(StubScaffold(bg))
    node = t.parse(["x", "OOV", "y"], vocab={"x", "y"})
    assert node.words == ["x", "y"]                         # OOV dropped before parsing


def test_controller_brakes_repeated_head_in_open_constituent():
    # A,B mutually bond -> an A-B-A run stays ONE open constituent; a 2nd B head is braked.
    bg = {("cl", "A"): {("cl", "B"): 100}, ("cl", "B"): {("cl", "A"): 100}}
    c = ConstituentController(SyntaxTree(StubScaffold(bg)))
    for w in ("A", "B", "A"):
        c.observe(w)
    assert c.open == [("cl", "A"), ("cl", "B"), ("cl", "A")]   # all bonds positive -> open grows
    assert c.penalty_signal("B") < 1.0                      # B repeats a head in the phrase -> brake
    assert c.penalty_signal("C") == 1.0                     # a NEW class (C unseen -> closes) is free
    c.reset()
    assert c.open == [] and c.penalty_signal("B") == 1.0    # reset clears the phrase


def test_controller_resets_at_a_boundary():
    # A->A is never seen (a boundary), so observing A,A CLOSES and reopens: open stays short.
    bg = {("cl", "A"): {("cl", "B"): 100}, ("cl", "B"): {("cl", "A"): 100}}
    c = ConstituentController(SyntaxTree(StubScaffold(bg)))
    c.observe("A")
    c.observe("A")                                          # A->A <= chance -> the phrase closed
    assert c.open == [("cl", "A")]                          # only the new word is open
    # function words are never braked (they route by grammar, not constituency)
    cf = ConstituentController(SyntaxTree(StubScaffold(bg, fn=("the",))))
    cf.observe("A"); cf.observe("B"); cf.observe("A")
    assert cf.penalty_signal("the") == 1.0


def _earned_pipeline():
    """A tiny corpus with two distributional groups + function words, earned end to end."""
    utts = ([["x", w] for w in ("aa", "bb", "cc")] * 8
            + [["m", w] for w in ("pp", "qq")] * 8)
    vocab = {"x", "m", "aa", "bb", "cc", "pp", "qq"}
    space = SemanticSpace(utts, vocab, n_anchors=2, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    sc = SyntaxScaffold(space, utts, vocab)
    return utts, vocab, space, sc


def test_parser_runs_on_an_earned_scaffold():
    utts, vocab, space, sc = _earned_pipeline()
    tree = SyntaxTree(sc)
    node = tree.parse(["x", "aa", "m", "pp"], vocab=vocab)
    assert node is not None and set(node.words) <= vocab
    assert str(node).count("(") == str(node).count(")")
    assert tree.binder.mean_constituent_len() >= 1.0


def test_constituency_lever_runs_deterministically():
    utts, vocab, space, sc = _earned_pipeline()
    cmu = {w: [w] for w in vocab}
    s1 = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s1.read("x aa m pp")
    s2 = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s2.read("x aa m pp")
    r1 = [w for w, _, _ in s1.respond(n=6, rng_seed=1, constituency=2.0)]
    r2 = [w for w, _, _ in s2.respond(n=6, rng_seed=1, constituency=2.0)]
    assert r1 and r1 == r2                                  # the lever is deterministic


def test_head_of_uses_the_three_earned_rules():
    bg = {("cl", 1): {("cl", 2): 100}}
    class_verb = {1: 0.9, 2: 0.1}                 # class 1 verb-ish, class 2 noun-ish
    b = ClassBinder(StubScaffold(bg), class_verb=class_verb)
    # rule 1: content heads over a functor (either side)
    assert b.head_of(("fn", "the"), ("cl", 2)) == ("cl", 2)
    assert b.head_of(("cl", 2), ("fn", "of")) == ("cl", 2)
    # rule 2: the predicate-classed child heads (categorial), whichever side it is on
    assert b.head_of(("cl", 1), ("cl", 2)) == ("cl", 1)
    assert b.head_of(("cl", 2), ("cl", 1)) == ("cl", 1)
    # rule 3: otherwise RIGHT-headed (earned 90% on nominal compounds) — including when
    # a class is unscored (absent evidence never counts as predicate, Law 2)
    b2 = ClassBinder(StubScaffold(bg), class_verb={2: 0.1})    # class 1 unscored
    assert b2.head_of(("cl", 1), ("cl", 2)) == ("cl", 2)
    assert b2.head_of(("cl", 2), ("cl", 1)) == ("cl", 1)
    b3 = ClassBinder(StubScaffold(bg))                          # no roles at all
    assert b3.head_of(("cl", 1), ("cl", 2)) == ("cl", 2)


def test_parse_annotates_categorial_heads_and_head_word():
    # 'the'(fn) + dog(cl 1, noun) + barks(cl 2, verb): (the dog) heads 'dog' (rule 1),
    # the root heads 'barks' (rule 2: the predicate class heads).
    class _Sc:
        bg = {("fn", "the"): {("cl", 1): 100}, ("cl", 1): {("cl", 2): 50},
              ("cl", 9): {("cl", 2): 100}}
        def sclass(self, w):
            return {"the": ("fn", "the"), "dog": ("cl", 1), "barks": ("cl", 2)}[w]
    t = SyntaxTree(_Sc(), class_verb={1: 0.1, 2: 0.9})
    node = t.parse(["the", "dog", "barks"])
    assert str(node) == "((the dog) barks)"
    assert node.left.head == ("cl", 1)             # (the dog) is a DOG-kind of thing
    assert node.left.head_word() == "dog"
    assert node.head == ("cl", 2)                  # the sentence is a BARKS-kind of thing
    assert node.head_word() == "barks"


def test_role_tagger_class_scores_aggregate_by_frequency():
    roles = _role_bigram()

    class _Space:                                  # minimal space stub: two classes
        class_words = {0: ["dog", "cat"], 1: ["ran", "ate"], 2: ["zzz"]}

    uni = Counter({"dog": 10, "cat": 5, "ran": 8, "ate": 2})
    cs = roles.class_scores(_Space(), uni)
    assert cs[0] < 0.5 < cs[1]                     # noun class low, verb class high
    assert 2 not in cs                             # no scored member -> absent (Law 2)


def _role_bigram():
    """A tiny word-bigram where 'the' (determiner) precedes nouns and 'he' (pronoun)
    precedes verbs — the functor-context signal the RoleTagger earns from."""
    bigram = {"the": Counter({"dog": 30, "cat": 30}),
              "he": Counter({"ran": 30, "ate": 30})}
    skeleton = {"the", "he"}
    return RoleTagger(bigram, skeleton, det_anchor="the")


def test_role_tagger_separates_verbs_from_nouns_by_functor_context():
    roles = _role_bigram()
    # 'the' is a NOMINAL functor (precedes nouns), 'he' a VERBAL one (precedes verbs)
    assert roles.nominal_ness["the"] > roles.nominal_ness["he"]
    # nouns (follow the determiner) score low; verbs (follow the pronoun) score high
    assert roles.is_predicate("ran") and roles.is_predicate("ate")
    assert not roles.is_predicate("dog") and not roles.is_predicate("cat")
    assert roles.score("ran") > roles.score("dog")
    assert roles.score("the") is None        # a functor has no verb_score (absent, Law 2)
    assert roles.score("never_seen") is None  # too-rare / unseen -> absent, not forced


def test_clause_controller_brakes_arguments_while_a_verb_is_owed():
    roles = _role_bigram()
    c = ClauseController(roles, brake=0.3)
    c.observe("dog")                          # a subject (argument) is now open
    assert c.penalty_signal("cat") < 1.0      # another argument while a verb is OWED -> brake
    assert c.penalty_signal("ran") == 1.0     # the owed predicate passes free
    c.observe("ran")                          # the clause now has its verb
    assert c.penalty_signal("cat") == 1.0     # arguments (objects) are free again
    c.reset()
    assert c.penalty_signal("cat") == 1.0     # fresh clause, no subject open yet


def test_clause_controller_runs_as_an_injected_controller():
    utts, vocab, space, sc = _earned_pipeline()
    cmu = {w: [w] for w in vocab}
    p = Predictor(utts, vocab)
    roles = RoleTagger(p.bigram, space.skeleton, det_anchor=next(iter(space.skeleton), "x"))
    s = Session(p, cmu, space=space, scaffold=sc); s.read("x aa m pp")
    out = [w for w, _, _ in s.respond(n=6, rng_seed=1, constituency=2.0,
                                      controller=ClauseController(roles))]
    assert out and all(isinstance(w, str) for w in out)


def test_injected_noop_controller_is_a_passthrough():
    # respond accepts any reset/observe/penalty_signal object; a no-op one must not change
    # the output vs the lever being off (the injection path the gate uses for its control).
    utts, vocab, space, sc = _earned_pipeline()
    cmu = {w: [w] for w in vocab}

    class _NoOp:
        def reset(self): pass
        def observe(self, w): pass
        def penalty_signal(self, w): return 1.0

    s = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s.read("x aa m pp")
    off = [w for w, _, _ in s.respond(n=6, rng_seed=1, constituency=0.0)]
    s2 = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s2.read("x aa m pp")
    noop = [w for w, _, _ in s2.respond(n=6, rng_seed=1, constituency=2.0, controller=_NoOp())]
    assert off == noop
