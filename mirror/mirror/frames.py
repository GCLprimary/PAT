"""D-1: the depth-2 resolver (probe 54) — the clause organ, minimal
and exact.

  SUBJECT       an NP (det/quant [adj] noun | name | pronoun) whose
                next token is verbish — a subject is an NP that
                LAUNCHES A PREDICATION.
  RELATIVE MASK 'that/who/which' whose preceding token ends a noun NP:
                the span through the relative's verb (+ optional
                object NP) is bracketed out; the head noun keeps the
                floor.
  ANTECEDENT    the RELATIVIZER-HEAD OVERRIDE first — an NP ending
                exactly at that/who/which left of the reflexive IS the
                matrix antecedent (what c_command-shaped sentences
                test; serves the domain family's relative-headed
                variants) — else WALK LEFT from the reflexive through
                the verb cluster to the nearest NP-tail whose noun is
                det/of/noun-preceded, or a listed or capitalized name
                (CASE IS PRESERVED into this resolver — the spec's
                amendment over the delivered probe, which lowercased
                first and starved the name signal), or a subject
                pronoun; ABSTAIN when unresolvable.
  phi-CHECK     number always (lexicon + pages); gender when known
                (names page + pronouns); himself/herself against a
                gender-unknown subject ABSTAINS — never guessed.

LAW 2: THE VERB INVENTORY IS AN ARTIFACT. Verbish-ness consults a
checksummed list exported from the mined pairs (bases taking -ed or
-ing, their -s forms, the derived forms themselves) plus the
irregular-pasts page — never a hand list. The session's noun-verb
ambiguity failures (upset, sounds — mined as nouns) are the
justification: the artifact list settles what the armchair argued
about. `verb_inventory()` builds it; its sha256 is pinned in
fixtures/verb_inventory.json and asserted by test.

NP machinery: last-noun-of-run heads; OF-PASSTHROUGH PARTITIVES
("a lot of patients" -> patients, pl); capitalization as the name
signal. The four session canaries ride the tests: partitives resolve
plural, upset/sounds resolve as predications, a relative-headed
subject is found despite the relativizer blocking its next-token, and
the clause-boundary mislabel family (F3) is recorded — reduced
relatives specifically unobserved in BLiMP.
"""
import re

REFLEXIVES = {"himself": ("m", "sg"), "herself": ("f", "sg"),
              "itself": ("n", "sg"), "themselves": (None, "pl")}
SUBJ_PRONOUNS = {"he": ("m", "sg"), "she": ("f", "sg"),
                 "it": ("n", "sg"), "they": (None, "pl"),
                 "i": (None, "sg"), "we": (None, "pl"),
                 "you": (None, None)}
DETS = frozenset({"the", "a", "an", "this", "that", "these", "those",
                  "some", "every", "each", "all", "most", "many",
                  "his", "her", "its", "their", "any", "no", "one",
                  "two", "three", "several", "few", "both"})
AUX_SG = frozenset({"is", "isn't", "was", "wasn't", "has", "hasn't",
                    "does", "doesn't"})
AUX_PL = frozenset({"are", "aren't", "were", "weren't", "have",
                    "haven't", "do", "don't"})
MODALS = frozenset({"can", "could", "will", "would", "may", "might",
                    "must", "should", "can't", "won't", "wouldn't",
                    "couldn't"})
NEGATIONS = frozenset({"didn't", "doesn't", "don't", "not", "n't",
                       "won't", "can't", "wasn't", "isn't", "aren't",
                       "weren't", "couldn't", "wouldn't"})
STOPWORDS = frozenset({"that", "who", "which", "and", "or", "but",
                       "of", "in", "on", "at", "to", "from", "with",
                       "about", "for", "by", "not"})
RELATIVIZERS = ("that", "who", "which")
_PUNCT = re.compile(r"[.,!?;:]+$|^[.,!?;:]+")


def case_tokens(sentence):
    """Tokenize CASE-PRESERVED with punctuation stripped — the name
    signal must survive into the resolver."""
    out = []
    for w in sentence.split():
        w = _PUNCT.sub("", w)
        if w:
            out.append(w)
    return out


def verb_inventory(transform, past_page=None):
    """LAW 2's artifact: verbs = mined bases taking -ed or -ing, their
    -s forms, the derived -ed/-ing/-s forms themselves, plus the
    irregular-pasts page's forms. Deterministic; checksummed by the
    fixture test."""
    from collections import defaultdict
    byb = defaultdict(dict)
    for base, sfx, w, _ in transform.pairs:
        byb[base][sfx] = w
    verbs = set()
    for base, d in byb.items():
        if "ed" in d or "ing" in d:
            verbs.add(base)
            for k in ("ed", "ing", "s"):
                if k in d:
                    verbs.add(d[k])
    if past_page is not None:
        for base, label in past_page.rows.items():
            verbs.add(base)
            for form in label.split(","):
                verbs.add(form.strip())
    return verbs


