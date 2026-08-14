"""Depth-2 fixture generation (D-1/D-2; probe 54). Run ONCE.

Pins: page checksums re-pinned (page 7 grew ONE row — `upset ->
upset` — for the walk-left canary; flagged in HANDOFF Part XII); the
law-2 verb artifact's checksum; the measured assignment table (the
HANDOFF prints it); the full-67 depth-2 reference
(fixtures/depth2_reference.json) — Part XII's regression baseline.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror import (Embedder, LawBook, Page, Transform, TrigramScorer,
                    aggregate, mine_pairs, run_all)
from mirror.agreement import build_number_lexicon
from mirror.blimp import (BLIMP_DIR, depth2_judge, load_paradigm,
                          reflexive_judge, sv_judge, sva2_judge)
from mirror.config import DATA_DIR
from mirror.frames import verb_inventory

FIX = DATA_DIR / "fixtures"
PAGES = ("demonstratives", "irregular_plurals", "reflexives",
         "quantifiers_existential", "npi", "gender_names",
         "past_irregulars")
CONTESTED = ("principle_A_c_command", "principle_A_domain_1",
             "principle_A_domain_2", "principle_A_domain_3",
             "anaphor_number_agreement")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    checks = {f"page_{n}.txt":
              sha256_bytes((DATA_DIR / f"page_{n}.txt").read_bytes())
              for n in PAGES}
    (FIX / "page_checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print(f"page_checksums.json re-pinned ({len(checks)} pages; "
          f"page 7 carries the upset row)")

    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    sg, pl, _ = build_number_lexicon(tr.pairs)
    book = LawBook([Page.load(DATA_DIR / f"page_{n}.txt")
                    for n in PAGES], sg, pl)
    verbs = verb_inventory(tr, book.page_named("past_irregulars"))
    vhash = sha256_bytes("\n".join(sorted(verbs)).encode("utf-8"))
    (FIX / "verb_inventory.json").write_text(json.dumps(
        {"sha256": vhash, "count": len(verbs),
         "provenance": "mined bases taking -ed/-ing, their -s and "
                       "derived forms, + page_past_irregulars"},
        indent=1), encoding="utf-8")
    print(f"verb_inventory.json: {len(verbs)} forms, {vhash[:16]}...")

    scorer = TrigramScorer()

    def measure(name, judge):
        ok = n = jn = jok = 0
        for g, b in load_paradigm(BLIMP_DIR / f"{name}.jsonl"):
            pick = judge(g, b)
            if pick is not None:
                jn += 1
                jok += int(pick == "g")
            else:
                pick = scorer.pick(g, b)
            ok += int(pick == "g")
            n += 1
        return [round(ok / n * 100, 1), jn,
                round(jok / jn * 100, 1) if jn else 0.0]

    strict = reflexive_judge(book)
    deep = depth2_judge(book, verbs)
    contest = {}
    for name in CONTESTED:
        s = measure(name, strict)
        d = measure(name, deep)
        elig_s = s[2] >= 85 and s[1] > 0
        elig_d = d[2] >= 85 and d[1] > 0
        if elig_s and not elig_d:
            winner = "strict-frame"
        elif elig_d and not elig_s:
            winner = "depth-2"
        else:
            winner = "depth-2" if d[0] > s[0] else "strict-frame"
        contest[name] = {"strict_frame": s, "depth_2": d,
                         "winner": winner}
    sv = measure("irregular_plural_subject_verb_agreement_2",
                 sv_judge(book))
    s2 = measure("irregular_plural_subject_verb_agreement_2",
                 sva2_judge(book, verbs))
    contest["irregular_plural_subject_verb_agreement_2"] = {
        "sv": sv, "sva2": s2,
        "winner": "sva2" if s2[2] >= 85 and s2[0] > sv[0] else "sv"}
    (FIX / "assignment_table.json").write_text(
        json.dumps(contest, indent=1), encoding="utf-8")
    print("assignment_table.json pinned:")
    for name, row in contest.items():
        print(f"  {name}: {row['winner']}")

    schooled = run_all(scorer, book, verbs=verbs)
    agg = aggregate(schooled)
    (FIX / "depth2_reference.json").write_text(json.dumps({
        "schooled": {k: [round(v[0], 2), v[1], round(v[2], 2)]
                     for k, v in schooled.items()},
        "overall": round(agg["forced_overall"], 2),
        "selective": {"coverage_pct": round(agg["coverage_pct"], 1),
                      "judged_acc_pct": round(agg["judged_acc_pct"], 2)},
    }, indent=1), encoding="utf-8")
    print(f"depth2_reference.json: overall "
          f"{agg['forced_overall']:.2f}, selective "
          f"{agg['coverage_pct']:.1f}% @ {agg['judged_acc_pct']:.2f}%")


if __name__ == "__main__":
    main()
