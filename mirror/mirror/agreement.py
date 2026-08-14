"""R-3: the agreement register (probes 37, 37b) — English as the test.

Subject–verb number agreement with attractors (Linzen-style): the
register mechanism from R-2 applied to real sentences. The first DET-N
subject OPENS a number register; the finite verb CLOSES it; consonance
is number match. The attractor case — an opposite-number noun sitting
between subject and verb — is exactly where windowed and recency
machinery gets seduced (recent-noun: 17% under attraction) and a held
register does not (83%).

THE BROKEN RULER, KEPT AS EVIDENCE (probe 37): the first miner labeled
any sentence-initial "DET N" a subject, which mislabels fronted adjuncts
("that day ... the men were") — the register scored 44% and the tell was
recent-noun at 61%: the heuristic was broken, not the mechanism. The
STRICT FRAME (probe 37b) repairs it: sentence-initial DET-N only,
between-material must be a preposition-launched PP chain, and
between-nouns count as attractor candidates only when det/prep-gated.

SUBJECT IDENTIFICATION IS THE FRONTIER, NOT AGREEMENT (law 3 of this
build). The register mechanism is sound; knowing which noun opens it is
where the difficulty lives. This module is a frame, not a parser — it
mines only the sentences it can read with certainty and says so.

Law-4 miner hygiene: the number lexicon drops sg/pl-ambiguous forms, and
test sets exclude derived forms that are themselves known bases (the
'listing' pattern — third member of the instrument-noise family).

F-1 (probe 38): THE WIDENED FRAME — scope frames, don't replace them.
The v2 frame widens coverage bucket by bucket, and every bucket wears
its price as a confidence tier:

  tier 1 · strict (plain)   — sentence-initial DET-N subject, no adjunct,
                              no relative; the regression tier.
  tier 2 · adjunct-led      — leading PP chains skipped to reach the
                              subject; precision reported in a band.
  tier 3 · relative (EXPERIMENTAL) — subject-relative inner clauses
                              closed innermost-first (the RegisterBank
                              discipline applied to clause structure);
                              REPORT-ONLY, asserting it would be
                              pretending.

FRAME REFUSAL is a named taxonomy, not a silent skip: no-det-n-subject,
no-verb-in-window, coordination (the amendment: and/or/nor/but between
subject and verb — a conjoined subject changes the number the register
should hold, so the frame refuses rather than guesses), adjunct-
unparsed, object-relative. Coverage is bought bucket by bucket;
consumers choose tiers by number.
"""
from collections import Counter, defaultdict

SG_VERBS = frozenset({"is", "was", "has", "does"})
PL_VERBS = frozenset({"are", "were", "have", "do"})
DETERMINERS = frozenset({"the", "a", "an", "this", "that", "these",
                         "those", "all", "some", "his", "her", "their",
                         "its", "our", "my"})
PREPOSITIONS = frozenset({"of", "in", "on", "at", "by", "for", "with",
                          "from", "to", "near", "under", "over",
                          "between", "among", "through", "during",
                          "against", "across", "behind", "beside",
                          "without", "within", "upon", "into", "about"})
MAX_SPAN = 12


def build_number_lexicon(pairs):
    """sg = mined -s bases, pl = their derived forms; ambiguous dropped
    (law-4 hygiene: a form living in both sets is instrument noise)."""
    sg, pl = set(), set()
    for base, sfx, w, _ in pairs:
        if sfx == "s":
            sg.add(base)
            pl.add(w)
    ambiguous = sg & pl
    return sg - ambiguous, pl - ambiguous, ambiguous


def number_of(word, sg, pl):
    if word in sg:
        return "sg"
    if word in pl:
        return "pl"
    return None


def mine_strict_cases(sentences, sg, pl, max_span=MAX_SPAN):
    """The strict frame: sentence-initial DET-N subject; the material to
    the verb must be a preposition-launched PP chain; between-nouns are
    attractor candidates only when det/prep-gated."""
    cases = []
    for s in sentences:
        if len(s) < 3 or s[0] not in DETERMINERS:
            continue
        subj_n = number_of(s[1], sg, pl)
        if subj_n is None:
            continue
        subj_i = 1
        for j in range(subj_i + 1, min(subj_i + 1 + max_span, len(s))):
            if s[j] in SG_VERBS or s[j] in PL_VERBS:
                between = s[subj_i + 1:j]
                if between and between[0] not in PREPOSITIONS:
                    break                     # not a PP chain: unreadable
                gated_nouns = []
                for t in range(subj_i + 1, j):
                    n = number_of(s[t], sg, pl)
                    if n and s[t - 1] in (DETERMINERS | PREPOSITIONS):
                        gated_nouns.append((s[t], n))
                gold = "sg" if s[j] in SG_VERBS else "pl"
                attractor = any(n != subj_n for _, n in gated_nouns)
                cases.append({
                    "tokens": s, "subj_i": subj_i, "verb_i": j,
                    "subj_n": subj_n, "gold": gold,
                    "attractor": attractor, "between_nouns": gated_nouns,
                })
                break
    return cases


# ── the three predictors ─────────────────────────────────────────────
def predict_register(case):
    """First DET-N opens the register; it is held to the verb."""
    return case["subj_n"]


def predict_recent_noun(case):
    """The seduction control: the most recent gated noun wins."""
    nouns = case["between_nouns"]
    return nouns[-1][1] if nouns else case["subj_n"]


