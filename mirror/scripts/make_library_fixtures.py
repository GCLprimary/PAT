"""Library & auditor fixture generation (X-1/X-2/X-5; probes 44-47).

SEPARATE from every other fixture script. Run ONCE at build time. Pins:
  - page checksums grown to five (fixtures/page_checksums.json);
  - the 18 new-lane paradigms VENDORED beside the 14 (32 total);
  - the library reference (fixtures/library_reference.json): 5-page
    schooled + trigram-only per paradigm, the curve, and the audit
    reference numbers — the Part IX regression baseline.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import (Embedder, LawBook, Page, Transform, TrigramScorer,
                    audit_rule, build_form_lexicon, mine_pairs, run_all,
                    BE_AUX, MODAL_AUX, PERF_AUX)
from mirror.agreement import build_number_lexicon
from mirror.blimp import BLIMP_DIR, route
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"
VENDOR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" \
    / "blimp"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi")


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

    new_lanes = [p.stem for p in sorted(BLIMP_DIR.glob("*.jsonl"))
                 if route(p.stem) in ("reflexive", "quant", "npi")]
    for name in new_lanes:
        shutil.copyfile(BLIMP_DIR / f"{name}.jsonl",
                        VENDOR / f"{name}.jsonl")
    total = len(list(VENDOR.glob("*.jsonl")))
    print(f"vendored {len(new_lanes)} new-lane paradigms "
          f"({total} total under tests/fixtures/blimp/)")

    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    sg, pl, _ = build_number_lexicon(tr.pairs)
    book = LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in PAGES], sg, pl)
    forms = build_form_lexicon(tr.pairs)
    with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
        sents = [l.split() for l in f][:60000]
    audits = {}
    for name, aux, req in (("MODAL->bare", MODAL_AUX, "bare"),
                           ("PERF->ed", PERF_AUX, "ed"),
                           ("BE->ing", BE_AUX, "ing")):
        pct, n = audit_rule(sents, aux, req, forms)
        audits[name] = [round(pct, 1), n]

    scorer = TrigramScorer()
    schooled = run_all(scorer, book)
    trigram = run_all(scorer, None)
    reference = {
        "pages": list(PAGES),
        "schooled": {k: [round(v[0], 2), v[1], round(v[2], 2)]
                     for k, v in schooled.items()},
        "trigram_only": {k: round(v[0], 2) for k, v in trigram.items()},
        "curve": {
            "pages_0": round(sum(v[0] for v in trigram.values())
                             / len(trigram), 2),
            "pages_2": 60.52,
            "pages_5": round(sum(v[0] for v in schooled.values())
                             / len(schooled), 2),
        },
        "audit_references": audits,
        "conflict_ledger": book.conflict_ledger,
    }
    (FIX / "library_reference.json").write_text(
        json.dumps(reference, indent=1), encoding="utf-8")
    print(f"library_reference.json: curve {reference['curve']}; "
          f"audits {audits}")


if __name__ == "__main__":
    main()
