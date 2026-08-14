"""K-1: the case census (builder-measured; the amendment pattern).

LAW 2 OF PART XV: CASE IS A RECEIPT, NOT STYLING. Sentence-MEDIAL
capitalization is the proper-noun signal; sentence-initial capitals
are positionally ambiguous and counted separately — position-
conditioned counting, as always.

LAW 3: NEW CHANNELS RIDE PARALLEL ARTIFACTS. The pinned lowercase
corpora stay untouched at their checksums; this census is a NEW
checksummed artifact derived from the raw cased sources: the NLTK
originals of corpus_big's three registers (brown, gutenberg, reuters
— cased by vintage) plus the 35 pinned Gutenberg novels of
corpus_10m, re-fetched cased by their manifest IDs.

THE THRESHOLD IS DERIVED, NOT DECLARED: the medial-cap ratio
r = medial_cap / (medial_cap + medial_lower) is sharply bimodal; the
classification boundary is the minimum-density interior bin of the
20-bin histogram (the valley between the common mode at r~0 and the
proper mode at r~1). proper: r above the valley; common: below;
dual: inside the valley bin, or no medial evidence at all. The
histogram and the chosen valley are printed as provenance and stored
in the manifest.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror.config import DATA_DIR

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_corpus_10m import BOOKS, fetch, strip_gutenberg

_KEEP = re.compile(r"[^a-z']")


def norm(tok):
    return _KEEP.sub("", tok.lower()).strip("'")


def tally(census, sent_tokens):
    """Position-conditioned counting over one cased sentence."""
    seen_first_alpha = False
    for tok in sent_tokens:
        if not tok or not tok[0].isalpha():
            continue
        key = norm(tok)
        if not key:
            continue
        cap = tok[0].isupper()
        row = census[key]
        if not seen_first_alpha:
            if cap:
                row[2] += 1              # sentence-initial capitalized
            seen_first_alpha = True
            continue
        row[0 if cap else 1] += 1        # medial cap / medial lower
    return census


def nltk_sources(census):
    import nltk
    for cid in ("brown", "gutenberg", "reuters"):
        try:
            nltk.data.find(f"corpora/{cid}")
        except LookupError:
            nltk.download(cid, quiet=True)
        module = getattr(__import__("nltk.corpus", fromlist=[cid]), cid)
        n = 0
        for sent in module.sents():
            tally(census, sent)
            n += 1
        print(f"  {cid}: {n} cased sentences", flush=True)


def book_sources(census):
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    from nltk.tokenize import sent_tokenize, wordpunct_tokenize
    for book_id, title in BOOKS:
        raw = strip_gutenberg(fetch(book_id))
        n = 0
        for sent in sent_tokenize(raw):
            tally(census, wordpunct_tokenize(sent))
            n += 1
        print(f"  {book_id} {title[:32]}: {n} cased sentences",
              flush=True)
        time.sleep(1.0)


def derive_threshold(census):
    """The valley of the bimodal medial-cap ratio histogram."""
    bins = [0] * 20
    for mc, ml, ic in census.values():
        tot = mc + ml
        if tot == 0:
            continue
        r = mc / tot
        bins[min(19, int(r * 20))] += 1
    interior = range(2, 18)
    valley = min(interior, key=lambda i: bins[i])
    lo, hi = valley / 20, (valley + 1) / 20
    return bins, valley, lo, hi


def main():
    census = defaultdict(lambda: [0, 0, 0])
    print("NLTK cased sources:")
    nltk_sources(census)
    print("pinned Gutenberg novels, re-fetched cased:")
    book_sources(census)

    bins, valley, lo, hi = derive_threshold(census)
    print(f"\nhistogram (20 bins of medial-cap ratio): {bins}")
    print(f"valley bin {valley} -> common: r <= {lo:.2f}, proper: "
          f"r >= {hi:.2f}, dual inside (or no medial evidence)")

    rows = ["\t".join(("word", "medial_cap", "medial_lower",
                       "initial_cap", "classification"))]
    for w in sorted(census):
        mc, ml, ic = census[w]
        tot = mc + ml
        if tot == 0:
            cls = "dual"
        else:
            r = mc / tot
            cls = "proper" if r >= hi else \
                "common" if r <= lo else "dual"
        rows.append(f"{w}\t{mc}\t{ml}\t{ic}\t{cls}")
    out = DATA_DIR / "case_census.tsv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8",
                   newline="\n")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (DATA_DIR / "fixtures" / "case_census_manifest.json").write_text(
        json.dumps({"case_census.tsv": sha,
                    "types": len(census),
                    "histogram": bins, "valley_bin": valley,
                    "common_max_r": lo, "proper_min_r": hi,
                    "sources": "NLTK brown/gutenberg/reuters (cased "
                               "vintage) + the 35 corpus_10m novels "
                               "re-fetched cased"},
                   indent=1), encoding="utf-8")
    print(f"\ncase_census.tsv: {len(census)} types, sha {sha[:16]}...")


if __name__ == "__main__":
    main()
