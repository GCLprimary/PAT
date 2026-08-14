"""
make_corpus.py — grab the Brown corpus and write data/corpus.txt in the ElfIX
running-text contract: one sentence per line, lowercased, punctuation stripped,
words space-separated, UTF-8. Internal apostrophes kept (CMU has contractions).
"""
from __future__ import annotations
import re, argparse
from pathlib import Path
import nltk
from nltk.corpus import brown

_KEEP = re.compile(r"[^a-z']")

def norm(tok: str) -> str:
    return _KEEP.sub("", tok.lower()).strip("'")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/corpus.txt")
    ap.add_argument("--categories", nargs="*", default=None)
    ap.add_argument("--min-len", type=int, default=3)
    ap.add_argument("--cmu", default=None, help="optional: report CMU coverage")
    args = ap.parse_args()

    try:
        nltk.data.find("corpora/brown")
    except LookupError:
        nltk.download("brown", quiet=True)

    sents = brown.sents(categories=args.categories) if args.categories else brown.sents()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)

    n_sent = n_word = 0
    cmu = None
    if args.cmu:
        cmu = set()
        for line in Path(args.cmu).read_text(encoding="utf-8", errors="ignore").splitlines():
            if "\t" in line:
                w = line.split("\t", 1)[0]
                if "(" not in w:
                    cmu.add(w)
    oov = 0
    with out.open("w", encoding="utf-8") as f:
        for sent in sents:
            pieces = []
            for t in sent:
                pieces.extend(re.split(r"[-/]", t))
            toks = [norm(t) for t in pieces]
            toks = [t for t in toks if t]
            if len(toks) < args.min_len:
                continue
            f.write(" ".join(toks) + "\n")
            n_sent += 1; n_word += len(toks)
            if cmu is not None:
                oov += sum(1 for t in toks if t not in cmu)

    print(f"wrote {out}: {n_sent:,} sentences, {n_word:,} words")
    if cmu is not None:
        print(f"CMU coverage: {100*(1-oov/max(1,n_word)):.1f}%  (OOV {oov:,}/{n_word:,})")

if __name__ == "__main__":
    main()
