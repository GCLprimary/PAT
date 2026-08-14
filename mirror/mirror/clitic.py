"""K-3: the 's clitic (probe 58) — the apostrophe channel's mined
half.

LAW 4 OF PART XV: THE CLITIC OBEYS THE THIRDS. The possessive-'s
remainder splits exactly as the plural's ruler of thirds predicts,
plus the affricate row that has now confirmed itself three times:

    voiced final     -> z        (adam's:  ... m + z)
    voiceless final  -> s        (albright's: ... t + s)
    sibilant final   -> IH z     (ross's: ... s + IH z)
    affricate final  -> AH z     (church's: ... CH + AH z)

Measured on this corpus: z 392 / s 84 / IH-z 19 / AH-z 5 across 500
double-locked pairs (attested >= 2 in the pinned corpus_big).

The clitic enters as a mined suffix family at PAIR-EXACT granularity
(registration is opt-in per gate, provenance `read:clitic`; the
shipped six-suffix gates stay untouched — no-harm is a gate). The
contraction classes stay PAGE-TAUGHT (page_contractions.txt) — twenty
n't types are a lesson, not a mining run. The possessive-vs-is
ambiguity ("the dog's barking") and the plural-possessive s' are
CENSUSED and flagged to the frames lane — never guessed.
"""
from collections import Counter, defaultdict

from .config import ensure_elfix_importable

ensure_elfix_importable()
from elfix.substrate.features import features  # noqa: E402

CLITIC = "'s"
SIBILANTS = frozenset({"s", "z", "SH", "ZH"})
AFFRICATES = frozenset({"CH", "JH"})


def _is_vowel(p):
    return str(getattr(features(p), "kind", "?")) == "vowel"


def _voiced(p):
    return bool(getattr(features(p), "voiced", False)) or _is_vowel(p)


def final_class(phone):
    if phone in SIBILANTS:
        return "sibilant"
    if phone in AFFRICATES:
        return "affricate"
    return "voiced" if _voiced(phone) else "voiceless"


def mine_clitic_pairs(corpus, counts, min_attested=2):
    """Double-locked (stem, word, remainder) triples for the 's
    clitic: orthographic strip + pron prefix + attestation."""
    pairs = []
    for w in corpus:
        if not w.endswith(CLITIC) or len(w) < 4:
            continue
        stem = w[:-2]
        if stem not in corpus or counts[w] < min_attested:
            continue
        wp, sp = tuple(corpus[w]), tuple(corpus[stem])
        if wp[:len(sp)] != sp:
            continue
        pairs.append((stem, w, wp[len(sp):]))
    return pairs


def clitic_table(corpus, pairs):
    """final-class -> modal remainder, with support — the four rows
    of law 4, induced."""
    support = defaultdict(Counter)
    for stem, w, rem in pairs:
        support[final_class(corpus[stem][-1])][tuple(rem)] += 1
    return {cls: c.most_common(1)[0][0] for cls, c in support.items()}, \
        {cls: dict(c) for cls, c in support.items()}


def register_clitic(gate, corpus, pairs):
    """Opt-in registration at pair-exact granularity: the shipped
    gates never widen unless a caller asks."""
    for stem, w, rem in pairs:
        t = tuple(rem)
        gate.attested.setdefault(CLITIC, set()).add(t)
        gate.pair_rems.setdefault(
            (tuple(corpus[stem]), CLITIC), set()).add(t)
        gate.surface_words.setdefault((stem, CLITIC), []).append(w)
    return gate


def apostrophe_census(corpus):
    """The lexicon's apostrophe classes — the channel's population."""
    classes = Counter()
    for w in corpus:
        if "'" not in w:
            continue
        for suf in ("n't", "'ll", "'ve", "'re", "'d", CLITIC, "'m"):
            if w.endswith(suf):
                classes[suf] += 1
                break
        else:
            classes["other"] += 1
    return classes


def frames_lane_census(corpus, counts):
    """The ambiguities this Part refuses to guess (flagged to the
    frames lane): plural-possessive s' types, and the token mass of
    's forms whose reading (possessive vs is-contraction) is
    syntactic, not lexical."""
    s_prime_types = sum(1 for w in corpus
                        if w.endswith("s'") and len(w) > 2)
    ambiguous_mass = sum(counts[w] for w in corpus
                         if w.endswith(CLITIC) and counts[w] > 0)
    return {"plural_possessive_s_prime_types": s_prime_types,
            "possessive_vs_is_token_mass": ambiguous_mass}
