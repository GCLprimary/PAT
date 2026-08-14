"""mirror demo (W-6): the system's one-paragraph existence proof.

A NOVEL derived word arrives (never stored anywhere). The mirror loop
analyzes it against what memory actually knows: it recovers (base,
suffix) by reflecting seam-bound predictions, retrieves the base's
episode from a_mem by a form-only cue, and reports the base's derived
family and meaning neighborhood. Then a word whose base memory does NOT
know arrives — and the loop refuses, plainly, instead of confabulating.

Runs from a fresh checkout:  python examples/demo_core.py   (< 30 s)
"""
import os
import sys
import tempfile
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from mirror import (Embedder, MeaningGeometry, MirrorLoop, Rung, Transform,
                    mine_pairs)

N_BASES = 12


def main():
    t0 = time.time()
    print("loading organs...")
    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    geo = MeaningGeometry()
    print(f"  represent: {emb.dim}-dim shape geometry over "
          f"{len(emb.corpus)} pronunciations")
    print(f"  transform: {len(tr.pairs)} mined pairs -> "
          f"{len(tr.suffixes)} learned suffix forms")
    print(f"  meaning:   {geo.dim}-word PPMI count geometry "
          f"({time.time() - t0:.0f}s)")

    # what memory knows: the probe-20 sampling, filtered to meaning vocab
    rng2 = np.random.default_rng(11)
    byb = defaultdict(dict)
    for base, sfx, w, _ in tr.pairs:
        byb[base][sfx] = w
    cands = [b for b, d in byb.items() if len(d) >= 1 and len(b) >= 4]
    rng2.shuffle(cands)
    known_pool, withheld_pool = cands[:40], cands[40:80]
    known = [b for b in known_pool if b in geo][:N_BASES]

    rung = Rung(emb, geo)
    mem, hooks, mids = rung.write_bank(known, path=tempfile.mkdtemp())
    loop = MirrorLoop(emb, tr, {b: emb.corpus[b] for b in known})
    print(f"  memory:    {len(known)} base episodes on the grid-47 stage "
          f"({time.time() - t0:.0f}s)")

    # ── a novel derived word whose base memory knows ─────────────────
    base = next(b for b in known if byb[b])
    sfx, novel = next(iter(byb[base].items()))
    print()
    print("=" * 64)
    print(f"NOVEL WORD: '{novel}'  (never stored; base '{base}' is in memory)")
    print("=" * 64)
    a = loop.analyze(emb.corpus[novel])
    print(f"  loop: {a.mode} -> base '{a.base}' + suffix '-{a.suffix}' "
          f"(agreement {a.score:.3f}, depth L{a.depth})")

    rec = hooks.recall_context(rung.episode(a.base, meaning=False))
    got = mem.library.get(rec.identity).meta["word"]
    print(f"  a_mem: form-only cue -> episode {rec.identity} ('{got}') "
          f"[{'correct' if got == a.base else 'WRONG'}]")
    family = ", ".join(f"-{s}: {w}" for s, w in sorted(byb[a.base].items()))
    print(f"  family of '{a.base}': {family}")
    neigh = [w for _, w in geo.neighbors(a.base, k=12)
             if w not in geo.vocab[:geo.content_cut]][:4]
    print(f"  meaning neighborhood: {', '.join(neigh)}  "
          f"(content words only, display filter)")

    # ── a word whose base memory does NOT know ───────────────────────
    ub = next(b for b in withheld_pool if byb[b])
    _, unknown_word = next(iter(byb[ub].items()))
    print()
    print("=" * 64)
    print(f"UNKNOWN-BASE WORD: '{unknown_word}'  (base '{ub}' NOT in memory)")
    print("=" * 64)
    a2 = loop.analyze(emb.corpus[unknown_word])
    if a2.mode == "REFUSE":
        print(f"  loop: REFUSE — best standing agreement {a2.score:.3f} "
              f"< theta 0.98.")
        print("  I don't recognize this word's base. I won't invent one.")
    else:
        print(f"  loop: {a2.mode} {a2.base}+{a2.suffix} — CONFABULATION, "
              f"this is a bug")

    print(f"\ndone in {time.time() - t0:.1f}s  (target < 30s)")


if __name__ == "__main__":
    main()
