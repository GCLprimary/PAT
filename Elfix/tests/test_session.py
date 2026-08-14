"""Tests for the input/output wrap (elfix/session.py): a read<->respond loop that
tags + learns from input, responds carry-conditioned over real context, governs the
read/write asymmetry (read trains, self-reply is quarantined), and localises meaning."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from elfix.predict import Predictor
from elfix.session import Session


def _session():
    cmu = {"the": ["DH", "AH"], "cat": ["k", "AE", "t"],
           "dog": ["d", "AO", "g"], "sat": ["s", "AE", "t"]}
    p = Predictor([["the", "cat"], ["the", "dog"]] * 5, set(cmu))
    return Session(p, cmu), p, cmu


def test_read_tags_learns_and_remembers():
    s, p, _ = _session()
    r = s.read("the cat zzz")                       # zzz is oov (not in cmu)
    assert {t.word: t.tag for t in r.tokens} == {
        "the": "attested", "cat": "attested", "zzz": "oov"}
    assert "zzz" in s.history                        # oov is still remembered
    assert p.acquired.ext["the"]["cat"] >= 1         # learned the->cat from INPUT
    assert s.carry.prob("cat") > 0                   # working memory updated (in-vocab)


def test_read_surprisal_only_between_invocab_words():
    s, _, _ = _session()
    su = {t.word: t.surprisal for t in s.read("the cat").tokens}
    assert su["the"] is None                         # cold start: no prev
    assert su["cat"] is not None and su["cat"] >= 0.0  # -log2 P(cat | the)


def test_respond_deterministic_no_adjacent_repeat_and_quarantined():
    s, p, _ = _session()
    s.read("the cat the dog the cat")
    ext_before = p.acquired.seen_ext
    r1 = s.respond(n=6, rng_seed=3)
    s2, _, _ = _session()
    s2.read("the cat the dog the cat")
    r2 = s2.respond(n=6, rng_seed=3)
    words = [w for w, _, _ in r1]
    assert words == [w for w, _, _ in r2]            # deterministic given the seed
    assert all(a != b for a, b in zip(words, words[1:]))   # no adjacent repeat
    # the read/write asymmetry: reading trained (ext > 0); responding did NOT (self)
    assert p.acquired.seen_ext == ext_before         # self-reply never trains
    assert p.acquired.seen_gen > 0                    # but is recorded (quarantined)


def test_locator_ranks_most_surprising_first():
    s, _, _ = _session()
    s.read("the cat the cat the cat the dog sat")
    loc = s.locator()
    assert loc == sorted(loc, key=lambda x: -x[1])   # most surprising first
    assert all(isinstance(w, str) and h >= 0.0 for w, h in loc)


def test_session_grows_and_uses_a_new_word_from_its_shape():
    # closing the loop: a word never seen is PRONOUNCED from its shape (walk+ing),
    # added to the vocab, and then participates via CONTEXT (the acquired store).
    from elfix.lexicon.inferred_store import InferredStore
    cmu = {"walk": ["w", "AO", "k"], "home": ["h", "OW", "m"],
           "she": ["SH", "IY"], "was": ["w", "AH", "z"]}
    p = Predictor([["she", "was", "home"]] * 5, set(cmu))
    s = Session(p, cmu, store=InferredStore(cmu))
    assert "walking" not in p.vocab                  # genuinely new
    r = s.read("she was walking home")
    assert r.grown == 1                              # pronounced one new word
    assert {t.word: t.tag for t in r.tokens}["walking"] == "inferred"
    assert "walking" in p.vocab                      # now a predictable citizen
    assert p.acquired.ext["walking"]["home"] >= 1    # placed by CONTEXT (walking->home)


def test_oov_stays_oov_without_a_store():
    s, p, _ = _session()                             # no store attached
    r = s.read("the cat zzqx")                       # zzqx can't decompose
    assert r.grown == 0
    assert {t.word: t.tag for t in r.tokens}["zzqx"] == "oov"
    assert "zzqx" not in p.vocab


def test_locator_typed_tags_surprises_with_their_class():
    from elfix.semantic import SemanticSpace
    utts = ([["x", w, "y"] for w in ("aa", "bb", "cc")] * 8
            + [["m", w, "n"] for w in ("pp", "qq")] * 8)
    cmu = {w: [w] for w in ("x", "y", "m", "n", "aa", "bb", "cc", "pp", "qq")}
    space = SemanticSpace(utts, set(cmu), n_anchors=4, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    s = Session(Predictor(utts, set(cmu)), cmu, space=space)
    s.read("x aa y m pp n x bb y")
    typed = s.locator_typed()
    assert typed == sorted(typed, key=lambda x: -x[1])         # still surprise-ranked
    classed = [(w, t) for w, _, t, _ in typed if t is not None]
    assert classed                                              # content words got a type
    assert all(t.startswith("{") for _, t in classed)          # readable anchor-frame
    # the POS role is earned (predicate/argument) or absent — never anything else
    assert all(r in (None, "predicate", "argument") for _, _, _, r in typed)
    # without a space, the typed locator has neither class nor role (no crash)
    s2, _, _ = _session()
    s2.read("the cat the dog")
    assert all(t is None and r is None for _, _, t, r in s2.locator_typed())


def test_respond_generation_levers_run_and_stay_deterministic():
    # the above-the-floor levers (adaptive topic, no-repeat, function-word penalty)
    # accept params, run with a space, and stay deterministic given the seed.
    from elfix.semantic import SemanticSpace
    utts = ([["x", w, "y"] for w in ("aa", "bb", "cc")] * 8
            + [["m", w, "n"] for w in ("pp", "qq")] * 8)
    cmu = {w: [w] for w in ("x", "y", "m", "n", "aa", "bb", "cc", "pp", "qq")}
    space = SemanticSpace(utts, set(cmu), n_anchors=4, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    kw = dict(n=6, rng_seed=2, sem_adapt=(0.6, 9.0), no_repeat=3, fn_penalty=0.25)
    s1 = Session(Predictor(utts, set(cmu)), cmu, space=space); s1.read("x aa y m pp n")
    s2 = Session(Predictor(utts, set(cmu)), cmu, space=space); s2.read("x aa y m pp n")
    w1 = [w for w, _, _ in s1.respond(**kw)]
    w2 = [w for w, _, _ in s2.respond(**kw)]
    assert w1 == w2                                       # deterministic given the seed
    assert all(a != b for a, b in zip(w1, w1[1:]))        # no adjacent repeat


def test_grown_oov_is_replaced_by_context_after_enough_reads():
    # two distributional frames: {run,aa,bb} sit in 'x _ y'; {pp,qq} in 'm _ n'.
    # 'running' (run+ing) cold-starts to run's class, but is READ in the m _ n frame,
    # so after REPLACE_AT reads its context should move it to the OTHER class.
    from elfix.semantic import SemanticSpace
    from elfix.lexicon.inferred_store import InferredStore
    utts = ([["x", w, "y"] for w in ("run", "aa", "bb")] * 8
            + [["m", w, "n"] for w in ("pp", "qq")] * 8)
    cmu = {w: [w] for w in ("x", "y", "m", "n", "run", "aa", "bb", "pp", "qq")}
    space = SemanticSpace(utts, set(cmu), n_anchors=4, window=1, min_count=2,
                          n_cluster_words=6, k=2, iters=20, seed=0)
    p = Predictor(utts, set(cmu))
    s = Session(p, cmu, store=InferredStore(cmu), space=space)
    s.read("m running n")                            # grow -> cold-start = run's class
    cold = space.class_of("running")
    assert cold == space.class_of("run")             # cold-start inherits the stem
    s.read("m running n")                            # 2nd read -> re-place by m/n context
    assert s.replaced >= 1
    assert space.class_of("running") == space.class_of("pp")   # now the m/n frame class
    assert space.class_of("running") != cold