def train_ngram_counts(sentences):
    bi, tri = defaultdict(Counter), defaultdict(Counter)
    for s in sentences:
        for a, b in zip(s, s[1:]):
            bi[a][b] += 1
        for a, b, c in zip(s, s[1:], s[2:]):
            tri[(a, b)][c] += 1
    return bi, tri


def predict_trigram(case, bi, tri):
    s, j = case["tokens"], case["verb_i"]
    ctx2 = (s[j - 2], s[j - 1]) if j >= 2 else None
    best, best_n = None, -1.0
    for v in SG_VERBS | PL_VERBS:
        c = float(tri[ctx2][v]) if ctx2 in tri else 0.0
        if c == 0 and s[j - 1] in bi:
            c = 0.1 * bi[s[j - 1]][v]
        if c > best_n:
            best_n, best = c, v
    if best is None or best_n <= 0:
        return None
    return "sg" if best in SG_VERBS else "pl"


# ── F-1: the widened frame (probe 38) ────────────────────────────────
# The v2 frame keeps its own token sets (the probe's), separate from the
# strict frame's above: tier-1 must reproduce the strict regression, and
# reproducing the probe's mining requires the probe's lexica.
DET_V2 = frozenset({"the", "a", "an", "this", "that", "these", "those",
                    "his", "her", "their", "its", "our", "my"})
PREP_V2 = frozenset({"of", "in", "on", "at", "with", "for", "to", "from",
                     "by", "over", "under", "near", "during", "after",
                     "before", "through"})
RELATIVIZERS = frozenset({"who", "which", "whose"})
COORDINATORS = frozenset({"and", "or", "nor", "but"})
FRAME_WINDOW = 16

TIER_OF_BUCKET = {"plain": 1, "adjunct": 2, "relative": 3}
REFUSAL_TAXONOMY = ("no-det-n-subject", "no-verb-in-window",
                    "coordination", "adjunct-unparsed", "object-relative")
EXPERIMENTAL_TIERS = (3,)      # report-only; asserting would be pretending


def frame_v2(tokens, sg, pl):
    """The widened frame -> (subj_i, verb_i, bucket) on acceptance, or
    (None, None, refusal_reason) with the reason from REFUSAL_TAXONOMY.

    Adjunct-skip walks leading PP chains to the true subject;
    subject-relative inner clauses are closed innermost-first at their
    verb (the RegisterBank discipline applied to clause structure); the
    coordination amendment refuses conjoined material between subject
    and verb rather than guessing which conjunct rules the register.
    """
    s = tokens
    i = 0
    had_adjunct = False
    while i < len(s) - 2 and s[i] in PREP_V2:
        had_adjunct = True
        i += 1
        if i < len(s) and s[i] in DET_V2:
            i += 1
        hops = 0
        while (i < len(s) and number_of(s[i], sg, pl) is None
               and hops < 2):
            i += 1
            hops += 1
        if i >= len(s) or number_of(s[i], sg, pl) is None:
            return None, None, "adjunct-unparsed"
        i += 1
    if (i >= len(s) - 1 or s[i] not in DET_V2
            or number_of(s[i + 1], sg, pl) is None):
        return None, None, "no-det-n-subject"
    subj_i = i + 1
    j = subj_i + 1
    had_rel = False
    while j < min(subj_i + FRAME_WINDOW, len(s)):
        t = s[j]
        if t in COORDINATORS:
            return None, None, "coordination"
        rel_here = t in RELATIVIZERS or \
            (t == "that" and number_of(s[j - 1], sg, pl) is not None)
        if rel_here:
            had_rel = True
            if j + 1 < len(s):
                nxt = s[j + 1]
                verbish = (nxt in SG_VERBS or nxt in PL_VERBS) or \
                    (number_of(nxt, sg, pl) is not None
                     and t not in DET_V2 and t not in PREP_V2)
                if verbish:
                    j += 2       # close the inner clause at its verb
                    continue
            return None, None, "object-relative"
        if t in SG_VERBS or t in PL_VERBS:
            bucket = ("relative" if had_rel
                      else "adjunct" if had_adjunct else "plain")
            return subj_i, j, bucket
        j += 1
    return None, None, "no-verb-in-window"


def between_nouns_v2(tokens, subj_i, verb_i, sg, pl):
    """Attractor candidates between subject and verb, det/prep-gated
    with the v2 sets."""
    out = []
    for k in range(subj_i + 1, verb_i):
        n = number_of(tokens[k], sg, pl)
        if n and tokens[k - 1] in DET_V2 | PREP_V2:
            out.append((tokens[k], n))
    return out


def mine_v2_cases(sentences, sg, pl):
    """-> (cases, refusals Counter). Every accepted case carries its
    bucket and confidence tier; every refusal carries its taxonomy name.
    """
    cases, refusals = [], Counter()
    for s in sentences:
        subj_i, verb_i, bucket = frame_v2(s, sg, pl)
        if subj_i is None:
            refusals[bucket] += 1
            continue
        subj_n = number_of(s[subj_i], sg, pl)
        gold = "sg" if s[verb_i] in SG_VERBS else "pl"
        nb = between_nouns_v2(s, subj_i, verb_i, sg, pl)
        cases.append({
            "tokens": s, "subj_i": subj_i, "verb_i": verb_i,
            "subj_n": subj_n, "gold": gold,
            "attractor": any(n != subj_n for _, n in nb),
            "between_nouns": nb,
            "bucket": bucket, "tier": TIER_OF_BUCKET[bucket],
        })
    return cases, refusals
