"""J-2: the audit and verify verbs (probe 56) — Pat's first job,
spoken.

LAW 1 — THE VERB FIVE-TUPLE IS THE UNIT OF FEATURE. Both tuples, as
shipped (and printed in HANDOFF Part XIV):

  AUDIT
    name:      audit
    trigger:   `audit <target>`, target in {cmu, unimorph, homophones}
    organs:    auditor.audit_cmu / audit_unimorph / homophone_index
               over the shipped corpus artifacts + the names page
               (onomastic flags, law 4)
    refusals:  unknown target -> "refuse: I can audit cmu, unimorph,
               homophones"; every row-level hazard flagged, never
               dropped
    provenance line: the report row itself (word/stem/suffix/expected/
               actual/class/altered or lemma/form/tags/attested/
               locks/onomastic) — law 2: no empty receipt fields

  VERIFY
    name:      verify
    trigger:   `verify <word> = <base>+<suffix>`
    organs:    the oracle ladder over the mined-pair artifacts
               (pair-exact -> attested remainders -> pron prefixes)
    refusals:  unknown base / unreadable word / pron-prefix failure /
               unattested remainder — each NAMED, each carrying its
               receipt; malformed input -> named grammar refusal
    provenance line: the verdict string itself — CERTIFY/REFUSE/
               HOMOPHONE plus the phones or pair that decided it

The phrasing slot stays a slot: template lines, never chat.
"""
from collections import Counter, defaultdict
from pathlib import Path

from mirror import Page
from mirror.config import DATA_DIR as MIRROR_DATA

from .auditor import (audit_cmu, audit_unimorph, homophone_index,
                      organ_voice_cmu, organ_voice_homophones,
                      organ_voice_unimorph, write_tsv, CMU_COLUMNS,
                      HOMO_COLUMNS, UNI_COLUMNS)

AUDIT_TARGETS = ("cmu", "unimorph", "homophones")
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class Oracle:
    """The verification ladder, probe-verbatim: proposals in,
    receipts out."""

    def __init__(self, organs):
        self.corpus = organs.embedder.corpus
        self.pair_set = {(b, s): w
                         for b, s, w, _ in organs.transform.pairs}
        self.attested = defaultdict(set)
        for b, s, w, r in organs.transform.pairs:
            self.attested[s].add(tuple(r))

    def verify(self, word, base, sfx):
        """-> (verdict, line): verdict in CERTIFY/REFUSE/HOMOPHONE."""
        wp = tuple(self.corpus.get(word, ()))
        if base not in self.corpus:
            return "REFUSE", f"REFUSE — '{base}' is not a word I know"
        bp = tuple(self.corpus[base])
        if not wp:
            return "REFUSE", \
                f"REFUSE — '{word}' is not a form I can read"
        if wp[:len(bp)] != bp:
            return "REFUSE", (
                f"REFUSE — pron('{word}') does not begin with "
                f"pron('{base}') [{' '.join(wp)} vs {' '.join(bp)}]")
        rem = wp[len(bp):]
        if rem not in self.attested.get(sfx, set()):
            return "REFUSE", (
                f"REFUSE — remainder [{' '.join(rem)}] is not an "
                f"attested form of -{sfx}")
        surf = self.pair_set.get((base, sfx))
        if surf == word:
            return "CERTIFY", \
                f"CERTIFY — {base}+{sfx}, pair-exact, mined"
        if surf and tuple(self.corpus[surf]) == wp:
            return "HOMOPHONE", (
                f"HOMOPHONE — sounds exactly like {surf} "
                f"({base}+{sfx}); I cannot tell them apart by ear")
        return "CERTIFY", f"CERTIFY — {base}+{sfx}, ladder-licensed"


