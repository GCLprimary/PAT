"""X-6: vendor the word-similarity benchmark rows (probe 47).

Source: github.com/vecto-ai/word-benchmarks (word-similarity/
monolingual/en). Copies WordSim-353 (similarity and relatedness splits;
Finkelstein et al. 2001, Agirre et al. 2009) and SimLex-999 (Hill et
al. 2015) under tests/fixtures/meaning/ and pins their checksums.
Run ONCE; tests never fetch (artifact law).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mirror.config import DATA_DIR

REPO = "https://github.com/vecto-ai/word-benchmarks"
FILES = ("wordsim353-sim.csv", "wordsim353-rel.csv", "simlex999.csv")
VENDOR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" \
    / "meaning"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    VENDOR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "--depth", "1", REPO, tmp],
                       check=True)
        src = Path(tmp) / "word-similarity" / "monolingual" / "en"
        for name in FILES:
            shutil.copyfile(src / name, VENDOR / name)
    manifest = {name: sha256(VENDOR / name) for name in FILES}
    (DATA_DIR / "fixtures" / "meaning_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"vendored {len(FILES)} benchmarks under "
          f"tests/fixtures/meaning/; manifest pinned")


if __name__ == "__main__":
    main()
