"""XVII T-1: pin the citizenship sample (run ONCE — law 2).

The pool is probe 59's lived diet: KNOWN = the full-stream words;
teachable = lexicon minus KNOWN, alphabetic, len >= 3; stems = the
teachable words that carry mined children (6,076 stems / 7,005
children — probe-exact). The 50-stem unlock sample is a seed-7
shuffle; the predicted-pron case is the first sampled stem whose +s
spelling is NOT in the lexicon (law 2's REPORT lane); the anagram
case (past = tap+s) is verified against the counts before pinning.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import get_organs

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"
OUT = FIX / "citizenship_sample.json"


def main():
    if OUT.exists():
        print(f"REFUSE: {OUT} exists — regeneration is an event, "
              f"not a refresh.")
        return 1
    organs = get_organs()
    corpus = organs.embedder.corpus

    stream = json.loads((FIX / "reading_stream_full.json").read_text(
        encoding="utf-8"))["stream"]
    known = {w for w in stream if w in corpus}
    teach = [w for w in corpus
             if w not in known and w.isalpha() and len(w) >= 3]

    byb = defaultdict(dict)
    for b, s, w, _ in organs.transform.pairs:
        byb[b][s] = w
    stems = [w for w in teach if byb.get(w)]
    children = sum(len(byb[w]) for w in stems)

    pron2 = defaultdict(list)
    for w, p in corpus.items():
        pron2[tuple(p)].append(w)
    coll = sum(1 for w in teach
               if any(x in known for x in pron2[tuple(corpus[w])]
                      if x != w))

    rng = random.Random(7)
    sample = sorted(rng.sample(stems, 50))
    predicted = next(s for s in sample
                     if "s" not in byb[s] and (s + "s") not in corpus)

    past = tuple(corpus["past"])
    assert Counter(past) == Counter(corpus["taps"]) and \
        tuple(corpus["taps"]) != past, "the anagram case broke"

    fx = {
        "protocol": ("probe 59: KNOWN = full-stream words; teachable "
                     "= lexicon - KNOWN, alpha, len>=3; stems carry "
                     "mined children; sample = seed-7 choice of 50"),
        "pool": {"known": len(known), "teachable": len(teach),
                 "stems": len(stems), "children": children,
                 "ear_collisions": coll},
        "sample": {s: byb[s] for s in sample},
        "predicted_case": {"stem": predicted, "guess": predicted + "s"},
        "anagram_case": {"word": "past", "base": "tap", "sfx": "s"},
        "ear_case": {"teach": "aalen", "hears": "alan"},
    }
    OUT.write_text(json.dumps(fx, indent=1) + "\n", encoding="utf-8",
                   newline="\n")
    print(f"pool: stems {len(stems)} children {children} "
          f"(want 6076/7005); ear {coll}/{len(teach)} = "
          f"{coll/len(teach)*100:.1f}%")
    print(f"sample of 50 pinned; predicted case: {predicted}+s; "
          f"anagram case: past = tap+s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
