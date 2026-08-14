"""
elfix/oov.py  —  closing the loop: place a NEW word from its SOUND/MORPHOLOGY
=============================================================================
The bridge between the two halves of ElfIX. A word the system has never seen has NO
distributional history — so its first handle is its SOUND: the earned morphology
(Half A) pronounces it and segments it into a known stem + suffix, and that
segmentation PLACES it in a distributional class (Half B) before any context
accumulates. Sound for the novel, distribution for the familiar.

  pronounce : lexicon.InferredStore (already built) — compose the stem's pronunciation
              with the earned -s/-z, -t/-d allomorphy.
  place     : `infer_class` — a new word inherits its STEM's distributional class
              (topic: 'kayaking' is about kayaks), falling back to the dominant class
              of its SUFFIX (syntax: '-ing' words are participles). No gradients,
              every step a count you can point at (Law 6).

Whether the morphology actually predicts the class is the FALSIFIABLE claim
(scripts/oov_gate.py): does a held-out word's stem/suffix place it near its true
distributional class, sight unseen? If yes, the sound half informs the generative
half — the unification the project's name promises.

PROVENANCE: [NEW->original]. decompose/compose from lexicon (Stages 1-2); classes
from semantic. The morphology->class bridge is the new piece.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from typing import Dict, Optional, Tuple, Callable
from .lexicon.ortho_affix import decompose


def build_suffix_class(space, in_vocab: Callable[[str], bool]) -> Dict[str, int]:
    """Earn each inflectional suffix's DOMINANT distributional class, from the known
    words that carry it (e.g. '-ing' -> the participle class). A re-derivable view of
    the space + the affix inventory (Law 3); used as the fallback when a new word's
    stem itself has no class."""
    sc: Dict[str, Counter] = defaultdict(Counter)
    for w, cid in space.word_class.items():
        for stem, suf in decompose(w, in_vocab):
            if space.class_of(stem) is not None:
                sc[suf][cid] += 1
                break
    return {suf: c.most_common(1)[0][0] for suf, c in sc.items() if c}


def infer_class(word: str, space, in_vocab: Callable[[str], bool],
                suffix_dom: Optional[Dict[str, int]] = None) -> Tuple[Optional[int], str]:
    """Place an OOV `word` in a distributional class from its MORPHOLOGY ALONE — no
    distribution of its own required. Prefer the STEM's class (a derived word is about
    its stem); fall back to the SUFFIX's dominant class. Returns (class_id, how) or
    (None, 'absent') if it does not decompose to a known stem."""
    for stem, suf in decompose(word, in_vocab):
        c = space.class_of(stem)
        if c is not None:
            return c, f"stem:{stem}+{suf}"
        if suffix_dom and suf in suffix_dom:
            return suffix_dom[suf], f"suffix:-{suf}"
    return None, "absent"


def resolve(word: str, store, space, in_vocab: Callable[[str], bool],
            suffix_dom: Optional[Dict[str, int]] = None):
    """Full OOV placement: PRONUNCIATION (InferredStore) + distributional CLASS
    (morphology). Returns (phonemes|None, class_id|None, how). The two halves, joined
    at the frontier where each is needed."""
    pron, _src = store.lookup(word)
    cid, how = infer_class(word, space, in_vocab, suffix_dom)
    return pron, cid, how
