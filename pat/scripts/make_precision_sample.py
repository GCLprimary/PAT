"""J-3: generate the precision sample — the human's rung (law 5).

50 stratified rows (15 elision, 15 mutation, 10 UniMorph addenda,
5 insertion, 5 onomastic-flagged), full receipts, an EMPTY verdict
column with schema {correct, incorrect, unsure}. The >= 90% precision
clause is graded at the human gate, by the human, on this file — the
build does not self-grade. Run ONCE; deterministic (index-strided
selection, no rng).
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import get_organs
from pat.auditor import audit_cmu, audit_unimorph
from mirror import Page
from mirror.config import DATA_DIR as MIRROR_DATA

REPORTS = Path(__file__).resolve().parent.parent / "reports"
STRATA = (("elision", 15), ("mutation", 15), ("unimorph", 10),
          ("insertion", 5), ("onomastic", 5))


def stride(rows, n):
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def main():
    organs = get_organs()
    corpus = organs.embedder.corpus
    counts = Counter()
    with open(MIRROR_DATA / "corpus_big.txt", encoding="utf-8") as f:
        for line in f:
            counts.update(line.split())
    cmu_rows, _ = audit_cmu(corpus, counts)
    name_words = set(Page.load(
        MIRROR_DATA / "page_gender_names.txt").rows)
    uni_rows = audit_unimorph(corpus, counts, organs.transform.pairs,
                              MIRROR_DATA / "unimorph_eng.tsv",
                              name_words)

    header = ("stratum", "claim", "receipt", "verdict")
    out = ["\t".join(header)]
    for stratum, n in STRATA:
        if stratum in ("elision", "mutation", "insertion"):
            pool = [r for r in cmu_rows if r["class"] == stratum]
            for r in stride(pool, n):
                claim = (f"{r['word']} = {r['stem']}+{r['suffix']} "
                         f"({r['class']}: [{r['altered_phone']}])")
                receipt = (f"expected {r['expected_phones']} | actual "
                           f"{r['actual_phones']} | "
                           f"{r['subfamily'] or 'unclassed'}")
                out.append("\t".join((stratum, claim, receipt, "")))
        elif stratum == "unimorph":
            pool = [r for r in uni_rows if r["onomastic"] == "no"]
            for r in stride(pool, n):
                claim = f"UniMorph lacks: {r['lemma']} -> {r['form']}"
                receipt = (f"tags {r['tags']} | attested "
                           f"x{r['attested_count']} | pron-exact | "
                           f"ortho-exact")
                out.append("\t".join((stratum, claim, receipt, "")))
        else:
            pool = [r for r in uni_rows if r["onomastic"] == "yes"]
            for r in stride(pool, n):
                claim = (f"UniMorph lacks: {r['lemma']} -> "
                         f"{r['form']} [ONOMASTIC]")
                receipt = (f"tags {r['tags']} | attested "
                           f"x{r['attested_count']} | stem on the "
                           f"names page")
                out.append("\t".join((stratum, claim, receipt, "")))
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "precision_sample.tsv").write_text(
        "\n".join(out) + "\n", encoding="utf-8", newline="\n")
    (REPORTS / "precision_sample.README.txt").write_text(
        "The human's rung (law 5). Fill the empty `verdict` column\n"
        "with exactly one of: correct / incorrect / unsure.\n"
        "The >= 90% precision clause (ex-onomastic; onomastic subrate\n"
        "reported separately) is graded at the human gate on this\n"
        "file. The build does not self-grade.\n",
        encoding="utf-8", newline="\n")
    print(f"precision_sample.tsv: {len(out) - 1} rows "
          f"({', '.join(f'{s} {n}' for s, n in STRATA)})")


if __name__ == "__main__":
    main()
