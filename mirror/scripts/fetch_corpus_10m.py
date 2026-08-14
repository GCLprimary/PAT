"""C-1: assemble the 10M single-register corpus (builder-executed).

Sourcing policy (the spec's): single-register coherent text — the
Gutenberg finding governs — assembled locally to 10.0M ± 0.2M words,
BabyLM-legal (Project Gutenberg is a BabyLM source class), pinned as
data/corpus_10m.txt with md5+sha256 in a manifest. The 5.2M
corpus_big stays pinned and untouched; every existing battery keeps
its vintage.

The register: long-form 19th/early-20th-century narrative fiction
(one register, many hands), the same class Gutenberg's offsets won
with in Part II. Book list pinned below by Gutenberg ID, fetched from
the public cache, headers stripped, normalized under the EXACT ElfIX
data contract mirror.meaning uses (punkt sentences, wordpunct tokens,
[-/] splits, [a-z'] keep, min length 3). Accumulation stops inside
the target window; the last book is truncated at a sentence boundary
to land at 10.0M.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror.config import DATA_DIR

# pinned: (gutenberg_id, title) — long single-register narrative fiction
BOOKS = [
    (2600, "War and Peace"), (135, "Les Miserables"),
    (1184, "The Count of Monte Cristo"), (996, "Don Quixote"),
    (145, "Middlemarch"), (766, "David Copperfield"),
    (1023, "Bleak House"), (1399, "Anna Karenina"),
    (28054, "The Brothers Karamazov"), (599, "Vanity Fair"),
    (2554, "Crime and Punishment"), (2701, "Moby Dick"),
    (5231, "The Way We Live Now"), (6593, "The History of Tom Jones"),
    (580, "The Pickwick Papers"), (967, "Nicholas Nickleby"),
    (968, "Martin Chuzzlewit"), (821, "Dombey and Son"),
    (963, "Little Dorrit"), (883, "Our Mutual Friend"),
    (1260, "Jane Eyre"), (110, "Tess of the d'Urbervilles"),
    (768, "Wuthering Heights"), (2833, "The Portrait of a Lady"),
    (4274, "Wives and Daughters"), (4276, "North and South"),
    (2638, "The Idiot"), (5140, "He Knew He Was Right"),
    (155, "The Moonstone"), (583, "The Woman in White"),
    (143, "The Mayor of Casterbridge"), (122, "The Return of the Native"),
    (1400, "Great Expectations"), (730, "Oliver Twist"),
    (345, "Dracula"),
]
TARGET = 10_000_000
LO, HI = 9_800_000, 10_200_000
_KEEP = re.compile(r"[^a-z']")
START_RE = re.compile(r"\*\*\* ?START OF (THE|THIS) PROJECT", re.I)
END_RE = re.compile(r"\*\*\* ?END OF (THE|THIS) PROJECT", re.I)


def fetch(book_id):
    urls = (f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt")
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            continue
    raise RuntimeError(f"could not fetch book {book_id}")


def strip_gutenberg(text):
    lines = text.splitlines()
    start = 0
    end = len(lines)
    for i, ln in enumerate(lines):
        if START_RE.search(ln):
            start = i + 1
        elif END_RE.search(ln):
            end = i
            break
    return "\n".join(lines[start:end])


def contract_sentences(text):
    """The ElfIX data contract, replicated from mirror.meaning."""
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    from nltk.tokenize import sent_tokenize, wordpunct_tokenize
    out = []
    for sent in sent_tokenize(text):
        pieces = []
        for t in wordpunct_tokenize(sent):
            pieces.extend(re.split(r"[-/]", t))
        toks = [_KEEP.sub("", t.lower()).strip("'") for t in pieces]
        toks = [t for t in toks if t]
        if len(toks) >= 3:
            out.append(toks)
    return out


def main():
    out_path = DATA_DIR / "corpus_10m.txt"
    total = 0
    used = []
    with open(out_path, "w", encoding="utf-8") as f:
        for book_id, title in BOOKS:
            if total >= TARGET:
                break
            raw = strip_gutenberg(fetch(book_id))
            sents = contract_sentences(raw)
            wrote = 0
            for toks in sents:
                if total >= TARGET:
                    break
                f.write(" ".join(toks) + "\n")
                total += len(toks)
                wrote += len(toks)
            used.append({"id": book_id, "title": title, "words": wrote})
            print(f"  {book_id:6d} {title[:38]:38s} +{wrote:8,d} "
                  f"-> {total:10,d}", flush=True)
            time.sleep(1.0)                    # polite pacing
    assert LO <= total <= HI, f"landed at {total} words"

    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            md5.update(chunk)
            sha.update(chunk)
    manifest = {
        "corpus_10m.txt": {"words": total, "md5": md5.hexdigest(),
                           "sha256": sha.hexdigest()},
        "register": "long-form public-domain narrative fiction "
                    "(Project Gutenberg; BabyLM-legal source class)",
        "books": used,
        "contract": "ElfIX data contract (punkt sentences, wordpunct "
                    "tokens, [-/] splits, [a-z'] keep, min length 3)",
    }
    (DATA_DIR / "fixtures" / "corpus_10m_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"\ncorpus_10m.txt: {total:,} words from {len(used)} books; "
          f"manifest pinned")


if __name__ == "__main__":
    main()
