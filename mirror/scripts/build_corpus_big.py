"""XVI-b: reconstitute corpus_big.txt from the shipped .xz (F5, slim).

corpus_big is the probe machine's bespoke import (Part IV-b, the corpus
convergence) — it is NOT rebuildable from NLTK (the registry variant
differs by hash), so the slim tree ships it compressed and this script
reconstitutes the exact bytes. Law 2: the artifact is pinned — the
decompressed file must land on the recorded sha256 or this script
deletes it and fails loudly.

Needed by: the `walk` and `audit` verbs, and the mirror/pat suites.
The REPL's other verbs (analyze, know, verify, remember, relates) boot
without it.

    python mirror/scripts/build_corpus_big.py
"""
import hashlib
import lzma
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
XZ = DATA / "corpus_big.txt.xz"
OUT = DATA / "corpus_big.txt"
SHA256 = "0de0be30e1e7bcb6ee463a25113bb7dd18d6f1143633e44bc238b2c3dc5f2b20"


def main():
    if OUT.exists():
        got = hashlib.sha256(OUT.read_bytes()).hexdigest()
        if got == SHA256:
            print(f"corpus_big.txt already built and verified "
                  f"({OUT.stat().st_size:,} bytes, sha256 {got[:12]}…)")
            return 0
        print(f"corpus_big.txt exists but sha256 {got[:12]}… != pinned "
              f"{SHA256[:12]}… — rebuilding from the shipped .xz")
    raw = lzma.decompress(XZ.read_bytes())
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA256:
        print(f"FATAL: decompressed sha256 {got} != pinned {SHA256} — "
              f"the shipped .xz does not carry the pinned artifact")
        return 1
    OUT.write_bytes(raw)
    print(f"corpus_big.txt built: {len(raw):,} bytes, "
          f"sha256 {got[:12]}… == pinned. walk, audit, and the suites "
          f"are live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
