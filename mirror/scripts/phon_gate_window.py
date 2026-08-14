"""The phon-gate design window: where would theta_phon have to sit?
True bindings' phon-space mass vs the homoshape imposters' phon scores.
"""
import sys, json
sys.path.insert(0, r"C:\Users\lgndz\pat\mirror")
import numpy as np
from mirror import Embedder, Transform, mine_pairs
from mirror.diagnostics import shape_seq
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
emb = Embedder()
tr = Transform(emb).fit(mine_pairs(emb.corpus))
split = json.loads((FIX / "imposter_split.json").read_text(encoding="utf-8"))
known = split["known_bases"]

def phon_bound(b, sfx):
    if sfx is None:
        return emb.phon_vec(emb.corpus[b])
    return tr.bind(emb.corpus[b], sfx, space="phon")

# true bindings in phon space
true_p = []
for base, sfx, w in split["known_forms"]:
    obs = emb.phon_vec(emb.corpus[w])
    true_p.append(float(obs @ phon_bound(base, sfx)))
true_p = np.array(true_p)

# shape-collision imposters (shape score == 1.0): their PHON scores
bindings = {}
for b in known:
    bindings[(b, None)] = (emb.shape_vec(emb.corpus[b]),
                           shape_seq(emb.corpus[b]))
    for sfx in tr.suffixes:
        v = tr.bind(emb.corpus[b], sfx)
        if v is not None:
            bindings[(b, sfx)] = (
                v, shape_seq(list(emb.corpus[b]) + tr.modal_phon[sfx]))

imposter_phon = []
for group, forms in (("known", split["known_forms"]),
                     ("unknown", split["unknown_forms"])):
    for base, sfx, w in forms:
        oseq = shape_seq(emb.corpus[w])
        obs_p = emb.phon_vec(emb.corpus[w])
        for key, (vec, bseq) in bindings.items():
            if group == "known" and key == (base, sfx):
                continue
            if bseq == oseq:                      # a perfect shape imposter
                sp = float(obs_p @ phon_bound(*key))
                imposter_phon.append((sp, w, key))

imposter_phon.sort(reverse=True)
print(f"TRUE bindings, phon space:   mean {true_p.mean():.4f}  "
      f"min {true_p.min():.4f}  p5 {np.percentile(true_p, 5):.4f}")
print(f"SHAPE-IMPOSTERS, phon space: max {imposter_phon[0][0]:.4f}  "
      f"(n={len(imposter_phon)})")
for sp, w, key in imposter_phon[:6]:
    print(f"   {sp:.4f}  '{w}' vs {key[0]}+{key[1] or 'BARE'}")
lo, hi = imposter_phon[0][0], float(np.percentile(true_p, 5))
print(f"\nTHE WINDOW: imposter phon ceiling {lo:.4f}  vs  true p5 {hi:.4f}"
      f"  ->  {'OPEN: gate fits between them' if lo < hi else 'TIGHT/CLOSED: gate costs true accepts'}")
print(f"true accepts lost at theta_p just above ceiling: "
      f"{(true_p <= lo).mean():.1%} (these become safe refusals)")
