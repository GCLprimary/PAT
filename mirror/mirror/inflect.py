"""E-1: orthographic inflection, induced (probes 51/53) — the same
organ as the phon table, one floor over.

LAW 1 (the mining projection has a shadow): string-concatenation
mining structurally cannot see non-concatenative orthography — moved
(e-deletion), making (e-deletion), stopped (doubling), carries
(y-replacement) — and a table induced from mined pairs inherits the
blindness (22-30% on exactly those classes). When a ruler's own
attested pairs exist, induce from THEM: this table is induced from the
vendored UniMorph English train split (lemma-disjoint, seed 7), never
from the miner's shadow.

The classes: {s, es, ies, ed, d, ied, Ced, ing, e_ing, Cing} — plain
attachment, e-support, y-replacement, e-deletion, and consonant
doubling, for -s / -ed / -ing families. The signature is
(CV-pattern of the penultimate two letters, final letter); the table
is argmax counts per (tag, signature); an unseen signature REFUSES.
~298 rows, printed in full in the HANDOFF — the model IS the page.

Irregulars ride pages only (page 2 plurals, page 7 pasts); UniMorph is
data, never a lesson source — no page may be authored from it. The
residue is REFUSED or wrong, never silently patched.
"""
import random
from collections import Counter, defaultdict
from pathlib import Path

from .config import DATA_DIR

UNIMORPH_PATH = DATA_DIR / "unimorph_eng.tsv"
TAGS = ("V;PST", "V;PRS;3;SG", "V;V.PTCP;PRS", "N;PL")
VOWELS = set("aeiou")
SPLIT_SEED = 7
TRAIN_FRAC = 0.8
TEST_CAP = 3000


def classify(base, form):
    """Which orthographic rule takes base -> form, or None."""
    if form == base + "s":
        return "s"
    if form == base + "es":
        return "es"
    if base.endswith("y") and form == base[:-1] + "ies":
        return "ies"
    if form == base + "ed":
        return "ed"
    if base.endswith("e") and form == base + "d":
        return "d"
    if base.endswith("y") and form == base[:-1] + "ied":
        return "ied"
    if len(base) >= 2 and form == base + base[-1] + "ed":
        return "Ced"
    if form == base + "ing":
        return "ing"
    if base.endswith("e") and form == base[:-1] + "ing":
        return "e_ing"
    if len(base) >= 2 and form == base + base[-1] + "ing":
        return "Cing"
    return None


def apply_class(base, cls):
    return {
        "s": base + "s", "es": base + "es",
        "ies": base[:-1] + "ies",
        "ed": base + "ed", "d": base + "d",
        "ied": base[:-1] + "ied",
        "Ced": base + base[-1] + "ed",
        "ing": base + "ing", "e_ing": base[:-1] + "ing",
        "Cing": base + base[-1] + "ing",
    }[cls]


def signature(base):
    """(CV-pattern of the penultimate two letters, final letter)."""
    prev = "V" if len(base) > 1 and base[-2] in VOWELS else "C"
    pprev = "V" if len(base) > 2 and base[-3] in VOWELS else "C"
    return (pprev + prev, base[-1])


def load_unimorph(path=None, tags=TAGS):
    """tag -> {lemma: form} (last row wins, the probe protocol);
    lemmas filtered to plain lowercase words of 3-12 letters."""
    path = UNIMORPH_PATH if path is None else Path(path)
    gold = {t: {} for t in tags}
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 3 and p[2] in gold:
                lemma, form = p[0], p[1]
                if lemma.isalpha() and lemma.islower() \
                        and 3 <= len(lemma) <= 12:
                    gold[p[2]][lemma] = form
    return gold


class InflectionTable:
    """tag x signature -> argmax rule class, induced from the UniMorph
    train split; selective (unseen signature refuses)."""

    def __init__(self):
        self.rules = {}          # tag -> {sig: class}
        self.support = {}        # tag -> {sig: Counter}
        self.splits = {}         # tag -> (train lemmas, test lemmas)
        self.gold = {}

    def fit(self, path=None, tags=TAGS):
        self.gold = load_unimorph(path, tags)
        for tag in tags:
            lemmas = list(self.gold[tag])
            random.Random(SPLIT_SEED).shuffle(lemmas)
            cut = int(len(lemmas) * TRAIN_FRAC)
            train = lemmas[:cut]
            test = lemmas[cut:cut + TEST_CAP]
            self.splits[tag] = (train, test)
            table = defaultdict(Counter)
            for lemma in train:
                cls = classify(lemma, self.gold[tag][lemma])
                if cls:
                    table[signature(lemma)][cls] += 1
            self.support[tag] = dict(table)
            self.rules[tag] = {sig: c.most_common(1)[0][0]
                               for sig, c in table.items()}
        return self

    def apply(self, lemma, tag, overrides=None):
        """Page-first (irregulars ride pages, law of the library), then
        the induced rule; unseen signature -> None (REFUSE)."""
        if overrides and lemma in overrides:
            return overrides[lemma]
        cls = self.rules[tag].get(signature(lemma))
        if cls is None:
            return None
        return apply_class(lemma, cls)

    def evaluate(self, tag, overrides=None):
        """-> (ok, wrong, refused, n) on the held-out lemmas."""
        _, test = self.splits[tag]
        ok = wrong = refused = 0
        for lemma in test:
            got = self.apply(lemma, tag, overrides=overrides)
            if got is None:
                refused += 1
            elif got == self.gold[tag][lemma]:
                ok += 1
            else:
                wrong += 1
        return ok, wrong, refused, len(test)

    def n_rows(self):
        return sum(len(r) for r in self.rules.values())

    def export(self):
        """The model as a page: every row, frequent-first, readable."""
        lines = []
        for tag in self.rules:
            rows = sorted(self.support[tag].items(),
                          key=lambda kv: -sum(kv[1].values()))
            lines.append(f"{tag}  ({len(rows)} signatures)")
            for sig, dist in rows:
                total = sum(dist.values())
                cls, cnt = dist.most_common(1)[0]
                lines.append(f"  {sig[0]}·{sig[1]:1s}  -> "
                             f"{cls:6s} ({cnt}/{total})")
            lines.append("")
        return "\n".join(lines)
