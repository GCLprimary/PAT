"""Teach-order sweep fixture (F-3; the tie-order luck, retired).

Run ONCE at build time. Pins cell/seal plus the first two other
colliding pairs from mirror's pinned collision census (phon_gate_sets),
with each base's first two derived forms. Appends the new artifact's
checksum to checksums.json — every existing pinned artifact and its
checksum is preserved untouched (regenerating THEM is a probe this
script cannot trigger).
"""
import hashlib
import json
import sys
from collections import defaultdict
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
    byb = defaultdict(dict)
    for base, sfx, w, _ in tr.pairs:
        byb[base][sfx] = w

    census = json.loads(
        (MIRROR_DATA / "fixtures" / "phon_gate_sets.json").read_text(
            encoding="utf-8"))
    pairs = [("cell", "seal")]
    for B1, B2 in census["disamb"]:
        if {B1, B2} == {"cell", "seal"}:
            continue
        pairs.append((B1, B2))
        if len(pairs) == 3:
            break

    pinned = []
    for a, b in pairs:
        assert emb.corpus[a] != emb.corpus[b], f"{a}/{b} are homophones"
        pinned.append({
            "a": a, "b": b,
            "forms": {base: [[sfx, w] for sfx, w
                             in list(byb[base].items())[:2]]
                      for base in (a, b)},
        })
        print(f"pair {a}/{b}: " + "  ".join(
            f"{base} -> {[w for _, w in p['forms'][base]]}"
            for p, base in [(pinned[-1], a), (pinned[-1], b)]))

    (FIX / "teach_order_pairs.json").write_text(
        json.dumps({"pairs": pinned}, indent=1), encoding="utf-8")

    checks = json.loads((FIX / "checksums.json").read_text(
        encoding="utf-8"))
    checks["teach_order_pairs.json"] = sha256(
        FIX / "teach_order_pairs.json")
    (FIX / "checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print("checksums.json: appended teach_order_pairs.json "
          f"({checks['teach_order_pairs.json'][:16]}...)")


if __name__ == "__main__":
    main()
