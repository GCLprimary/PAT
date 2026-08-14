"""Tests for the semantic layer (elfix/semantic.py): distributional classes earned by
counted co-occurrence clustering, the SemanticCarry topical prior, and its wiring into
prediction and the session. Uses tiny data with two cleanly-separated distributional
groups so the clustering is deterministic."""
import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SemanticCarry, SyntaxScaffold
from elfix.session import Session


def _two_class():
    """A corpus with two distributional groups: {aa,bb,cc} always sit in 'x _ y',
    {pp,qq,rr} always in 'm _ n'. Same frame -> same class; the two differ."""
    utts = []
    for _ in range(10):
        for w in ("aa", "bb", "cc"):
            utts.append(["x", w, "y"])
        for w in ("pp", "qq", "rr"):
            utts.append(["m", w, "n"])
    vocab = {"x", "y", "m", "n", "aa", "bb", "cc", "pp", "qq", "rr"}
    space = SemanticSpace(utts, vocab, n_anchors=4, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    return space, utts, vocab


def test_semantic_space_clusters_distributional_groups():
    space, _, _ = _two_class()
    assert space.class_of("aa") == space.class_of("bb") == space.class_of("cc")
    assert space.class_of("pp") == space.class_of("qq") == space.class_of("rr")
    assert space.class_of("aa") != space.class_of("pp")   # the two frames separate
    assert space.class_of("never_seen") is None           # absence != zero (Law 2)


def test_semantic_carry_primes_class_members_and_decays():
    space, utts, vocab = _two_class()
    uni = Counter(w for u in utts for w in u)
    sc = SemanticCarry(space, uni, rate=0.5)
    sc.observe("aa")                                       # activate aa's class (topic)
    assert sc.prob("bb") > 0                               # bb primed though never seen
    assert sc.prob("pp") == 0.0                            # the other topic is cold
    for _ in range(8):
        sc.observe("pp")                                   # shift the topic
    assert sc.prob("pp") > sc.prob("bb")                   # old topic faded
    sc.reset()
    assert sc.total == 0.0 and sc.prob("bb") == 0.0


def test_predict_topic_prior_surfaces_on_topic_word():
    space, utts, vocab = _two_class()
    p = Predictor(utts, vocab)
    sc = SemanticCarry(space, p.unigram, rate=0.9)
    sc.observe("aa")                                       # topic = {aa,bb,cc}
    ranked, _, level = p.predict("zzz", k=8, sem_cache=sc, sem_beta=0.6)
    words = [w for w, _, _ in ranked]
    assert "+topic" in level                               # the topic prior fired
    assert "bb" in words or "cc" in words                  # on-topic words surfaced


def test_syntax_scaffold_learns_grammatical_class_transitions():
    # 'x' is always followed by an {aa,bb,cc} word; 'm' by a {pp,qq} word. The scaffold
    # should make the SEEN class-transition far more likely than the unseen one.
    utts = ([["x", w] for w in ("aa", "bb", "cc")] * 8
            + [["m", w] for w in ("pp", "qq")] * 8)
    vocab = {"x", "m", "aa", "bb", "cc", "pp", "qq"}
    space = SemanticSpace(utts, vocab, n_anchors=2, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    sc = SyntaxScaffold(space, utts, vocab)
    assert sc.sclass("x")[0] == "fn"                  # x/m are function-class (anchors)
    assert sc.sclass("aa")[0] == "cl"                 # content words get a content class
    # the grammatical transition x->{aa-class} beats the never-seen x->{pp-class}
    assert sc.trans("x", "aa") > sc.trans("x", "pp")
    assert sc.trans("m", "pp") > sc.trans("m", "aa")
    # the grammar lever runs end-to-end with a scaffold, deterministically
    cmu = {w: [w] for w in vocab}
    s1 = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s1.read("x aa m pp")
    s2 = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc); s2.read("x aa m pp")
    w1 = [w for w, _, _ in s1.respond(n=6, rng_seed=1, grammar=2.0)]
    assert w1 and w1 == [w for w, _, _ in s2.respond(n=6, rng_seed=1, grammar=2.0)]


def test_sentence_arc_position_and_boundary_signals():
    utts = [["x", w, "y", "z"] for w in ("aa", "bb", "cc")] * 10
    vocab = {"x", "y", "z", "aa", "bb", "cc"}
    space = SemanticSpace(utts, vocab, n_anchors=3, window=1, min_count=2,
                          n_cluster_words=4, k=2, iters=20, seed=0)
    sc = SyntaxScaffold(space, utts, vocab)
    assert sc.mean_len > 0                                  # length model learned
    # 'x' is always sentence-initial (pos 0), 'z' always last (pos 1)
    assert sc.meanpos[sc.sclass("x")] < sc.meanpos[sc.sclass("z")]
    assert sc.end_prob("z", 4) > sc.end_prob("x", 4)       # sentences end after 'z', not 'x'
    # pos_fit: 'x' fits the start better than the end
    assert sc.pos_fit("x", 0.0) > sc.pos_fit("x", 1.0)
    # the boundary lever inserts '.' tokens and bounds the output
    cmu = {w: [w] for w in vocab}
    s = Session(Predictor(utts, vocab), cmu, space=space, scaffold=sc)
    s.read("x aa y z")
    out = [w for w, _, _ in s.respond(n=20, rng_seed=1, boundaries=True, position_bias=1.0)]
    assert "." in out                                      # at least one sentence boundary


def test_session_is_topic_aware_when_a_space_is_attached():
    space, utts, vocab = _two_class()
    p = Predictor(utts, vocab)
    cmu = {w: [w] for w in vocab}                          # trivial pronunciations
    s = Session(p, cmu, space=space)
    s.read("x aa y x bb y")                                # read the {aa,bb,cc} topic
    assert s.topics()                                      # a topic is named
    assert s.sem_carry.prob("cc") > 0                      # cc primed by its class-mates
    reply = s.respond(n=5, rng_seed=1)
    assert reply and all(isinstance(w, str) for w, _, _ in reply)
