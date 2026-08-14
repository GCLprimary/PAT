"""E-2: the wug demo — generalization, out loud.

"This is a wug; now there are two ___." The stem does not exist; the
induced table answers anyway, selectively, and cites its row.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import AllomorphTable, Embedder
from mirror.surface import final_signature
from mirror.wug import (novel_stems, textbook_gold, wug_inflect,
                        wug_surface)

t0 = time.time()
emb = Embedder()
table = AllomorphTable().fit(emb.corpus)

wug = ("w", "AH", "g")
assert tuple(wug) not in {tuple(p) for p in emb.corpus.values()}
sig = final_signature(wug[-1])
cls = wug_inflect(table, wug, "s")
dist = table.support["s"][sig]
print(f'"this is a wug; now there are two ..." -> wug+{cls}: '
      f'{" ".join(wug_surface(wug, cls))}')
print(f"  the table's row: {sig} -> {cls} "
      f"({dist[cls]}/{sum(dist.values())} in training) — voiced final "
      f"takes z, learned from counts, applied to a stem that has "
      f"never existed")

stems = novel_stems(emb.corpus, n=10, seed=50)
print("\nten more wugs:")
for stem in stems:
    row = []
    for sfx in ("s", "ed"):
        cls = wug_inflect(table, stem, sfx)
        row.append(f"+{sfx}: " + (" ".join(wug_surface(stem, cls))
                                  if cls else "REFUSE (unseen final)"))
    print(f"  {' '.join(stem):18s} {row[0]:26s} {row[1]}")

print(f"\ndone in {time.time() - t0:.1f}s")
