"""Entry-card fixture generation (E-4/E-5; probes 50-53). Run ONCE.

Pins: page checksums grown to SEVEN; the two irregular_past_participle
paradigms vendored (34 total under tests/fixtures/blimp/); the
7-page harness reference (fixtures/entry_reference.json) with the
selective aggregate — Part XI's regression baseline.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import (Embedder, LawBook, Page, Transform, TrigramScorer,
                    aggregate, mine_pairs, run_all)
from mirror.agreement import build_number_lexicon
from mirror.blimp import BLIMP_DIR
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" \
    / "blimp"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi", "gender_names",
         "past_irregulars")
NEW_PARADIGMS = ("irregular_past_participle_verbs",
                 "irregular_past_participle_adjectives")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = {f"page_{n}.txt": sha256(DATA_DIR / f"page_{n}.txt")
              for n in PAGES}
    (FIX / "page_checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print(f"page_checksums.json: {len(checks)} pages pinned")

    for name in NEW_PARADIGMS:
        shutil.copyfile(BLIMP_DIR / f"{name}.jsonl",
                        VENDOR / f"{name}.jsonl")
    print(f"vendored {len(NEW_PARADIGMS)} more paradigms "
          f"({len(list(VENDOR.glob('*.jsonl')))} total)")

    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    sg, pl, _ = build_number_lexicon(tr.pairs)
    book = LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in PAGES], sg, pl)
    scorer = TrigramScorer()
    schooled = run_all(scorer, book)
    trigram = run_all(scorer, None)
    agg = aggregate(schooled)
    reference = {
        "pages": list(PAGES),
        "schooled": {k: [round(v[0], 2), v[1], round(v[2], 2)]
                     for k, v in schooled.items()},
        "trigram_only": {k: round(v[0], 2) for k, v in trigram.items()},
        "curve": {"pages_0": 56.79, "pages_2": 60.52, "pages_5": 64.79,
                  "pages_7": round(agg["forced_overall"], 2)},
        "selective": {"coverage_pct": round(agg["coverage_pct"], 1),
                      "judged_acc_pct": round(agg["judged_acc_pct"], 2),
                      "judged": agg["judged"], "total": agg["total"]},
    }
    (FIX / "entry_reference.json").write_text(
        json.dumps(reference, indent=1), encoding="utf-8")
    print(f"entry_reference.json: curve {reference['curve']}; "
          f"selective {reference['selective']}")


if __name__ == "__main__":
    main()
