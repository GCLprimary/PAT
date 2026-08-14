"""
elfix/running_text.py  —  load the running-text corpus into tagged utterances
=============================================================================
The seam where the two halves of the vision meet: it turns `data/corpus.txt`
(one sentence per line, the ElfIX contract) into ordered, sentence-delimited
sequences of phoneme units, AND grows the inferred lexicon from the corpus's own
OOV — running-text FREQUENCY being the corroboration the holdout gate lacked.

  load_utterances   corpus.txt -> [[word, ...], ...]   (one line = one utterance,
                    the carry-reset boundary)
  grow_store        self-build the lexicon from OOV, weighted by frequency
                    (Stages 1-2 + the Stage-4 store), composing from ATTESTED
                    stems only (no compounding)
  tag_utterances    map each word to phonemes with a provenance tag:
                    attested (CMU) / inferred (store) / oov

This is what the deferred frontiers consume: the carry rate re-validated over
real cross-word context, the word rung across sentences, Tier-4/5 BETWEEN words,
Tier-6 op semantics read off a real next-unit task.

PROVENANCE: [NEW->original]. Law 2/3/5 governance lives in lexicon/inferred_store;
this only loads and tags. No phonemes from nltk's cmudict — only our CMU core.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from .data_io import load_cmu
from .lexicon.inferred_store import InferredStore
from .lexicon.ortho_affix import decompose
from .lexicon.compose_pron import compose

_HERE = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = _HERE / "data" / "corpus.txt"


@dataclass
class Token:
    word: str
    phonemes: Optional[List[str]]      # None when oov
    tag: str                           # 'attested' | 'inferred' | 'oov'


def load_utterances(path: Path = DEFAULT_CORPUS) -> List[List[str]]:
    """corpus.txt -> utterances (each a list of words). One sentence per line is
    one utterance — the carry-reset boundary. Tolerant of CRLF/LF."""
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    return [words for ln in text.splitlines() if (words := ln.split())]


def grow_store(utterances: List[List[str]], cmu: Dict[str, List[str]]) -> InferredStore:
    """Self-build the lexicon from corpus OOV, weighting each by running-text
    FREQUENCY. Composes from ATTESTED stems ONLY (no inferred-on-inferred). A
    frequent decomposable OOV is a real inflection -> confirmed; a one-off may be a
    coincidence -> malleable."""
    store = InferredStore(cmu)
    freq = Counter(w for utt in utterances for w in utt)
    for word, n in freq.items():
        if word in cmu:
            continue
        for stem, suf in decompose(word, cmu.__contains__):
            pron = compose(cmu[stem], suf)
            if pron is not None:
                store.propose(word, pron, stem, suf, f"decomp:{stem}+{suf}", weight=n)
    return store


def tag_utterances(utterances: List[List[str]], cmu: Dict[str, List[str]],
                   store: Optional[InferredStore] = None
                   ) -> Tuple[List[List[Token]], Dict[str, int]]:
    """Map each word to phonemes with a provenance tag (attested / inferred / oov).
    Each unique word is resolved once. Returns tagged utterances + token counts."""
    resolved: Dict[str, Token] = {}

    def resolve(w: str) -> Token:
        if w in cmu:
            return Token(w, list(cmu[w]), "attested")
        if store is not None:
            pron, src = store.lookup(w)
            if src.startswith("inferred"):
                return Token(w, pron, "inferred")
        return Token(w, None, "oov")

    stats: Counter = Counter()
    tagged: List[List[Token]] = []
    for utt in utterances:
        toks = []
        for w in utt:
            if w not in resolved:
                resolved[w] = resolve(w)
            t = resolved[w]
            toks.append(t)
            stats[t.tag] += 1
        tagged.append(toks)
    return tagged, dict(stats)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(_HERE))
    cmu = load_cmu()
    utts = load_utterances()
    store = grow_store(utts, cmu)
    tagged, stats = tag_utterances(utts, cmu, store)
    total = sum(stats.values())
    print(f"utterances {len(utts):,}   tokens {total:,}")
    for tag in ("attested", "inferred", "oov"):
        print(f"  {tag:9} {stats.get(tag, 0):>9,}  ({stats.get(tag, 0) / total:.2%})")
    conf = sum(1 for e in store.inferred.values() if e.state == "confirmed")
    print(f"self-built lexicon: {len(store.inferred):,} inferred words "
          f"({conf:,} confirmed by frequency/agreement, rest malleable); "
          f"{len(store.rejected):,} rejected (contradiction)")
    base = stats.get("attested", 0) / total
    lift = (stats.get("attested", 0) + stats.get("inferred", 0)) / total
    print(f"token coverage: {base:.2%} attested -> {lift:.2%} with the inferred tail")
