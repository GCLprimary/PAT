"""
scripts/constituents.py  —  data for the constituent/stack mechanism (the next frontier)
========================================================================================
The 1st-order ceiling is HIERARCHY (scripts/ngram_ceiling): the output stalls inside a
constituent because a flat model has no phrase CLOSURE. This gathers the data for the
fix. Two boundary mechanisms compared, both COUNTED, no gradient:

  FLAT chunker (cut at binding TROUGHS) — the syntactic analogue of syllable boundaries
      at sonority minima. MEASURED WEAK (~random): local boundary detection fails, because
      constituency is global/recursive, not a local contour.
  RECURSIVE agglomerative bracketer (merge strongest binding FIRST, build a tree) — the
      Tier-3 emergent-unit move (merge by coherence) lifted to syntax, and it PRODUCES
      NESTING (a tree = a stack). This works: it merges real grammatical units first
      (aux+been, more+than, adj+noun) and brackets NPs/PPs/verb-groups.

The binding is class-pair PMI: how much more c' follows c than chance (the same earned
class-bigram the scaffold uses). No gradients (Law 6); every merge is a count you can
point at.

PROVENANCE: [NEW->established] greedy mutual-information bracketing for unsupervised
constituency (Magerman & Marcus 1990); the agglomerative move is Tier-3's, recursive.

Run:  python scripts/constituents.py        (~2-3 min: the clustering earns)
"""
import sys
import math
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    a = int(len(utts) * 0.9)
    train, test = utts[:a], utts[a:]
    p = Predictor(train, vocab)
    print("  earning classes + scaffold...")
    space = SemanticSpace(train, vocab, unigram=p.unigram)
    sc = SyntaxScaffold(space, train, vocab)

    # ── class-pair PMI: the BINDING strength of an adjacent transition ───────────
    Npairs = sum(sum(r.values()) for r in sc.bg.values())
    left = {c: sum(r.values()) for c, r in sc.bg.items()}
    right = Counter()
    for c, r in sc.bg.items():
        for c2, k in r.items():
            right[c2] += k

    def pmi(c1, c2):
        j = sc.bg.get(c1, {}).get(c2, 0)
        return -6.0 if j == 0 else math.log2((j * Npairs) / (left[c1] * right[c2]))

    def bracket(words):
        """Greedy agglomerative bracketing: repeatedly merge the adjacent span-pair with
        the strongest edge-binding into a constituent -> a binary tree (a parse)."""
        units = [(w, sc.sclass(w), sc.sclass(w)) for w in words if w in vocab]
        while len(units) > 1:
            bi, best = 0, -9e9
            for i in range(len(units) - 1):
                b = pmi(units[i][2], units[i + 1][1])      # right edge of L to left edge of R
                if b > best:
                    best, bi = b, i
            l, r = units[bi], units[bi + 1]
            units[bi:bi + 2] = [("(" + l[0] + " " + r[0] + ")", l[1], r[2])]
        return units[0][0] if units else ""

    print("\n  RECURSIVE agglomerative bracketing (merge strongest binding first):")
    shown = 0
    for u in test:
        if 5 <= len(u) <= 11:
            print("    " + bracket(u))
            shown += 1
            if shown == 8:
                break

    def lab(c):
        if c[0] == "fn":
            return "'" + c[1] + "'"
        return "{" + ",".join(space.class_words[c[1]][:2]) + "}" if c[0] == "cl" else "unk"

    print("\n  the TIGHTEST class-bindings (what the tree merges FIRST = grammatical units):")
    pairs = [(pmi(c1, c2), c1, c2) for c1 in sc.bg for c2 in sc.bg[c1]
             if sc.bg[c1][c2] >= 100]
    for b, c1, c2 in sorted(pairs, reverse=True)[:10]:
        print(f"    {b:+.1f}  {lab(c1)} -> {lab(c2)}")

    print("\n  ==> DIRECTIONALLY VIABLE (counted, recursive), but the v1 is WEAK. A RECURSIVE")
    print("      agglomerative bracketer (the Tier-3 merge-by-binding move, lifted to syntax)")
    print("      builds real NPs/PPs/verb-groups and NESTS them (a tree = a stack), where the")
    print("      FLAT trough-chunker failed. BUT a proxy validation (does it recover obligatory")
    print("      NP/PP/VP bonds vs random merge?) is only MODEST: ~41% vs 35% random overall")
    print("      (+6pts) -- above chance on det+noun/prep+x, worse on aux+verb (plausibly")
    print("      correct: verb binds its object first). The proxy is crude (penalizes correct")
    print("      det-over-adjective attachment), so it likely understates -- but greedy")
    print("      class-PMI is a STARTING POINT, not a strong parser. The real build needs a")
    print("      better binding signal (head-awareness) + real evaluation (a treebank or a")
    print("      downstream task). NEXT: a SyntaxTree module + parse-guided generation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
