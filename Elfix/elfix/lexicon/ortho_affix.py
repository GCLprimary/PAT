"""
elfix/lexicon/ortho_affix.py  —  Stage 1: orthographic affixes + OOV decompose
==============================================================================
The grapheme twin of emergent/appendix.py. Discover productive word-final LETTER
shapes, then decompose an OOV spelling into a known stem + affix, applying the
regular English spelling restorations. See spec_lexicon_growth.md.

PROVENANCE
----------
- [NEW->original], mirrors emergent.appendix.discover_appendices on the
  orthographic side. Contrast baseline: Morfessor (Creutz & Lagus 2007).

DESIGN LAW CHECK
----------------
Law 1/3: the affix inventory is an earned, re-derivable view of the vocabulary
(productivity, no hand-listing). NOT circular: `decompose` uses stem-membership as
a GENERATION input (the held-out word's pronunciation is the gold, independent of
decomposability) — unlike the segmentation gold, where stem-membership WAS the
gold's defining criterion. See spec_lexicon_growth.md.

OPEN (carried forward): the productivity `frac` (same open question as the appendix
threshold); over-generation (a productive ending that is not an affix, e.g. -le)
is filtered by the stem-in-lexicon check but not fully — Stage 3 (phonotactic
critic) and longest-stem preference are the designated refinements.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable, Dict, List, Set, Tuple, Callable

# v1 scope: the regular English INFLECTIONAL suffixes (stress-preserving).
# discover_suffixes confirms the CORE of these (s, es, ed, ing, er) are productive;
# `est` is genuinely rare (superlatives are infrequent) so it sits below threshold
# and is included by linguistic scope, not productivity. composition (compose_pron)
# knows the allomorphy for exactly this set.
INFLECTIONAL: Tuple[str, ...] = ("s", "es", "ed", "ing", "er", "est")


def discover_suffixes(vocab: Iterable[str], max_len: int = 3,
                      frac: float = 0.1) -> Set[str]:
    """Earn productive word-final letter shapes by stem-diversity (Law 1) — the
    orthographic analogue of discover_appendices. Returned for inspection; v1
    composition operates on the INFLECTIONAL subset it has allomorph rules for.

    Finding (honest, carried forward): the ORTHOGRAPHIC distribution is far more
    skewed than the phoneme-shape one — every word ends in *some* letter, so single
    letters (e, s) dominate and the multi-letter inflectional affixes (ed, ing, es,
    er) only clear the cutoff at frac~0.1, not the appendix's 0.5. The exact frac
    is the same open productivity-threshold question; the gate does not depend on
    it (it decomposes with INFLECTIONAL directly)."""
    prod: Dict[str, Set[str]] = defaultdict(set)
    for w in vocab:
        for k in range(1, max_len + 1):
            if len(w) > k + 1:                     # require a stem of >= 2 letters
                prod[w[-k:]].add(w[:-k])
    if not prod:
        return set()
    cutoff = frac * max(len(s) for s in prod.values())
    return {suf for suf, s in prod.items() if len(s) >= cutoff}


def _restorations(base: str) -> List[str]:
    """Regular English spelling-restoration candidates for the stem left after
    stripping a suffix: identity, e-insertion (googl->google), consonant
    un-doubling (stopp->stop), and i->y (studi->study). Irregulars (wife->wives)
    are NOT handled in v1 — they simply fail to decompose."""
    cands = [base]
    if base:
        cands.append(base + "e")                           # drop-e words
        if len(base) >= 2 and base[-1] == base[-2]:
            cands.append(base[:-1])                         # un-double
        if base[-1] == "i":
            cands.append(base[:-1] + "y")                  # i -> y
    return cands


def decompose(word: str, in_lexicon: Callable[[str], bool],
              suffixes: Iterable[str] = INFLECTIONAL) -> List[Tuple[str, str]]:
    """
    Return (stem, suffix) splits of `word` where a spelling-restored stem is a
    known word (`in_lexicon(stem)` is True). Longest suffix first, first valid
    restoration per suffix. Empty list if nothing decomposes.

    >>> known = {"cat", "run", "make", "bus"}
    >>> decompose("cats", known.__contains__)
    [('cat', 's')]
    >>> decompose("running", known.__contains__)
    [('run', 'ing')]
    >>> decompose("making", known.__contains__)
    [('make', 'ing')]
    >>> decompose("buses", known.__contains__)
    [('bus', 'es')]
    """
    out: List[Tuple[str, str]] = []
    for suf in sorted(set(suffixes), key=len, reverse=True):
        if len(word) > len(suf) + 1 and word.endswith(suf):
            base = word[:-len(suf)]
            for stem in _restorations(base):
                if stem != word and in_lexicon(stem):
                    out.append((stem, suf))
                    break
    return out
