"""Reading-loop fixture generation, mirror side (W-1; probes 40-41).

SEPARATE from every other fixture script on purpose. Pins the induced
allomorph table the gate consults — the checksum test compares the
import-time table against this artifact byte for byte. Run ONCE.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import AllomorphTable, Embedder
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


def serialize_table(table):
    """Canonical, deterministic serialization (signatures joined with
    '|', keys sorted) — the checksum contract."""
    payload = {}
    for sfx in sorted(table.rules):
        payload[sfx] = {
            "rules": {"|".join(sig): cls
                      for sig, cls in sorted(table.rules[sfx].items())},
            "fallback": table.fallback[sfx],
            "support": {"|".join(sig): dict(sorted(cnt.items()))
                        for sig, cnt in sorted(table.support[sfx].items())},
            "accuracy": round(table.accuracy[sfx], 6),
            "n_test": table.n_test[sfx],
        }
    return json.dumps(payload, indent=1, sort_keys=True)


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    emb = Embedder()
    table = AllomorphTable().fit(emb.corpus)
    text = serialize_table(table)
    (FIX / "allomorph_table.json").write_text(text, encoding="utf-8")
    print("allomorph_table.json pinned: " + "  ".join(
        f"-{s}: {len(table.rules[s])} signatures, "
        f"{table.accuracy[s]:.1%} held-out" for s in sorted(table.rules)))


if __name__ == "__main__":
    main()
