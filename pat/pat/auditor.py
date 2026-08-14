"""J-1: the auditor organ (probe 56) — Pat's first job.

Pat audits the lexicons it was born from and emits RECEIPTED reports:

  A1  CMU VARIANT CANDIDATES — words whose orthography decomposes as
      stemword + known suffix spelling but whose pronunciation refuses
      the concatenation; every mismatch classed by edit-distance-1
      (elision / mutation / insertion) with the altered phone named.
      government's dropped /n/ was the demonstrated hit; this sweep
      measures the class. Subfamily annotations where mechanically
      computable: DEGEMINATION (the dropped phone equals both the
      stem's final and the tail's initial — abnormally = abnormal+ly
      losing one /l/) and VOICING-SZ (a mutation inside {s,z}); the
      probe's stress families need stress marks this lexicon does not
      carry, so those columns stay honest blanks.
  A2  UNIMORPH ADDENDA — double-locked mined pairs (pron-exact,
      ortho-exact, attested >= 5) whose (lemma, form, tag) rows the
      vendored file lacks. Onomastic hazard FLAGGED, never filtered
      (law 4): a stem on the names page rides the report with its
      flag up.
  A3  THE HOMOPHONE INDEX — the pron-group cross-reference CMU
      implies but never states.

LAW 2: A CLAIM WITHOUT ITS RECEIPT IS A CONFABULATION, EVEN IN A
REPORT. Every emitted row carries machine-checkable receipt fields;
an empty receipt field is a structural failure, not a style issue.

LAW 3: PHONE CASE IS ASSERTED AGAINST THE ARTIFACT. The mixed-case
vintage took its sixth scalp on probe 56 itself (lowercase ng vs NG,
1,858 phantom mutations); import-time, this module asserts its
suffix-tail phone set is a subset of the lexicon's actual alphabet.
"""
from collections import Counter, defaultdict
from pathlib import Path

SUFFIX_PHON = {"ment": ("m", "AH", "n", "t"), "ness": ("n", "AH", "s"),
               "less": ("l", "AH", "s"), "ly": ("l", "IY",),
               "ful": ("f", "AH", "l"), "ing": ("IH", "NG"),
               "er": ("ER",), "est": ("AH", "s", "t")}
TAGMAP = {"ed": ("V;PST", "V;V.PTCP;PST"), "ing": ("V;V.PTCP;PRS",),
          "s": ("N;PL", "V;PRS;3;SG")}
CMU_COLUMNS = ("word", "stem", "suffix", "expected_phones",
               "actual_phones", "class", "altered_phone", "subfamily")
UNI_COLUMNS = ("lemma", "form", "tags", "attested_count",
               "pron_exact", "ortho_exact", "onomastic",
               "case_evidence")
HOMO_COLUMNS = ("pron", "words", "n_words")


def assert_phone_case(corpus):
    """Law 3: the auditor's tail alphabet must live inside the
    lexicon's actual phone alphabet — no silent case vintages."""
    alphabet = {p for pron in corpus.values() for p in pron}
    tails = {p for tail in SUFFIX_PHON.values() for p in tail}
    stray = tails - alphabet
    assert not stray, \
        f"suffix-tail phones {sorted(stray)} are not in the lexicon's " \
        f"alphabet — the mixed-case vintage is back for a seventh scalp"


def edit1(a, b):
    if abs(len(a) - len(b)) > 1:
        return None
    if len(a) == len(b):
        d = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        return ("mutation", a[d[0]], b[d[0]]) if len(d) == 1 else None
    if len(a) < len(b):
        a, b, tag = b, a, "elision"
    else:
        tag = "insertion"
    for i in range(len(a)):
        if a[:i] + a[i + 1:] == b:
            return (tag, a[i], "-")
    return None


def _subfamily(kind, altered, other, stem_pron, tail):
    if kind == "elision" and stem_pron and tail \
            and altered == stem_pron[-1] and altered == tail[0]:
        return "degemination"
    if kind == "mutation" and {altered, other} == {"s", "z"}:
        return "voicing-sz"
    return ""


