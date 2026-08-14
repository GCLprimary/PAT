"""Schooled-twin fixture generation (L-1/L-2/L-3; probes 42-43).

SEPARATE from every other fixture script on purpose. Run ONCE at build
time. Pins:
  - the two lesson pages' checksums (fixtures/page_checksums.json);
  - the 14 agreement paradigms VENDORED under tests/fixtures/blimp/
    (artifact law — tests never fetch);
  - the battery reference values (fixtures/blimp_reference.json):
    per-paradigm forced/judged numbers with the LawBook and
    trigram-only, from one canonical run — the no-harm regression's
    baseline going forward.
Requires data/blimp/ (scripts/fetch_blimp.py, already run) and verifies
its manifest first.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import (Embedder, LawBook, Page, Transform, TrigramScorer,
                    mine_pairs, run_all)
from mirror.agreement import build_number_lexicon
from mirror.blimp import AGREEMENT_PARADIGMS, BLIMP_DIR
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" \
    / "blimp"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads((FIX / "blimp_manifest.json").read_text(
        encoding="utf-8"))
    for name, expected in manifest.items():
        assert sha256(BLIMP_DIR / name) == expected, \
            f"{name} does not match the fetched manifest"
    print(f"manifest verified: {len(manifest)} paradigms")

    pages = {
        "page_demonstratives.txt":
            sha256(DATA_DIR / "page_demonstratives.txt"),
        "page_irregular_plurals.txt":
            sha256(DATA_DIR / "page_irregular_plurals.txt"),
    }
    (FIX / "page_checksums.json").write_text(
        json.dumps(pages, indent=1), encoding="utf-8")
    print("page_checksums.json pinned:",
          {k: v[:12] + "..." for k, v in pages.items()})

    VENDOR.mkdir(parents=True, exist_ok=True)
    for name in AGREEMENT_PARADIGMS:
        shutil.copyfile(BLIMP_DIR / f"{name}.jsonl",
                        VENDOR / f"{name}.jsonl")
    print(f"vendored {len(AGREEMENT_PARADIGMS)} agreement paradigms "
          f"under tests/fixtures/blimp/")

    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    sg, pl, _ = build_number_lexicon(tr.pairs)
    book = LawBook([Page.load(DATA_DIR / "page_demonstratives.txt"),
                    Page.load(DATA_DIR / "page_irregular_plurals.txt")],
                   sg, pl)
    scorer = TrigramScorer()
    schooled = run_all(scorer, book)
    trigram = run_all(scorer, None)
    reference = {
        "schooled": {k: [round(v[0], 2), v[1], round(v[2], 2)]
                     for k, v in schooled.items()},
        "trigram_only": {k: round(v[0], 2) for k, v in trigram.items()},
        "overall_schooled": round(
            sum(v[0] for v in schooled.values()) / len(schooled), 2),
        "overall_trigram": round(
            sum(v[0] for v in trigram.values()) / len(trigram), 2),
        "conflict_ledger": book.conflict_ledger,
    }
    (FIX / "blimp_reference.json").write_text(
        json.dumps(reference, indent=1), encoding="utf-8")
    print(f"blimp_reference.json pinned: overall "
          f"{reference['overall_schooled']} schooled / "
          f"{reference['overall_trigram']} trigram; conflict ledger "
          f"{len(book.conflict_ledger)} entries")


if __name__ == "__main__":
    main()
