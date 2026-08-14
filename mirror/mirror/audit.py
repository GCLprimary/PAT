"""X-3: the consonance auditor (probe 46) — pages must pass the counts.

Before a page ships, its rule faces this audit: does the corpus agree?
The machinery is probe 46's, generalized — walk the pinned sentences,
find every adjacent (opener, verb-form) attestation, and measure how
often the form is the one the rule requires.

Founding precedent (the law-2 references, asserted in the tests):

  MODAL->bare   98.4%   a LAW — the counts confirm the textbook;
  PERF->ed      88.4%   strong — participle allomorphy pays the rest;
  BE->ing       20.2%   REFUTED — 'be' takes a disjunction
                        (progressive / passive / predication), and a
                        page teaching BE->ing would be teaching a
                        falsehood with a straight face.

The LawBook enforces the verdict: a page carrying an audit below
AUDIT_FLOOR is refused at load, by name and number (lessons.py).
Attestation examines the teacher too.
"""
from collections import defaultdict

MODAL_AUX = frozenset({"will", "would", "can", "could", "may", "might",
                       "must", "should", "shall", "do", "does", "did",
                       "to"})
PERF_AUX = frozenset({"has", "have", "had"})
BE_AUX = frozenset({"is", "are", "was", "were", "am", "been", "being"})


def build_form_lexicon(pairs):
    """word -> (base, form) over bases with BOTH -ed and -ing mined
    pairs (the probe-46 family: bare / ed / ing are the three-way
    choice the audit distinguishes)."""
    fam = defaultdict(dict)
    for base, sfx, w, _ in pairs:
        fam[base][sfx] = w
    forms = {}
    for base, d in fam.items():
        if "ed" in d and "ing" in d:
            forms[base] = (base, "bare")
            forms[d["ed"]] = (base, "ed")
            forms[d["ing"]] = (base, "ing")
    return forms


def audit_rule(sentences, opener_set, required_class, forms):
    """-> (consonance %, n attestations): of every adjacent
    (opener, known-form) pair in the sentences, the fraction whose form
    is the rule's required class. The number a page must carry to
    face the LawBook's floor."""
    ok = n = 0
    for s in sentences:
        for i, w in enumerate(s[:-1]):
            if w in opener_set and s[i + 1] in forms:
                _, form = forms[s[i + 1]]
                ok += int(form == required_class)
                n += 1
    return (ok / n * 100 if n else 0.0), n
