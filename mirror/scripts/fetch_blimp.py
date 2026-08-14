"""L-2: fetch BLiMP (github.com/alexwarstadt/blimp) into data/blimp/.

Shallow-clones the benchmark repo, copies the 67 paradigm jsonl files
into data/blimp/, and writes the pinned checksum manifest
(data/fixtures/blimp_manifest.json). Run ONCE at build time — tests
never fetch (artifact law); they verify the manifest and read the
local files.
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

REPO = "https://github.com/alexwarstadt/blimp"
BLIMP_DIR = DATA_DIR / "blimp"
FIX = DATA_DIR / "fixtures"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    BLIMP_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "--depth", "1", REPO, tmp],
                       check=True)
        src = Path(tmp) / "data"
        files = sorted(src.glob("*.jsonl"))
        if len(files) != 67:
            raise SystemExit(f"expected 67 paradigm files, found "
                             f"{len(files)} — the upstream layout moved")
        for f in files:
            shutil.copyfile(f, BLIMP_DIR / f.name)
    manifest = {f.name: sha256(f)
                for f in sorted(BLIMP_DIR.glob("*.jsonl"))}
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "blimp_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"fetched {len(manifest)} paradigms into {BLIMP_DIR}")
    print(f"manifest pinned: fixtures/blimp_manifest.json")


if __name__ == "__main__":
    main()
