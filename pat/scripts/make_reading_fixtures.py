"""Reading-loop fixture generation, agent side (W-3; probe 41).

Run ONCE at build time. Pins the 6,000-word frequency-ordered stream
(probe-41 protocol: corpus_big counts, count >= 4, in the CMU lexicon,
orthographic length >= 4), the 15 birth seeds (the first 15 bases in
the shuffled-pair byb order — the protocol, fourth sighting), and the
aligned 300-item derived-form test set. Appends checksums; every
existing pinned artifact stays untouched.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import Embedder, Transform, mine_pairs
from mirror.config import DATA_DIR as MIRROR_DATA

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    byb = {}
    for base, sfx, w, _ in tr.pairs:
        byb.setdefault(base, {})[sfx] = w

    cnt = Counter()
    with open(MIRROR_DATA / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            cnt.update(line.split())
    stream = [w for w, c in cnt.most_common()
              if c >= 4 and w in emb.corpus and len(w) >= 4][:6000]
    stream_set = set(stream)
    seeds = list(byb.keys())[:15]
    aligned = [[b, s, w] for b, d in byb.items() if b in stream_set
               for s, w in d.items()][:300]

    payload = {
        "stream": stream,
        "counts": {w: cnt[w] for w in stream},
        "seeds": seeds,
        "aligned_test": aligned,
        "protocol": ("corpus_big counts, count>=4, in CMU, len>=4, "
                     "frequency order, first 6000; seeds = first 15 "
                     "shuffled-byb bases; aligned test = byb pairs with "
                     "in-stream bases, first 300 in byb order"),
    }
    (FIX / "reading_stream.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")
    print(f"reading_stream.json: {len(stream)} words "
          f"(counts {min(payload['counts'].values())}.."
          f"{max(payload['counts'].values())}), {len(seeds)} seeds, "
          f"{len(aligned)} aligned test items")
    print(f"  seeds: {seeds}")
    print(f"  'place' in stream: {'place' in stream_set}")

    checks = json.loads((FIX / "checksums.json").read_text(
        encoding="utf-8"))
    checks["reading_stream.json"] = sha256(FIX / "reading_stream.json")
    (FIX / "checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print("checksums.json: appended reading_stream.json "
          f"({checks['reading_stream.json'][:16]}...)")


if __name__ == "__main__":
    main()
