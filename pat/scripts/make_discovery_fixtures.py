"""Discovery fixture generation (O-1; probe 55). Run ONCE.

Runs the full-vocabulary session, the discovery phases, and pins
discovered_suffixes.json (the checksummed artifact law 3 promises:
per suffix — tail, modal spelling, certified count, audit numbers,
spelling share — plus the mutating/bound census and every certified
pair). Appends its checksum; every existing pinned artifact stays
untouched.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import ReadingSession, discover, get_organs, write_artifact

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def main():
    organs = get_organs()
    full = json.loads((FIX / "reading_stream_full.json").read_text(
        encoding="utf-8"))
    seeds = json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))["seeds"]
    stream = full["stream"]
    session = ReadingSession(organs, seed_bases=seeds, policy=2)
    session.read(stream, epochs=6,
                 epoch_size=max(1, len(stream) // 6),
                 counts=full["counts"])
    result, retired_pairs = discover(session, stream)
    sha = write_artifact(result, retired_pairs,
                         FIX / "discovered_suffixes.json")
    checks = json.loads((FIX / "checksums.json").read_text(
        encoding="utf-8"))
    checks["discovered_suffixes.json"] = sha
    (FIX / "checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    promoted = [d["suffix"] for d in result["discovered"]]
    total = sum(len(p) for _, _, p, _ in retired_pairs)
    print(f"discovered_suffixes.json pinned ({sha[:16]}...): "
          f"promoted {promoted}, {total} certified pairs, "
          f"confabs {result['confabs']}")


if __name__ == "__main__":
    main()
