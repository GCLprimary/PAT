"""E-1: vendor UniMorph English (probe 51's data). Run ONCE.

Source: github.com/unimorph/eng (UniMorph 4.0 English; CC BY-SA 3.0 —
attribution: UniMorph project, Kirov et al. 2018 / Batsuren et al.
2022). Copies the `eng` lemma\tform\ttag file to data/unimorph_eng.tsv
and pins its checksum. UniMorph is DATA, never a lesson source — no
page may be authored from it (law of the library, restated in E-1).
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

REPO = "https://github.com/unimorph/eng"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "--depth", "1", REPO, tmp],
                       check=True)
        shutil.copyfile(Path(tmp) / "eng", DATA_DIR / "unimorph_eng.tsv")
    h = hashlib.sha256()
    with open(DATA_DIR / "unimorph_eng.tsv", "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    manifest = {"unimorph_eng.tsv": h.hexdigest(),
                "source": REPO, "license": "CC BY-SA 3.0"}
    (DATA_DIR / "fixtures" / "unimorph_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"vendored unimorph_eng.tsv "
          f"({(DATA_DIR / 'unimorph_eng.tsv').stat().st_size} bytes); "
          f"manifest pinned")


if __name__ == "__main__":
    main()
