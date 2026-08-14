"""L-1: pages and the LawBook (probes 42-43) — instruction as an
artifact.

A PAGE is a law-class artifact: readable rows with provenance
`lesson:<page-name>`, pinned as a data file with a checksum — the
artifact law applied to instruction. Its placement in the arbitration
ladder is exact:

  pages override induced CLASSIFICATIONS (inferences) — the number
  lexicon classing 'men' singular because men+s exists is derivation
  evidence misread as number evidence, and a page may correct it;

  pages NEVER override attested PAIRS (observations) — what was mined
  from the corpus was observed, and no lesson outranks an observation.

Every override is a ledgered conflict, and lessons never load silently:
the LawBook carries its conflict ledger from construction, and a page
known to correct the lexicon arriving with an empty ledger is itself a
failure (asserted in the tests).

Page file format (readable, one parser): lines of `X -> Y`.
  Without a `# rule:` header —
    Y in {sg, pl}  — a feature row: word X carries number Y
                     (the demonstratives / reflexives pages).
    otherwise      — a pair row: X is singular, Y its plural
                     (the irregular-plurals page).
  With a `# rule: <name>` header (X-1's minimal extension) — every row
  is a CLASS row: word X carries the literal label Y (`each ->
  strong_quant`), and the rule name is what a judge reads. Only sg/pl
  labels enter number lookups; class labels never touch them.

X-3 (law 2 of the library build): PAGES MUST PASS THE COUNTS. A page
may carry `# audit: <consonance%>` — the measured agreement of its rule
with the pinned corpus (mirror/audit.py). The LawBook REFUSES to load a
page whose audited rule scored below AUDIT_FLOOR, naming the number:
the founding precedent is the textbook class BE->ing, REFUTED at 20.2%
(be takes a disjunction — progressive/passive/predication), while
MODAL->bare is a law (98.4%) and PERF->ed strong (88.4%). Attestation
examines the teacher too.
"""
from pathlib import Path

from .agreement import number_of as induced_number_of

FEATURES = ("sg", "pl")
AUDIT_FLOOR = 30.0


class Page:
    """One readable lesson: name, rows, provenance; optionally a rule
    name (class pages) and an audited consonance number."""

    def __init__(self, name, rows, provenance=None, rule=None,
                 audit=None):
        self.name = name
        self.rows = dict(rows)
        self.provenance = provenance or f"lesson:{name}"
        self.rule = rule
        self.audit = audit
        self.n_lines = None          # set by load(); rows count otherwise

    @classmethod
    def load(cls, path):
        path = Path(path)
        name = path.stem.replace("page_", "")
        rows = {}
        rule = None
        audit = None
        n_lines = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# rule:"):
                rule = line.split(":", 1)[1].strip()
                continue
            if line.startswith("# audit:"):
                audit = float(line.split(":", 1)[1].strip().rstrip("%"))
                continue
            if not line or line.startswith("#"):
                continue
            left, arrow, right = line.partition("->")
            if not arrow:
                raise ValueError(f"{path.name}: unreadable line {line!r}")
            left, right = left.strip(), right.strip()
            n_lines += 1
            if rule is not None or right in FEATURES:
                rows[left] = right           # class row / feature row
            else:
                rows[left] = "sg"            # pair row
                rows[right] = "pl"
        page = cls(name, rows, rule=rule, audit=audit)
        page.n_lines = n_lines
        return page

    def classified(self, label):
        """The words this page puts in `label`."""
        return {w for w, c in self.rows.items() if c == label}

    def __len__(self):
        return len(self.rows)


class LawBook:
    """Pages stacked over the induced number lexicon. Wraps — does not
    modify — `agreement.number_of`: off-page words fall through to the
    induced classification unchanged."""

    def __init__(self, pages, sg_induced, pl_induced,
                 audit_floor=AUDIT_FLOOR):
        # law 2 of the library build: pages must pass the counts — an
        # audited rule below the floor is REFUSED by name and number
        for page in pages:
            if page.audit is not None and page.audit < audit_floor:
                raise ValueError(
                    f"page '{page.name}' REFUSED: its rule audited at "
                    f"{page.audit:.1f}% consonance, below the "
                    f"{audit_floor:.0f}% floor — the counts refuted "
                    f"this lesson (see mirror/audit.py)")
        self.pages = list(pages)
        self.sg_induced = sg_induced
        self.pl_induced = pl_induced
        self._page_num = {}          # word -> (number, page name)
        for page in self.pages:
            for word, num in page.rows.items():
                if num in FEATURES:
                    self._page_num.setdefault(word, (num, page.name))
        # law 2: lessons never load silently — the ledger is built at
        # construction and carried, not recomputed on request
        self.conflict_ledger = []
        for word, (num, page_name) in self._page_num.items():
            induced = induced_number_of(word, self.sg_induced,
                                        self.pl_induced)
            if induced is not None and induced != num:
                self.conflict_ledger.append(
                    (word, f"page:{num}", f"induced:{induced}",
                     page_name))

    def number_of(self, word):
        """Page-first; induced otherwise."""
        hit = self._page_num.get(word)
        if hit is not None:
            return hit[0]
        return induced_number_of(word, self.sg_induced, self.pl_induced)

    def provenance_of(self, word):
        """-> 'lesson:<page>' when a page rules this word, else None."""
        hit = self._page_num.get(word)
        return f"lesson:{hit[1]}" if hit else None

    def conflicts(self):
        """Every page entry whose induced classification disagrees:
        (word, page-says, induced-says) triples."""
        return [(w, p, i) for w, p, i, _ in self.conflict_ledger]

    def classified(self, label):
        """Words carrying `label` across every studied page."""
        out = set()
        for page in self.pages:
            out |= page.classified(label)
        return out

    def page_named(self, name):
        for page in self.pages:
            if page.name == name:
                return page
        return None

    def export(self):
        """The law, human-readable, mirroring AllomorphTable.export."""
        lines = []
        for page in self.pages:
            lines.append(f"page: {page.name}  ({len(page)} words, "
                         f"{page.provenance})")
            for word, num in sorted(page.rows.items()):
                mark = ""
                for cw, ps, is_, pn in self.conflict_ledger:
                    if cw == word and pn == page.name:
                        mark = f"   << OVERRIDES {is_}"
                        break
                lines.append(f"  {word:16s} -> {num}{mark}")
            lines.append("")
        lines.append(f"conflict ledger: {len(self.conflict_ledger)} "
                     f"overrides of induced classifications")
        for w, p, i, pn in self.conflict_ledger:
            lines.append(f"  {w:16s} {p}  over  {i}   [{pn}]")
        return "\n".join(lines)
