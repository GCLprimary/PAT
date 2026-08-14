"""Tests for the generative floor (elfix/predict.py): counted next-word prediction
with confidence + provenance, deterministic seeded generation, the semantic-locator
ordering (certain vs uncertain contexts), and the PHONOLOGICAL backoff mechanism
(sound-class pooling generalises across class-mates; off by default)."""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from elfix.predict import (Predictor, PhonoBackoff, CarryCache, AcquiredContext,
                           FactoredBase, route_key, make_key_of, MIN_CONTEXT, ACQUIRE_CONFIRM)
from elfix.semantic import SemanticSpace, SyntaxScaffold


def _factored_setup():
    utts = ([["x", w] for w in ("aa", "bb", "cc")] * 8
            + [["m", w] for w in ("pp", "qq")] * 8)
    vocab = {"x", "m", "aa", "bb", "cc", "pp", "qq"}
    p = Predictor(utts, vocab)
    space = SemanticSpace(utts, vocab, n_anchors=2, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    sc = SyntaxScaffold(space, utts, vocab)
    return p, space, sc, vocab


def test_factored_base_is_a_proper_distribution_and_opt_in():
    p, space, sc, vocab = _factored_setup()
    before = p.prob("x", "aa")
    assert p.factored is None                          # OFF by default (bare behaviour intact)
    _, _, lvl0 = p.predict("x")
    assert "factored" not in lvl0
    p.attach_factored(space, sc)
    assert isinstance(p.factored, FactoredBase)
    # the factored base is a proper distribution over the vocabulary
    assert abs(sum(p.factored.prob("x", w) for w in vocab) - 1.0) < 1e-9
    # attaching changes the scored prob and tags the provenance level
    assert p.prob("x", "aa") != before
    assert "+factored" in p.predict("x")[2]


def test_factored_gives_nonzero_within_class_mass_to_unseen_classmates():
    # the generalization MECHANISM: a class-mate the context never produced still gets
    # strictly-positive within-class mass (add-one folded in the class-unigram share), and
    # the factored prob factorizes exactly as P(class|class) x P(word|class,prev).
    p, space, sc, vocab = _factored_setup()
    p.attach_factored(space, sc)
    fac = p.factored
    # find a class with >= 2 members and a member 'w' with zero bigram count after 'x'
    cid = next(c for c, mem in space.class_words.items()
               if len([m for m in mem if m in vocab]) >= 2)
    mem = [m for m in space.class_words[cid] if m in vocab]
    w = next((m for m in mem if p.bigram.get("x", Counter()).get(m, 0) == 0), None)
    if w is not None:
        assert fac.p_within("x", w) > 0.0                     # unseen-in-context -> still positive
        assert abs(fac.prob("x", w) - sc.trans("x", w) * fac.p_within("x", w)) < 1e-12


def test_predict_confident_context_and_backoff():
    utts = [["a", "b"]] * 10 + [["c", "d"], ["c", "e"]]
    p = Predictor(utts, {"a", "b", "c", "d", "e"})
    ranked, h, level = p.predict("a")
    assert level == "lexical" and ranked[0][0] == "b" and h < 0.01   # a->b always
    assert p.predict("zzz")[2] == "backoff"                          # unseen -> backoff


def test_generation_is_deterministic_and_inspectable():
    p = Predictor([["a", "b", "c", "a", "b", "c"]] * 5, {"a", "b", "c"})
    g1 = p.generate("a", n=4, rng_seed=1)
    g2 = p.generate("a", n=4, rng_seed=1)
    assert g1 == g2                                # deterministic given the seed
    assert g1[0] == ("a", 0.0, "seed") and len(g1) == 5
    for word, entropy, level in g1[1:]:           # every step carries its evidence
        base = level.split("+")[0]                # carry-conditioned by default
        assert isinstance(word, str) and entropy >= 0.0 and base in ("lexical", "backoff")


def test_semantic_locator_orders_certain_before_uncertain():
    utts = [["a", "b"]] * 60 + [["x", str(i)] for i in range(60)]
    vocab = {"a", "b", "x"} | {str(i) for i in range(60)}
    cu = Predictor(utts, vocab).context_uncertainty(min_count=50)
    names = [c[0] for c in cu]
    assert names.index("a") < names.index("x")     # 'a'->b certain; 'x'->many uncertain


# ── the phonological backoff (sound-class smoothing) ──────────────────────────
def _soundclass(p, vocab, key_of=lambda w: w[-1]):
    """Attach a PhonoBackoff whose class key is a stand-in for sound (here the last
    character); the mechanism is identical to the router-keyed version."""
    p.phono = PhonoBackoff(p.bigram, vocab, key_of)
    return p


def test_phono_off_by_default_leaves_backoff_chain_unchanged():
    # without an attached phono backoff, predict() is exactly lexical -> unigram.
    p = Predictor([["a", "b"]] * 10 + [["c", "d"]], {"a", "b", "c", "d"})
    assert p.phono is None
    assert p.predict("zzz")[2] == "backoff"            # unseen -> unigram
    assert p.predict("c")[2] == "backoff"              # sparse, no phono tier -> unigram


def test_phono_backoff_generalises_across_soundclass():
    # 'cats' & 'dogs' (class 's') are reliably followed by 'ran'; 'rats' is sparse
    # (seen once) -> it should inherit its sound-class-mates' continuation.
    utts = [["cats", "ran"]] * 6 + [["dogs", "ran"]] * 6 + [["rats", "slept"]]
    vocab = {"cats", "dogs", "rats", "ran", "slept"}
    p = _soundclass(Predictor(utts, vocab), vocab)
    ranked, _, level = p.predict("rats")
    assert level == "phono"                             # sparse context -> phono tier
    assert ranked[0][0] == "ran"                        # generalised from sound-class
    cont = p.phono.continuation("rats")                 # the pooled class continuation
    assert cont["ran"] == 12 and cont["slept"] == 1     # cats+dogs+rats, by sound-class
    assert p.predict("cats")[2] == "lexical"            # dense context still lexical


def test_phono_continuation_absent_when_class_pool_too_thin():
    # a class whose pooled continuation is below min_mass returns None (absence !=
    # a confident zero) -> prediction falls through to the unigram.
    utts = [["zz", "q"]]                                # 'zz' seen once; class 'z' thin
    vocab = {"zz", "q"}
    p = _soundclass(Predictor(utts, vocab), vocab)
    assert p.phono.continuation("zz") is None
    assert p.predict("zz")[2] == "backoff"


def test_route_key_modes_and_missing():
    from elfix.routing.shape_routing import ShapeRouter
    from elfix.trajectory.trajectory import Trajectory
    words = {"cats": ["k", "AE", "t", "s"], "bats": ["b", "AE", "t", "s"],
             "running": ["r", "AH", "n", "IH", "NG"]}
    router = ShapeRouter([Trajectory.of(p) for p in words.values()], min_count=1)
    kf = route_key(router, words["cats"], "final")     # final arc -> one class id
    kr = route_key(router, words["cats"], "route")     # whole word -> a tuple of ids
    assert isinstance(kf, int) and isinstance(kr, tuple) and kr[-1] == kf
    assert route_key(router, [], "final") is None      # no routable arc -> no class
    key_of = make_key_of(router, words, "final")
    assert key_of("cats") == kf and key_of("not_a_word") is None
    assert key_of.mode == "final"


def test_locator_reports_unigram_and_soundclass_entropy():
    utts = [["cats", "ran"]] * 6 + [["dogs", "ran"]] * 6 + [["rats", "slept"]]
    vocab = {"cats", "dogs", "rats", "ran", "slept"}
    p = _soundclass(Predictor(utts, vocab), vocab)
    rows = {r[0]: r for r in p.locator()}              # sparse contexts only
    assert "rats" in rows and "cats" not in rows       # cats is dense (n>=MIN_CONTEXT)
    _, n, h_uni, h_phono = rows["rats"]
    assert n == 1 and h_uni >= 0.0 and h_phono is not None
    with pytest.raises(ValueError):                    # needs an attached phono backoff
        Predictor(utts, vocab).locator()


# ── carry-conditioned prediction (the decaying word-cache, Tier-5 over identity) ──
def test_carry_cache_decays_recents_and_resets():
    c = CarryCache(rate=0.5)
    c.observe("a"); c.observe("b")                     # a decays, b is fresh
    assert c.prob("b") > c.prob("a")                   # recent word dominates
    assert abs(c.prob("a") + c.prob("b") - 1.0) < 1e-9
    c.observe("a")                                     # a refreshed above the faded b
    assert c.prob("a") > c.prob("b")
    c.reset()
    assert c.total == 0.0 and c.prob("a") == 0.0       # hard discontinuity clears it


def test_carry_cache_reranks_prediction_toward_recent_context():
    # base: 'a' -> 'x' and 'y' equally likely. A cache that just saw 'y' should tip it.
    p = Predictor([["a", "x"]] * 5 + [["a", "y"]] * 5, {"a", "x", "y"})
    r0, _, lv0 = p.predict("a")                         # no cache: x and y tie
    assert lv0 == "lexical" and abs(dict((w, pr) for w, pr, _ in r0)["x"]
                                    - dict((w, pr) for w, pr, _ in r0)["y"]) < 1e-9
    cache = CarryCache(rate=0.9); cache.observe("y")
    r1, _, lv1 = p.predict("a", cache=cache, beta=0.5)
    pr = {w: p_ for w, p_, _ in r1}
    assert "carry" in lv1 and pr["y"] > pr["x"]         # recency prior broke the tie


def test_carry_generation_default_off_optin_fires_and_is_deterministic():
    p = Predictor([["a", "b", "c", "a", "b", "c"]] * 5, {"a", "b", "c"})
    g1 = p.generate("a", n=4, rng_seed=1)              # default: carry OFF (free-run)
    g2 = p.generate("a", n=4, rng_seed=1)
    assert g1 == g2 and g1[0] == ("a", 0.0, "seed")
    assert all("carry" not in lv for _, _, lv in g1[1:])   # off by default in free gen
    on = p.generate("a", n=4, rng_seed=1, use_carry=True)
    assert on == p.generate("a", n=4, rng_seed=1, use_carry=True)   # deterministic
    assert any("carry" in lv for _, _, lv in on[1:])       # opt-in fires the cache


# ── training through input (AcquiredContext: the distributional InferredStore) ──
def test_ingest_learns_a_sparse_context_from_input():
    # 'q' is unseen in train; reading input where 'q -> z' (>=MIN times) teaches it.
    p = Predictor([["a", "b"]] * 6, {"a", "b", "q", "z"})
    assert p.predict("q")[2] == "backoff"              # nothing known about 'q'
    for _ in range(MIN_CONTEXT + 1):
        p.ingest(["q", "z"], source="input")
    ranked, _, level = p.predict("q")
    assert level == "acquired" and ranked[0][0] == "z"  # learned from input
    assert p.transition_evidence("q", "z") == "acquired:confirmed"


def test_ingest_never_overwrites_the_attested_store():
    base = Predictor([["a", "b", "a", "b"]] * 3, {"a", "b", "c", "d"})
    import copy
    frozen = copy.deepcopy(base.bigram), copy.deepcopy(base.unigram)
    for _ in range(10):
        base.ingest(["c", "d"], source="input")
    assert base.bigram == frozen[0] and base.unigram == frozen[1]   # Law 3: separate store
    assert base.acquired.seen_ext == 10                              # learning is held apart


def test_self_generated_input_is_quarantined():
    p = Predictor([["a", "b"]] * 6, {"a", "b", "q", "z"})
    before = p.prob("q", "z")
    for _ in range(50):                                # flood it with self-generated text
        p.ingest(["q", "z"], source="self")
    assert p.prob("q", "z") == before                  # inert: never predicted from
    assert p.predict("q")[2] == "backoff"              # still no real evidence
    assert p.transition_evidence("q", "z") == "acquired:malleable"  # recorded, not trusted
    # but EXTERNAL corroboration of the same transition does train:
    for _ in range(ACQUIRE_CONFIRM):
        p.ingest(["q", "z"], source="input")
    assert p.transition_evidence("q", "z") == "acquired:confirmed"


def test_acquired_context_ternary_evidence():
    a = AcquiredContext()
    assert a.state("x", "y") == "absent"               # absence != zero (Law 2)
    a.ingest_utterance(["x", "y"], "input")
    assert a.state("x", "y") == "malleable"            # seen once
    a.ingest_utterance(["x", "y"], "input")
    assert a.state("x", "y") == "confirmed"            # corroborated (>= ACQUIRE_CONFIRM)
    a.ingest_utterance(["x", "w"], "self")
    assert a.state("x", "w") == "malleable"            # self-gen is recorded ...
    assert a.continuation("x").get("w", 0) == 0        # ... but quarantined from prediction
