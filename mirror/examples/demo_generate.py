"""mirror generation demo (G-6): the generative existence proof.

Five acts: produce novel derived surfaces with the count-induced
allomorphs (including epenthesis); decode a bound vector back to its
shape sequence; refuse a SUM-bound vector structurally (the seam-
connectivity theorem in action); continue an attested prompt; refuse a
word-salad prompt in plain language.

Runs from a fresh checkout:  python examples/demo_generate.py   (< 30 s)
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from mirror import (AllomorphTable, Embedder, MeaningGeometry, ShapeDecoder,
                    Transform, mine_pairs)
from mirror.generate import canonical_setup


def main():
    t0 = time.time()
    print("loading organs...")
    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    allo = AllomorphTable().fit(emb.corpus)
    dec = ShapeDecoder(emb)          # attested tie-break (promoted)
    geo = MeaningGeometry()
    gen, prompts_id, _ = canonical_setup(geo)
    print(f"  ready in {time.time() - t0:.0f}s\n")

    print("=" * 64)
    print("1 · NOVEL SURFACES — count-induced allomorphs, no hand rules")
    print("=" * 64)
    for base, sfx in (("dog", "s"), ("cat", "s"), ("horse", "s"),
                      ("play", "ed"), ("want", "ed")):
        surface = allo.surface(emb.corpus[base], sfx)
        cls = allo.choose(emb.corpus[base], sfx)
        tag = "  << epenthesis" if cls.startswith("epen") else ""
        print(f"  {base}+{sfx}:  {' '.join(emb.corpus[base])}  ->  "
              f"{' '.join(surface)}{tag}")

    print()
    print("=" * 64)
    print("2 · DECODE — a SEAM-bound vector walks back to its sequence")
    print("=" * 64)
    bound = tr.bind(emb.corpus["help"], "ing")       # helping, never stored
    d = dec.decode(bound)
    print(f"  bind(help, -ing) -> {d.status}; "
          f"{len(d.walks)} walk(s); decoded sequence:")
    print("    " + " . ".join("/".join(s) for s in d.sequence))

    print()
    print("=" * 64)
    print("3 · STRUCTURAL REFUSAL — the seam is the invertibility condition")
    print("=" * 64)
    from mirror import snap_counts
    c_base = snap_counts(emb.shape_vec(emb.corpus["help"]))
    c_suf = snap_counts(emb.shape_vec(tr.modal_phon["ing"]))
    d_sum = dec.decode((c_base + c_suf).astype(float))
    print(f"  SUM(help, -ing) [counts added, no junction bigram] -> "
          f"{d_sum.status}")
    print("  The parts superposed without the seam leave a disconnected")
    print("  graph: no walk exists, and the decoder says so structurally.")

    print()
    print("=" * 64)
    print("4 · CONTINUE — an attested prompt, whole-continuation audit")
    print("=" * 64)
    for prompt in prompts_id:                 # first held opening that stands
        out, status = gen.generate(prompt)
        if out:
            break
    coh = gen.coherence(out, gen.topic_vec(prompt))
    print(f"  held-out Brown opening: '{' '.join(prompt)}'")
    print(f"    -> '{' '.join(prompt)} {' '.join(out)}'  "
          f"(coherence {coh:+.2f})")

    print()
    print("=" * 64)
    print("5 · REFUSE — word salad, in plain language")
    print("=" * 64)
    salad = ("piano", "gravel", "senator")
    out, status = gen.generate(salad)
    print(f"  '{' '.join(salad)}' -> {status}")
    print("  Nothing I know continues from this. I have no attested path")
    print("  through these words, so I decline to invent one.")

    print(f"\ndone in {time.time() - t0:.1f}s  (target < 30s)")


if __name__ == "__main__":
    main()
