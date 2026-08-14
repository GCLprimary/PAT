"""L-2: the BLiMP harness (probes 42-43) — judgment stays selective.

Forced-choice baseline: a trigram scorer (stupid backoff, alpha = 0.4)
over the PINNED corpus_big.txt (checksum asserted at construction — the
artifact law). On top, two SELECTIVE judges that emit (verdict,
judged?) so coverage is always visible:

  demonstrative_judge — the LawBook-backed taught line: a
    demonstrative's number must match its noun's, scanning an
    adjective gap of up to 3 tokens. Its number lookups are page-first,
    so the irregular-plurals page flows straight into judgment.
  sv_judge v1 — subject-verb: the two sentences differ in exactly one
    token, the difference is an s-form, and the first det-N subject
    before that token carries the number. Its strictness (single-token
    diff, determiner-launched subjects only) is a KNOWN coverage gap —
    documented here, deliberately not patched in this build; the
    frame lane owns it (irregular_plural_SVA_2's subjects carry no
    determiner, so this judge never fires there).

Forced-choice fallback exists only inside benchmark mode: when a judge
abstains, the trigram scorer picks. Selective accuracy
(accuracy-at-coverage) is reported beside every forced number.
"""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import DATA_DIR

CORPUS_BIG_SHA256 = \
    "0de0be30e1e7bcb6ee463a25113bb7dd18d6f1143633e44bc238b2c3dc5f2b20"
ALPHA = 0.4
ADJ_GAP = 3
SV_DETS = frozenset({"the", "a", "an", "this", "that", "these", "those",
                     "some", "all", "most", "many", "each"})
BLIMP_DIR = DATA_DIR / "blimp"

# the 14 agreement paradigms (vendored under tests/fixtures/blimp/)
AGREEMENT_PARADIGMS = (
    "determiner_noun_agreement_1", "determiner_noun_agreement_2",
    "determiner_noun_agreement_irregular_1",
    "determiner_noun_agreement_irregular_2",
    "determiner_noun_agreement_with_adjective_1",
    "determiner_noun_agreement_with_adj_2",
    "determiner_noun_agreement_with_adj_irregular_1",
    "determiner_noun_agreement_with_adj_irregular_2",
    "distractor_agreement_relational_noun",
    "distractor_agreement_relative_clause",
    "irregular_plural_subject_verb_agreement_1",
    "irregular_plural_subject_verb_agreement_2",
    "regular_plural_subject_verb_agreement_1",
    "regular_plural_subject_verb_agreement_2",
)


def toks(sentence):
    return re.sub(r"[^a-z' ]", "", sentence.lower()).split()


def load_paradigm(path):
    """-> [(good_sentence, bad_sentence)] from a BLiMP jsonl file."""
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            pairs.append((d["sentence_good"], d["sentence_bad"]))
    return pairs


