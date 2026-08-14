"""
scripts/showcase.py  —  the whole system, on real inputs (a capstone demo + data)
=================================================================================
Runs diverse inputs through the FULL ElfIX stack with every capability on, and prints
both the OUTPUT and the structural DATA, so you can see where it stands:

  read   -> tag/pronounce (incl. OOV grown from shape), three memory tiers updated
  topic  -> the named distributional classes (what it's talking about)
  locator-> the highest-surprisal words, TYPED by class (where meaning attached + kind)
  respond-> bounded, subject->predicate-arced, grammatical-shaped, on-topic, content-rich
  data   -> per-response metrics (content / function balance, sentence structure)

Every value is a count you can point at; no gradient anywhere. The output is the SHAPE
of language (topical, content-rich, role-ordered, bounded), counted — not a parser.

Run:  python scripts/showcase.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.session import Session
from elfix.lexicon.inferred_store import InferredStore

INPUTS = [
    "the president spoke to the senate about the new law",
    "she walked into the dark empty room and saw",
    "the army crossed the river at dawn and attacked",
    "he loved her more than anything else in the world",
    "the company lost three million dollars last year",
    "she kept blogging all afternoon and then blogging again",   # OOV: 'blogging'
]


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    print("building the full system (model + topic classes + syntactic scaffold)...")
    p = Predictor(utts[:52000], vocab)
    space = SemanticSpace(utts[:52000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:52000], vocab)
    skel = space.skeleton
    print(f"ready: {len(p.bigram):,} contexts, {len(space.class_words)} meaning-classes, "
          f"syntactic scaffold + sentence arc\n")

    tot = {"content": 0.0, "fn": 0.0, "n": 0}
    for text in INPUTS:
        s = Session(p, cmu, store=InferredStore(cmu), space=space, scaffold=scaffold,
                    learn=False)
        r = s.read(text)
        out = s.respond(n=26, temperature=0.7, rng_seed=7,
                        boundaries=True, position_bias=1.5)
        words = [w for w, _, _ in out]
        body = [w for w in words if w != "."]
        content = [w for w in body if w not in skel]
        sents = max(1, words.count(".") + (1 if body and words[-1] != "." else 0))

        print("=" * 78)
        print(f"INPUT : {text}")
        if r.grown:
            tok = next((t for t in r.tokens if t.tag == "inferred"), None)
            print(f"  OOV  : grew {r.grown} new word from its shape"
                  + (f" ('{tok.word}', {tok.n_phonemes} phonemes)" if tok else ""))
        print(f"  topic: {', '.join(s.topics(3))}")
        loc = "; ".join(f"{w}({h:.0f}){t or ''}{'/' + r if r else ''}"
                        for w, h, t, r in s.locator_typed(3))
        print(f"  meaning attached at: {loc}")
        print(f"  RESPONSE: {' '.join(words)}")
        print(f"  data: content {len(content)/max(1,len(body)):.0%}, "
              f"function {1-len(content)/max(1,len(body)):.0%}, "
              f"{sents} sentence(s) ~{len(body)//sents} words\n")
        tot["content"] += len(content) / max(1, len(body))
        tot["fn"] += 1 - len(content) / max(1, len(body))
        tot["n"] += 1

    n = tot["n"] or 1
    print("=" * 78)
    print(f"ACROSS {n} INPUTS:  content {tot['content']/n:.0%}, function {tot['fn']/n:.0%} "
          f"(real English ~50/50) -- bounded, role-ordered, on-topic output.")
    print("  Strong: topic identification, content, sentence boundaries, subject->object")
    print("          order, OOV pronounce+learn. Honest ceiling: full grammaticality")
    print("          (phrase structure + agreement) -- a counted SHAPE, not a parser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