class Depth2Resolver:
    """The clause organ over one LawBook + the verb artifact."""

    def __init__(self, lawbook, verbs):
        self.lawbook = lawbook
        self.verbs = verbs
        self.fem = lawbook.classified("f")
        self.masc = lawbook.classified("m")
        self.aux_all = AUX_SG | AUX_PL | MODALS | \
            frozenset({"be", "been", "being", "get", "got", "had",
                       "have", "has"})

    # ── word classes ─────────────────────────────────────────────────
    def num_of(self, word):
        return self.lawbook.number_of(word)

    def is_verbish(self, w):
        if w in self.aux_all or w in self.verbs \
                or w.endswith("ing") or w.endswith("ed"):
            return True
        if w in STOPWORDS or w in DETS or w in SUBJ_PRONOUNS \
                or w in REFLEXIVES:
            return False
        if w in self.fem or w in self.masc:
            return False
        if w.endswith("s") and not w.endswith("ss") \
                and w[:-1] in self.verbs:
            return True
        if self.num_of(w) is not None:
            return False
        return w.isalpha()

    # ── NP machinery ─────────────────────────────────────────────────
    def np_at(self, ws, i):
        """NP starting at i -> (end_index_exclusive, (gender, number))
        or None. Last-noun-of-run heads; of-passthrough partitives;
        names by page or capitalization."""
        wl = ws[i].lower()
        if wl in SUBJ_PRONOUNS and wl != "you":
            return i + 1, SUBJ_PRONOUNS[wl]
        if wl in DETS:
            j = i + 1
            last = None
            while j < len(ws) and j - i <= 7:
                wj = ws[j].lower()
                if wj == "of" and last is not None:
                    j += 1
                    continue
                if wj in STOPWORDS or wj in self.verbs or \
                        (self.is_verbish(wj)
                         and self.num_of(wj) is None):
                    break
                if self.num_of(wj) is not None:
                    last = j
                j += 1
            if last is not None:
                return last + 1, (None, self.num_of(ws[last].lower()))
            return None
        if wl in self.fem:
            return i + 1, ("f", "sg")
        if wl in self.masc:
            return i + 1, ("m", "sg")
        if ws[i][:1].isupper() and wl not in DETS \
                and wl not in STOPWORDS and wl not in self.verbs \
                and not self.is_verbish(wl) \
                and self.num_of(wl) is None and wl not in REFLEXIVES:
            return i + 1, (None, "sg")     # unlisted NAME, by case
        return None

    # ── the resolver ─────────────────────────────────────────────────
    def resolve(self, ws, ri):
        """Antecedent phi for the reflexive at index ri, or None."""
        # 1: relativizer-head override
        for k in range(ri - 1, 0, -1):
            if ws[k].lower() in RELATIVIZERS:
                for s in range(max(0, k - 8), k):
                    r = self.np_at(ws, s)
                    if r and r[0] == k:
                        return r[1]
                break
        # 2: walk left through the verb cluster
        i = ri - 1
        while i >= 0:
            w = ws[i].lower()
            prev = ws[i - 1].lower() if i >= 1 else ""
            if self.num_of(w) is not None and \
                    (prev in DETS or prev == "of"
                     or self.num_of(prev) is not None):
                for s in range(max(0, i - 7), i + 1):
                    r = self.np_at(ws, s)
                    if r and r[0] == i + 1:
                        return r[1]
                return (None, self.num_of(w))
            if w in self.fem:
                return ("f", "sg")
            if w in self.masc:
                return ("m", "sg")
            if ws[i][:1].isupper() and i > 0 and w not in DETS \
                    and w not in STOPWORDS and w not in self.verbs \
                    and self.num_of(w) is None:
                return (None, "sg")
            if w in SUBJ_PRONOUNS and w != "you":
                return SUBJ_PRONOUNS[w]
            i -= 1
        return None

    def violation(self, ws):
        """0 = consonant, 1 = violation, None = abstain (law: never
        guessed — himself/herself against a gender-unknown subject
        abstains)."""
        ri = next((i for i, w in enumerate(ws)
                   if w.lower() in REFLEXIVES), None)
        if ri is None:
            return 0
        r_gender, r_number = REFLEXIVES[ws[ri].lower()]
        phi = self.resolve(ws, ri)
        if phi is None:
            return None
        s_gender, s_number = phi
        if s_number is None:
            return None
        if s_number != r_number:
            return 1
        if r_gender and s_gender and r_gender != s_gender:
            return 1
        if r_gender in ("m", "f") and s_gender is None:
            return None
        return 0

    def verb_number(self, ws, j):
        """The number a verb cluster starting near j demands."""
        for w in ws[j:j + 3]:
            w = w.lower()
            if w in AUX_SG:
                return "sg"
            if w in AUX_PL:
                return "pl"
            if self.is_verbish(w):
                if w.endswith("s") and not w.endswith("ss"):
                    return "sg"
                if not w.endswith("ing") and not w.endswith("ed"):
                    return "pl"
        return None
