"""Full-vocabulary stream fixture (X-4; probe 44). Run ONCE.

The 10x stream: every corpus_big word with count >= 2 that lives in the
CMU lexicon at orthographic length >= 4, in frequency order — the FULL
qualifying vocabulary (probe 44; Part VII's 6,000 was the cap the row
bank needed, and the dict-exact engine does not need it). Appends the
checksum; every existing pinned artifact stays untouched.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import Embedder
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
    cnt = Counter()
    with open(MIRROR_DATA / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            cnt.update(line.split())
    stream = [w for w, c in cnt.most_common()
              if c >= 2 and w in emb.corpus and len(w) >= 4]
    payload = {
        "stream": stream,
        "counts": {w: cnt[w] for w in stream},
        "protocol": ("corpus_big counts, count>=2, in CMU, len>=4, "
                     "frequency order, uncapped (probe 44); seeds are "
                     "reading_stream.json's 15"),
    }
    (FIX / "reading_stream_full.json").write_text(
        json.dumps(payload), encoding="utf-8")
    print(f"reading_stream_full.json: {len(stream)} words "
          f"(counts {min(payload['counts'].values())}.."
          f"{max(payload['counts'].values())})")

    checks = json.loads((FIX / "checksums.json").read_text(
        encoding="utf-8"))
    checks["reading_stream_full.json"] = sha256(
        FIX / "reading_stream_full.json")
    (FIX / "checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print("checksums.json: appended reading_stream_full.json")


if __name__ == "__main__":
    main()