class TrigramScorer:
    """Stupid backoff over the pinned corpus (probe-42 arithmetic:
    tri -> alpha*bi -> alpha^2*uni with the 0.1 unigram floor)."""

    def __init__(self, corpus_path=None, expect_sha256=CORPUS_BIG_SHA256):
        corpus_path = (DATA_DIR / "corpus_big.txt"
                       if corpus_path is None else Path(corpus_path))
        if expect_sha256 is not None:
            import hashlib
            h = hashlib.sha256()
            with open(corpus_path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            got = h.hexdigest()
            assert got == expect_sha256, \
                f"corpus_big checksum {got[:16]}... is not the pinned " \
                f"artifact — the baseline row would be meaningless"
        self.uni = Counter()
        self.bi = defaultdict(Counter)
        self.tri = defaultdict(Counter)
        with open(corpus_path, encoding="utf-8") as f:
            for line in f:
                ws = line.split()
                self.uni.update(ws)
                for a, b in zip(ws, ws[1:]):
                    self.bi[a][b] += 1
                for a, b, c in zip(ws, ws[1:], ws[2:]):
                    self.tri[(a, b)][c] += 1
        self.total = sum(self.uni.values())
        self._bi_tot = {k: sum(c.values()) for k, c in self.bi.items()}
        self._tri_tot = {k: sum(c.values()) for k, c in self.tri.items()}

    def logp(self, ws):
        s = 0.0
        for i, w in enumerate(ws):
            if i >= 2:
                ctx = (ws[i - 2], ws[i - 1])
                c = self.tri.get(ctx)
                if c is not None and c[w] > 0:
                    s += math.log(c[w] / self._tri_tot[ctx])
                    continue
            if i >= 1:
                c = self.bi.get(ws[i - 1])
                if c is not None and c[w] > 0:
                    s += math.log(ALPHA * c[w] / self._bi_tot[ws[i - 1]])
                    continue
            s += math.log(ALPHA * ALPHA * max(self.uni[w], 0.1)
                          / self.total)
        return s

    def pick(self, good, bad):
        return "g" if self.logp(toks(good)) >= self.logp(toks(bad)) \
            else "b"


def demonstrative_judge(lawbook):
    """The taught line as a judge: demonstrative number must match its
    noun's, adjective gap <= 3, LawBook-backed number lookups."""
    demo_page = next(p for p in lawbook.pages
                     if p.name == "demonstratives")
    demos = set(demo_page.rows)

    def viol(ws):
        for i, w in enumerate(ws[:-1]):
            if w in demos:
                for j in range(i + 1, min(i + 1 + ADJ_GAP, len(ws))):
                    n = lawbook.number_of(ws[j])
                    if n:
                        return 0 if n == demo_page.rows[w] else 1
        return None

    def judge(good, bad):
        vg, vb = viol(toks(good)), viol(toks(bad))
        if vg is None or vb is None or vg == vb:
            return None
        return "g" if vg < vb else "b"

    return judge


def sv_judge(lawbook):
    """Subject-verb v1: single-token s-form diff, first det-N subject
    before the verb (the documented coverage gap lives here)."""

    def judge(good, bad):
        dg, db = toks(good), toks(bad)
        if len(dg) != len(db):
            return None
        diffs = [i for i, (x, y) in enumerate(zip(dg, db)) if x != y]
        if len(diffs) != 1:
            return None
        i = diffs[0]
        s_g = dg[i].endswith("s") and not db[i].endswith("s")
        s_b = db[i].endswith("s") and not dg[i].endswith("s")
        if not (s_g or s_b):
            return None
        subj = None
        for k in range(len(dg) - 1):
            if dg[k] in SV_DETS and lawbook.number_of(dg[k + 1]) \
                    and k + 1 < i:
                subj = lawbook.number_of(dg[k + 1])
                break
        if subj is None:
            return None
        return "g" if (s_g == (subj == "sg")) else "b"

    return judge


# ── X-2: the library's judges (probe 45) ─────────────────────────────
REFL_OPENERS = frozenset({"the", "a", "an", "this", "that", "these",
                          "those", "most", "many", "all", "some", "no",
                          "each", "every"})
REFL_PL_HEURISTIC = frozenset({"these", "those", "most", "many", "all",
                               "some"})
EXIST_BE = frozenset({"is", "are", "was", "were"})
AUX_Q = frozenset({"has", "have", "had", "do", "does", "did", "is",
                   "are", "was", "were", "can", "could", "will",
                   "would", "should", "might"})


def _page_judge(viol_fn):
    def judge(good, bad):
        vg, vb = viol_fn(toks(good)), viol_fn(toks(bad))
        if vg is None or vb is None or vg == vb:
            return None
        return "g" if vg < vb else "b"
    return judge


def reflexive_judge(lawbook):
    """Law 1 of the library build: a page without structure is
    seduction with extra steps. The antecedent is the STRICT-FRAME
    subject (sentence-initial opener + number-known noun; each/every
    force sg) or the judge ABSTAINS — the nearest-prior-noun version
    scored 20% judged on principle_A_c_command, which is the
    recent-noun baseline wearing a page as a costume."""
    page = lawbook.page_named("reflexives")
    refl = page.rows

    def viol(ws):
        refl_w = next((w for w in ws if w in refl), None)
        if refl_w is None:
            return None
        if len(ws) >= 2 and ws[0] in REFL_OPENERS:
            n = lawbook.number_of(ws[1])
            if n is None and ws[0] in REFL_PL_HEURISTIC \
                    and ws[1].endswith("s"):
                n = "pl"
            if ws[0] in ("each", "every"):
                n = "sg"
            if n:
                return 0 if n == refl[refl_w] else 1
        return None

    return _page_judge(viol)


def existential_quant_judge(lawbook):
    """there + BE + (optional 'only') + quantifier; a page-classified
    strong quantifier in the pivot is the violation."""
    strong = lawbook.classified("strong_quant")

    def viol(ws):
        for i, w in enumerate(ws[:-2]):
            if w == "there" and ws[i + 1] in EXIST_BE:
                j = i + 2
                if ws[j] == "only":
                    j += 1
                if j >= len(ws):
                    return None
                return 1 if ws[j] in strong else 0
        return None

    return _page_judge(viol)


def npi_judge(lawbook):
    """An NPI without a licensor is the violation; both-licensed or
    both-violating pairs abstain — which is why the *scope* paradigms
    (licensor present in both sentences) report ZERO judged pairs,
    asserted as law 4's leak-proof-by-construction."""
    npis = lawbook.classified("npi")
    licensors = lawbook.classified("licensor")

    def viol(ws):
        if not any(w.strip("'") in npis for w in ws):
            return 0
        licensed = ws[0] in AUX_Q or any(
            w in licensors or w.endswith("n't") for w in ws)
        return 0 if licensed else 1

    return _page_judge(viol)


# ── E-4: diff-position judges (probes 53) — the reusable shape ───────
PPART_DETS = frozenset({"the", "a", "an", "this", "that", "these",
                        "those", "some", "every", "each", "all", "most",
                        "many", "his", "her", "its", "their", "any",
                        "no"})
PPART_AUXES = frozenset({"has", "have", "had", "is", "are", "was",
                         "were", "be", "been", "being", "get", "got"})


def _one_diff(good, bad):
    """Align the pair; exactly one differing token or None. The
    diff-judge shape: act only when the diff is the page's business."""
    ta, tb = toks(good), toks(bad)
    if len(ta) != len(tb):
        return None
    ks = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
    if len(ks) != 1:
        return None
    return ta, tb, ks[0]


def gender_judge(lawbook):
    """LAW 3's poster child: anaphor_gender sat inside the reflexive
    lane and was silently absorbed (0 judged) until this direct judge
    routed FIRST. Diff must be {himself, herself}; gender comes from
    any listed name (page 6); abstain off-list — coverage is the
    name-list dial, documented, not grown."""
    fem = lawbook.classified("f")
    masc = lawbook.classified("m")

    def judge(good, bad):
        aligned = _one_diff(good, bad)
        if aligned is None:
            return None
        ta, tb, k = aligned
        if {ta[k], tb[k]} != {"himself", "herself"}:
            return None
        gender = None
        for w in ta:
            if w in fem:
                gender = "f"
                break
            if w in masc:
                gender = "m"
                break
        if gender is None:
            return None
        want = "herself" if gender == "f" else "himself"
        return "g" if ta[k] == want else "b"

    return judge


def ppart_judge(lawbook):
    """Page 7's diff-judge: the diff is one listed verb's (past,
    participle); prenominal position (determiner immediately before,
    no auxiliary near) demands the participle; bare-verbal (no aux
    within 3 tokens) demands the past; anything else abstains."""
    page = lawbook.page_named("past_irregulars")
    pairs = {}
    for base, label in page.rows.items():
        parts = [p.strip() for p in label.split(",")]
        if len(parts) == 2 and parts[0] != parts[1]:
            pairs[base] = (parts[0], parts[1])
    pairset = {frozenset(v) for v in pairs.values()}
    pparts = {v[1] for v in pairs.values()}
    past_only = {v[0] for v in pairs.values() if v[0] != v[1]}

    def judge(good, bad):
        aligned = _one_diff(good, bad)
        if aligned is None:
            return None
        ta, tb, k = aligned
        x, y = ta[k], tb[k]
        if frozenset((x, y)) not in pairset:
            return None
        prenominal = k >= 1 and ta[k - 1] in PPART_DETS
        aux_near = any(w in PPART_AUXES
                       for w in ta[max(0, k - 3):k])
        if prenominal and not aux_near:
            want_ppart = True
        elif not aux_near:
            want_ppart = False
        else:
            return None
        x_is_ppart = x in pparts and x not in past_only
        return "g" if x_is_ppart == want_ppart else "b"

    return judge


# ── D-2 (probe 54): the depth-2 lane and the assignment law ──────────
# LAW 1: JUDGES ARE ASSIGNED PER-PARADIGM BY MEASURED PRECISION —
# winner by forced accuracy with a judged-accuracy floor of 85%. The
# assignment below is the MEASURED table (re-measured by the test,
# printed in the HANDOFF). Pinned by measurement already: c_command
# stays with the strict-frame judge (64.9 @ 87 beats depth-2's
# 53.9 @ 62.7) — c_command's antecedent IS the strict-frame subject;
# it was never depth-2's customer.
DEPTH2_ASSIGNED = frozenset({
    "principle_A_domain_1", "principle_A_domain_2",
    "principle_A_domain_3", "anaphor_number_agreement",
})
SVA2_ASSIGNED = frozenset({"irregular_plural_subject_verb_agreement_2"})


def depth2_judge(lawbook, verbs):
    """The clause organ as a judge (mirror.frames): case-preserved
    tokens in, abstention out where phi is undecidable."""
    from .frames import Depth2Resolver, case_tokens
    resolver = Depth2Resolver(lawbook, verbs)

    def judge(good, bad):
        vg = resolver.violation(case_tokens(good))
        vb = resolver.violation(case_tokens(bad))
        if vg is None or vb is None or vg == vb:
            return None
        return "g" if vg < vb else "b"

    return judge


def sva2_judge(lawbook, verbs):
    """Noun-side diff, verb-number constant: the pair differs in one
    noun's number; the verb cluster after it fixes which is right."""
    from .frames import Depth2Resolver, case_tokens
    resolver = Depth2Resolver(lawbook, verbs)

    def judge(good, bad):
        ta = [w.lower() for w in case_tokens(good)]
        tb = [w.lower() for w in case_tokens(bad)]
        if len(ta) != len(tb):
            return None
        ks = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
        if len(ks) != 1:
            return None
        k = ks[0]
        na, nb = lawbook.number_of(ta[k]), lawbook.number_of(tb[k])
        if not na or not nb or na == nb:
            return None
        vn = resolver.verb_number(ta, k + 1)
        if vn is None:
            return None
        return "g" if na == vn else "b"

    return judge


def route(name):
    """Which judge lane a paradigm rides. LAW 3 (probe 53): THE
    SPECIFIC JUDGE OUTRANKS THE GENERAL LANE — direct diff-judges take
    their paradigms BEFORE the reflexive catch-all (anaphor_gender was
    silently absorbed at 0 judged until this order was encoded).
    LAW 1 (probe 54): the depth-2 and sva2 lanes carry exactly the
    paradigms the assignment measurement gave them."""
    if name == "anaphor_gender_agreement":
        return "gender"
    if name.startswith("irregular_past_participle"):
        return "ppart"
    if name in DEPTH2_ASSIGNED:
        return "depth2"
    if name in SVA2_ASSIGNED:
        return "sva2"
    if name.startswith("determiner_noun"):
        return "dn"
    if "subject_verb" in name or name.startswith("distractor_agreement"):
        return "sv"
    if name.startswith("principle_A") or name.startswith("anaphor"):
        return "reflexive"
    if name.startswith("existential_there_quantifiers"):
        return "quant"
    if "npi" in name:
        return "npi"
    return None


def run(path, scorer, lawbook=None, verbs=None):
    """One paradigm -> (forced_acc, judged_n, judged_acc); judges fire
    only in their lane, the trigram picks whenever they abstain.
    verbs: the law-2 artifact (mirror.frames.verb_inventory) — the
    depth-2 and sva2 lanes need it and abstain entirely without it."""
    path = Path(path)
    name = path.stem
    lane = route(name) if lawbook is not None else None
    judge = None
    if lane == "dn":
        judge = demonstrative_judge(lawbook)
    elif lane == "sv":
        judge = sv_judge(lawbook)
    elif lane == "gender" and lawbook.classified("f"):
        judge = gender_judge(lawbook)
    elif lane == "ppart" and lawbook.page_named("past_irregulars"):
        judge = ppart_judge(lawbook)
    elif lane == "depth2" and verbs is not None \
            and lawbook.page_named("reflexives"):
        judge = depth2_judge(lawbook, verbs)
    elif lane == "sva2" and verbs is not None:
        judge = sva2_judge(lawbook, verbs)
    elif lane in ("depth2", "sva2"):
        judge = None                     # no artifact: whole lane abstains
    elif lane == "reflexive" and lawbook.page_named("reflexives"):
        judge = reflexive_judge(lawbook)
    elif lane == "quant" and lawbook.classified("strong_quant"):
        judge = existential_quant_judge(lawbook)
    elif lane == "npi" and lawbook.classified("npi"):
        judge = npi_judge(lawbook)
    ok = n = jok = jn = 0
    for good, bad in load_paradigm(path):
        pick = judge(good, bad) if judge else None
        if pick is not None:
            jn += 1
            jok += int(pick == "g")
        else:
            pick = scorer.pick(good, bad)
        ok += int(pick == "g")
        n += 1
    return (ok / n * 100, jn, (jok / jn * 100 if jn else 0.0))


def run_all(scorer, lawbook=None, blimp_dir=None, verbs=None):
    """Every paradigm in the directory -> {name: (forced, jn, jacc)}."""
    blimp_dir = BLIMP_DIR if blimp_dir is None else Path(blimp_dir)
    results = {}
    for path in sorted(blimp_dir.glob("*.jsonl")):
        results[path.stem] = run(path, scorer, lawbook, verbs=verbs)
    return results


def aggregate(results, pairs_per_paradigm=1000):
    """E-5: THE SELECTIVE AGGREGATE — judged coverage and judged
    accuracy over every paradigm, beside the forced overall. The entry
    card's number: judgment stays selective, and the selectivity is
    always visible."""
    total = len(results) * pairs_per_paradigm
    jn = sum(v[1] for v in results.values())
    jok = sum(round(v[1] * v[2] / 100) for v in results.values())
    return {
        "forced_overall": sum(v[0] for v in results.values())
        / len(results),
        "judged": jn, "total": total,
        "coverage_pct": jn / total * 100,
        "judged_acc_pct": (jok / jn * 100 if jn else 0.0),
    }


def table(results, baseline=None):
    """The probe-43-style table, readable — with the entry-card row
    printed EVERY run (E-5)."""
    lines = []
    agg = aggregate(results)
    lines.append(f"OVERALL ({len(results)} paradigms, forced): "
                 f"{agg['forced_overall']:.1f}%")
    lines.append(f"SELECTIVE: judged {agg['judged']}/{agg['total']} = "
                 f"{agg['coverage_pct']:.1f}% coverage @ "
                 f"{agg['judged_acc_pct']:.2f}% judged accuracy")
    for name in sorted(results):
        forced, jn, jacc = results[name]
        base = (f"{baseline[name][0]:5.1f} -> " if baseline
                and name in baseline else "")
        j = f"   (judged {jn}, {jacc:.0f}%)" if jn else ""
        lines.append(f"  {name[:46]:46s} {base}{forced:5.1f}{j}")
    return "\n".join(lines)