def audit_cmu(corpus, counts):
    """A1 -> (rows, class_counter). Probe-exact walk: first matching
    suffix spelling with an attested stem candidate (e-restoration
    included) settles the word."""
    assert_phone_case(corpus)
    rows = []
    classes = Counter()
    for w in corpus:
        if counts[w] < 3:
            continue
        for sfx, tail in SUFFIX_PHON.items():
            if not w.endswith(sfx) or len(w) - len(sfx) < 4:
                continue
            sw = w[:-len(sfx)]
            cand = [sw] + ([sw + "e"] if sw + "e" in corpus else [])
            settled = False
            for s2 in cand:
                if s2 not in corpus or counts[s2] < 3:
                    continue
                expect = tuple(corpus[s2]) + tail
                actual = tuple(corpus[w])
                if actual == expect:
                    classes["exact"] += 1
                    settled = True
                    break
                e = edit1(list(actual), list(expect))
                if e:
                    kind, altered, other = e
                    classes[kind] += 1
                    rows.append({
                        "word": w, "stem": s2, "suffix": sfx,
                        "expected_phones": " ".join(expect),
                        "actual_phones": " ".join(actual),
                        "class": kind, "altered_phone": altered,
                        "subfamily": _subfamily(
                            kind, altered, other,
                            tuple(corpus[s2]), tail),
                    })
                    settled = True
                    break
            if settled:
                break
    return rows, classes


def load_case_census(path):
    """K-1's artifact: word -> (medial_cap, medial_lower, initial_cap,
    classification). Case is a receipt, not styling (law 2)."""
    census = {}
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            w, mc, ml, ic, cls = line.rstrip("\n").split("\t")
            census[w] = (int(mc), int(ml), int(ic), cls)
    return census


def case_evidence(census, word):
    """The receipt string the case channel contributes to a row."""
    if census is None or word not in census:
        return "no-census"
    mc, ml, ic, cls = census[word]
    return f"{cls} ({mc}/{mc + ml} medial-cap, {ic} initial)"


def audit_unimorph(corpus, counts, pairs, unimorph_path, name_words,
                   case_census=None):
    """A2 -> rows: double-locked mined pairs the vendored file lacks.
    K-2: every row carries its case evidence; the onomastic flag stays
    (law 4 — flagged, never filtered) and the census now adjudicates
    it BY MEASUREMENT."""
    uni = defaultdict(set)
    with open(unimorph_path, encoding="utf-8") as f:
        for line in f:
            q = line.rstrip("\n").split("\t")
            if len(q) == 3:
                uni[q[0]].add((q[1], q[2]))
    rows = []
    for base, sfx, w, rem in pairs:
        if sfx not in TAGMAP or counts[w] < 5:
            continue
        if tuple(corpus[base]) + tuple(rem) != tuple(corpus[w]):
            continue
        have = uni.get(base, set())
        if any((w, t) in have for t in TAGMAP[sfx]):
            continue
        rows.append({
            "lemma": base, "form": w, "tags": "/".join(TAGMAP[sfx]),
            "attested_count": counts[w], "pron_exact": "yes",
            "ortho_exact": "yes",
            "onomastic": "yes" if base in name_words else "no",
            "case_evidence": case_evidence(case_census, base),
        })
    return rows


def homophone_index(corpus):
    """A3 -> rows: every pron-group with two or more distinct words."""
    groups = defaultdict(set)
    for w, p in corpus.items():
        groups[tuple(p)].add(w)
    rows = []
    for pron, words in groups.items():
        if len(words) >= 2:
            rows.append({"pron": " ".join(pron),
                         "words": "/".join(sorted(words)),
                         "n_words": len(words)})
    rows.sort(key=lambda r: (-r["n_words"], r["pron"]))
    return rows


def write_tsv(rows, columns, out_path):
    """Law 2 enforced at write time: an empty receipt field is a
    structural failure."""
    lines = ["\t".join(columns)]
    for row in rows:
        vals = []
        for c in columns:
            v = str(row[c])
            assert v != "" or c == "subfamily", \
                f"UNRECEIPTED CLAIM: empty '{c}' in {row}"
            vals.append(v)
        lines.append("\t".join(vals))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines) + "\n",
                              encoding="utf-8", newline="\n")
    return len(rows)


def organ_voice_cmu(rows, classes):
    mism = classes["elision"] + classes["mutation"] + classes["insertion"]
    degem = sum(1 for r in rows if r["subfamily"] == "degemination")
    return (f"{mism} variant candidates against "
            f"{classes['exact']} exact decompositions; every row "
            f"carries its receipt. {classes['elision']} elisions "
            f"({degem} of them the degemination family), "
            f"{classes['mutation']} mutations, "
            f"{classes['insertion']} insertions.")


def organ_voice_unimorph(rows):
    ono = sum(1 for r in rows if r["onomastic"] == "yes")
    return (f"{len(rows)} double-locked pairs the vendored file "
            f"lacks; every row pron-exact, ortho-exact, attested at "
            f"count >= 5. {ono} rows fly the onomastic flag — "
            f"hazards ride the report, never the cutting-room floor.")


def organ_voice_homophones(rows):
    biggest = rows[0] if rows else None
    return (f"{len(rows)} pronunciation groups the lexicon implies "
            f"but never states"
            + (f"; the largest shares one sound among "
               f"{biggest['n_words']} spellings ({biggest['words']})."
               if biggest else "."))
