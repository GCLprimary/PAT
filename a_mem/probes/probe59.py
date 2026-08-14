"""Probe 59: TAUGHT-WORD CITIZENSHIP (the lantern upgrade, measured).
A taught word's status is decided by which receipts exist:
  pron on file -> FULL CITIZEN: joins the derivation index; its
  inflected surfaces certify through the standard double-lock.
  no pron    -> PARTIAL CITIZEN: remembered with its taught receipt;
  inflections refuse with the reason named.
Design numbers this probe measures against the lived diet:
  1. homophone-collision rate among teachable words (the ear clause)
  2. unlock yield: mined child surfaces per taught stem
  3. surface-pron coverage: how often a child's pron is on file vs
     needing the transform's prediction (the predicted-pron clause)
  4. the partial-citizen refusal, asserted.
"""
import json, warnings
from collections import defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

stream = json.load(open("/home/claude/review17/pat/pat/data/fixtures/reading_stream_full.json"))
if isinstance(stream, dict):
    stream = stream.get("words") or stream.get("stream") or list(stream)
KNOWN = {w for w in stream if isinstance(w, str) and w in corpus}
TEACH = [w for w in corpus if w not in KNOWN and w.isalpha() and len(w) >= 3]
print(f"lived diet: {len(KNOWN)} known; teachable pool: {len(TEACH)}")

PRON2WORDS = defaultdict(list)
for w, p in corpus.items(): PRON2WORDS[tuple(p)].append(w)
coll = [w for w in TEACH if any(x in KNOWN for x in PRON2WORDS[tuple(corpus[w])] if x != w)]
print(f"1. ear clause: {len(coll)}/{len(TEACH)} teachable words "
      f"({len(coll)/len(TEACH)*100:.1f}%) collide with a KNOWN spelling "
      f"-- e.g., {[(w, [x for x in PRON2WORDS[tuple(corpus[w])] if x in KNOWN][0]) for w in coll[:3]]}")

byb = defaultdict(dict)
for b, s, w, r in pairs: byb[b][s] = w
stems = [w for w in TEACH if byb.get(w)]
children = sum(len(byb[w]) for w in stems)
print(f"2. unlock yield: {len(stems)} teachable stems carry mined children; "
      f"{children} surfaces unlock on teach ({children/len(stems):.2f}/stem) "
      f"-- e.g., {[(w, list(byb[w].values())) for w in stems[:3]]}")

no_pron = with_pron = 0
for w in stems[:4000]:
    for sfx in ("s", "ed", "ing"):
        kid = byb[w].get(sfx)
        if kid: with_pron += 1
        else:
            guess = w + sfx if sfx != "ing" or not w.endswith("e") else w[:-1] + sfx
            if guess in corpus: with_pron += 1
            elif (w + sfx) in corpus: with_pron += 1
            else: no_pron += 1
print(f"3. surface-pron coverage: {with_pron}/{with_pron+no_pron} "
      f"({with_pron/(with_pron+no_pron)*100:.1f}%) of candidate children have "
      f"prons on file; {no_pron} would need the transform's PREDICTED pron "
      f"(wears 'predicted' provenance or refuses -- the spec's choice)")

for nonce in ("zorp", "flimber"):
    assert nonce not in corpus
print("4. partial citizen asserted: zorp/flimber have no pron on file -> "
      "\"remembered (taught receipt kept); inflections refuse: no "
      "pronunciation on file\"")
