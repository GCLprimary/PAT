"""
elfix/lexicon/inferred_store.py  —  Stage 4: the inferred-pronunciation store
=============================================================================
The governance layer that grows the dictionary. Generated pronunciations live
here, SEPARATE from the attested CMU core, with ternary evidence and
malleable->confirmed promotion. Three guarantees the laws demand:

  - never SHADOW the attested core (a lookup prefers attested ground truth);
  - never COMPOUND (generation reads attested stems ONLY — no inferred-on-inferred,
    the error-cascade trap the spec calls out);
  - never COLLAPSE inferred into attested (the growable lexicon is a re-derivable
    VIEW, not a write-back).

Evidence is ternary (Law 5) AND distinguishes absence from zero (Law 2):
  attested  +1   (CMU ground truth)
  inferred   0   (generated; silent on truth until corroborated)
  rejected  -1   (evidenced-against: contradiction or illegality)
  absent  None   (never seen — NOT the same as inferred-at-0)

PROVENANCE
----------
- malleable->confirmed promotion: [GCL] malleable_library.
- ternary evidence: [ElfIX] ternary_valence (why_piece6).
- Composition inputs: lexicon/ortho_affix + compose_pron (Stages 1-2).

CORROBORATION (the promotion fuel)
----------------------------------
A malleable entry is promoted to confirmed by EITHER `CONFIRM_AT` independent
agreeing sources (multiple decompositions composing to the same pron) OR
`FREQ_CONFIRM` running-text occurrences (a recurring OOV is a real word, not a
nonce). The frequency path is fed by `running_text.grow_store` (the corpus is now
in place). A one-off OOV that decomposes stays MALLEABLE — honestly uncertain.
Note: running-text inferred prons have NO gold to check against (the word is OOV
by definition), so frequency is a confidence heuristic; the precision evidence is
the holdout gate's 95.8% on regular decompositions, not these.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Iterable
from .ortho_affix import decompose
from .compose_pron import compose

CONFIRM_AT = 2            # independent agreeing sources to promote malleable->confirmed
FREQ_CONFIRM = 3          # OR running-text occurrences (a recurring OOV is a real word)


@dataclass
class Inferred:
    word: str
    pron: List[str]
    stem: str
    suffix: str
    sources: Set[str] = field(default_factory=set)
    freq: int = 0                       # running-text occurrences (corroboration)

    @property
    def state(self) -> str:
        return ("confirmed"
                if len(self.sources) >= CONFIRM_AT or self.freq >= FREQ_CONFIRM
                else "malleable")


class InferredStore:
    """Generated pronunciations, governed. `attested` (the CMU core) is read-only
    ground truth and is never written."""

    def __init__(self, attested: Dict[str, List[str]]):
        self.attested = attested
        self.inferred: Dict[str, Inferred] = {}
        self.rejected: Dict[str, str] = {}              # word -> reason (-1)

    def evidence(self, word: str) -> Optional[int]:
        """Ternary evidence, with absence distinct from zero (Law 2/5)."""
        if word in self.attested:
            return 1
        if word in self.rejected:
            return -1
        if word in self.inferred:
            return 0
        return None                                     # absent != inferred(0)

    def lookup(self, word: str) -> Tuple[Optional[List[str]], str]:
        """Provenance-aware: attested ground truth always wins (never shadowed)."""
        if word in self.attested:
            return list(self.attested[word]), "attested"
        e = self.inferred.get(word)
        if e is not None:
            return list(e.pron), "inferred:" + e.state
        return None, "absent"

    def propose(self, word: str, pron: List[str], stem: str, suffix: str,
                source: str, weight: int = 1) -> str:
        """Add a generated pronunciation (malleable), or corroborate an agreeing
        one (-> confirmed at CONFIRM_AT sources OR FREQ_CONFIRM occurrences).
        `weight` is the running-text frequency this evidence carries. A conflicting
        pron is a contradiction -> rejected (-1). Never overwrites attested."""
        if word in self.attested:
            return "attested"                           # never shadow ground truth
        if word in self.rejected:
            return "rejected"
        e = self.inferred.get(word)
        if e is None:
            self.inferred[word] = Inferred(word, list(pron), stem, suffix,
                                           {source}, weight)
        elif e.pron == pron:
            e.sources.add(source); e.freq += weight     # corroboration
        else:
            self._reject(word, "conflicting inferred pronunciations")
            return "rejected"
        return self.inferred[word].state

    def _reject(self, word: str, reason: str) -> None:
        self.inferred.pop(word, None)
        self.rejected[word] = reason

    def confirmed_view(self) -> Dict[str, List[str]]:
        """The growable lexicon = attested + CONFIRMED inferred, a re-derivable
        VIEW (Law 3). Inferred is never merged INTO the attested dict."""
        out = {w: list(p) for w, p in self.attested.items()}
        for w, e in self.inferred.items():
            if e.state == "confirmed":
                out[w] = list(e.pron)
        return out

    def grow(self, oov: Iterable[str]) -> Dict[str, int]:
        """Grow the store over OOV words. decompose reads the ATTESTED core ONLY,
        so a stem is never an inferred word (no compounding). Each decomposition
        that composes is a corroboration source."""
        stats = {"covered": 0, "malleable": 0, "confirmed": 0,
                 "rejected": 0, "uncovered": 0}
        attested_only = self.attested.__contains__      # generation reads attested only
        for word in oov:
            if word in self.attested:
                continue
            proposed = False
            for stem, suf in decompose(word, attested_only):
                pron = compose(self.attested[stem], suf)
                if pron is None:
                    continue
                self.propose(word, pron, stem, suf, f"decomp:{stem}+{suf}")
                proposed = True
            if not proposed:
                stats["uncovered"] += 1
            elif word in self.rejected:
                stats["rejected"] += 1
            else:
                stats["covered"] += 1
                stats[self.inferred[word].state] += 1
        return stats


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from elfix.data_io import load_cmu

    cmu = load_cmu()
    # holdout: pretend every 20th word is OOV; grow the store from the rest.
    held = {w: p for i, (w, p) in enumerate(cmu.items()) if i % 20 == 0}
    attested = {w: p for w, p in cmu.items() if w not in held}
    store = InferredStore(attested)
    stats = store.grow(held.keys())
    print(f"held-out OOV: {len(held):,}")
    print(f"grow stats: {stats}")
    ok = tot = 0
    for w, truth in held.items():
        pron, src = store.lookup(w)
        if src.startswith("inferred"):
            tot += 1
            ok += (pron == truth)
    print(f"recovered {tot:,}/{len(held):,} held-out words as inferred; "
          f"pronunciation precision {ok / max(1, tot):.1%}")
    print("(most entries stay MALLEABLE -- confirmation awaits running-text "
          "corroboration; the store is honestly uncertain, not falsely confident.)")