class AuditDesk:
    """The audit verb's organ composition; reports land in
    agent/reports/ with law-2 structural receipts."""

    def __init__(self, organs):
        self.organs = organs
        self.corpus = organs.embedder.corpus
        self._counts = None
        self._names = None

    @property
    def counts(self):
        if self._counts is None:
            c = Counter()
            with open(MIRROR_DATA / "corpus_big.txt",
                      encoding="utf-8") as f:
                for line in f:
                    c.update(line.split())
            self._counts = c
        return self._counts

    @property
    def name_words(self):
        if self._names is None:
            page = Page.load(MIRROR_DATA / "page_gender_names.txt")
            self._names = set(page.rows)
        return self._names

    @property
    def case_census(self):
        if not hasattr(self, "_census"):
            from .auditor import load_case_census
            path = MIRROR_DATA / "case_census.tsv"
            self._census = load_case_census(path) if path.exists() \
                else None
        return self._census

    def unimorph_rows(self):
        return audit_unimorph(
            self.corpus, self.counts, self.organs.transform.pairs,
            MIRROR_DATA / "unimorph_eng.tsv", self.name_words,
            case_census=self.case_census)

    def run(self, target):
        """-> (path, n_rows, organ-voice line)."""
        if target == "cmu":
            rows, classes = audit_cmu(self.corpus, self.counts)
            path = REPORTS_DIR / "audit_cmu.tsv"
            write_tsv(rows, CMU_COLUMNS, path)
            return path, len(rows), organ_voice_cmu(rows, classes)
        if target == "unimorph":
            rows = self.unimorph_rows()
            path = REPORTS_DIR / "audit_unimorph.tsv"
            write_tsv(rows, UNI_COLUMNS, path)
            return path, len(rows), organ_voice_unimorph(rows)
        rows = homophone_index(self.corpus)
        path = REPORTS_DIR / "homophone_index.tsv"
        write_tsv(rows, HOMO_COLUMNS, path)
        return path, len(rows), organ_voice_homophones(rows)

    # ── K-4: the PR drafts (drafting only — submission is the
    # human's act; a submit button is a non-goal) ────────────────────
    def draft_prs(self):
        """-> (cmu_draft_path, unimorph_draft_path, delta). The
        UniMorph draft EXCLUDES census-proper rows — exclusion by
        MEASUREMENT (K-2), not page membership; the reclassification
        delta is reported."""
        drafts = REPORTS_DIR / "pr_drafts"
        drafts.mkdir(parents=True, exist_ok=True)

        cmu_rows, classes = audit_cmu(self.corpus, self.counts)
        top = sorted(cmu_rows, key=lambda r: -self.counts[r["word"]])
        lines = [
            "# CMUdict variant candidates — receipted errata draft",
            "",
            "## Methodology",
            "Every entry below decomposes orthographically as "
            "stem + suffix spelling with both halves attested "
            "(count >= 3), yet its pronunciation refuses the "
            "concatenation by exactly one phone (edit-distance-1). "
            "Each row carries the full receipt: expected phones, "
            "actual phones, the altered phone, and the mismatch "
            "class. Nothing is asserted without its phones.",
            "",
            f"Total: {len(cmu_rows)} candidates "
            f"(elision {classes['elision']}, mutation "
            f"{classes['mutation']}, insertion "
            f"{classes['insertion']}) against {classes['exact']} "
            f"exact decompositions. Full table: "
            f"reports/audit_cmu.tsv.",
            "",
            "## Top exemplars (by corpus attestation)",
            "",
            "| word | decomposition | expected | actual | class |",
            "|---|---|---|---|---|",
        ]
        for r in top[:15]:
            lines.append(
                f"| {r['word']} | {r['stem']}+{r['suffix']} | "
                f"{r['expected_phones']} | {r['actual_phones']} | "
                f"{r['class']}"
                + (f" ({r['subfamily']})" if r['subfamily'] else "")
                + " |")
        lines += ["", "## Reproduction",
                  "```", "python -m pytest tests/test_audit.py "
                  "tests/test_case.py -q   # agent repo",
                  "```", ""]
        cmu_path = drafts / "cmudict_variants.md"
        cmu_path.write_text("\n".join(lines), encoding="utf-8",
                            newline="\n")

        uni_rows = self.unimorph_rows()
        clean = [r for r in uni_rows
                 if not r["case_evidence"].startswith("proper")]
        excluded = len(uni_rows) - len(clean)
        top_u = sorted(clean, key=lambda r: -r["attested_count"])
        lines = [
            "# UniMorph (eng) addenda — receipted draft",
            "",
            "## Methodology",
            "Every entry is a double-locked pair: the form's "
            "pronunciation extends the lemma's exactly, the spelling "
            "is the exact concatenation, and the form is attested "
            "(count >= 5) in a 5.2M-word corpus. Rows whose lemma "
            "the case census classifies PROPER (sentence-medial "
            "capitalization dominance over raw cased sources) are "
            "EXCLUDED by that measurement — not by any name list.",
            "",
            f"Total: {len(clean)} addenda rows ({excluded} excluded "
            f"as census-proper; the flags ride the full table). "
            f"Full table: reports/audit_unimorph.tsv.",
            "",
            "## Top exemplars (by attestation)",
            "",
            "| lemma | form | tags | attested | case evidence |",
            "|---|---|---|---|---|",
        ]
        for r in top_u[:15]:
            lines.append(
                f"| {r['lemma']} | {r['form']} | {r['tags']} | "
                f"x{r['attested_count']} | {r['case_evidence']} |")
        lines += ["", "## Reproduction",
                  "```", "python -m pytest tests/test_audit.py "
                  "tests/test_case.py -q   # agent repo",
                  "```", ""]
        uni_path = drafts / "unimorph_addenda.md"
        uni_path.write_text("\n".join(lines), encoding="utf-8",
                            newline="\n")
        return cmu_path, uni_path, excluded


def parse_verify(toks):
    """`verify <word> = <base>+<suffix>` -> (word, base, sfx) or None."""
    if len(toks) == 4 and toks[2] == "=" and "+" in toks[3]:
        base, _, sfx = toks[3].partition("+")
        if base and sfx:
            return toks[1].lower(), base.lower(), sfx.lower()
    return None
