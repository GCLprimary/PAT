"""XVI-b: build the shipped canonical store — Pat's lived session as an
artifact (F1 of the bounced front-door gate).

The protocol is demo_reading's, verbatim: born with the 15 pinned
seeds, read the pinned stream's first 5,000 words in 5 epochs (long
enough for the metabolism to show the certified prunes), study the
irregular-plurals page, save. The resulting store is what `pat` seeds
~/.pat from on a stranger's first boot: the Pat that passed the
batteries, receipts included.

Run ONCE (law 2 — the artifact is pinned; regeneration is an event):
the script refuses to overwrite an existing store, asserts the
live-log pins on the session it built, then REBOOTS an Agent from the
saved files and asserts the same pins through the restored ledgers —
the build is its own gate. Checksums land in
pat/data/fixtures/canonical_store.json.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import Agent

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "data" / "fixtures"
STORE = ROOT / "data" / "store"

SIDE_BIO = "derivable: sigh+ed; read-taught epoch 1, pruned epoch 5"


def main():
    if STORE.exists():
        print(f"REFUSE: {STORE} already exists — the canonical store is "
              f"a pinned artifact. Delete it deliberately to rebuild.")
        return 1
    fx = json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))

    agent = Agent(str(STORE), seed_bases=fx["seeds"])
    print(f"born knowing {len(agent.known)} bases")
    report = agent.read(fx["stream"][:5000], epochs=5, epoch_size=1000,
                        counts=fx["counts"])
    snap = report["snapshots"][-1]
    print(f"read: known {snap['known']}, deferred {snap['deferred']}, "
          f"unlocked {snap['unlocked']}, pruned {snap['pruned']}")

    from mirror.config import DATA_DIR as MIRROR_DATA
    sr = agent.study(MIRROR_DATA / "page_irregular_plurals.txt")
    print(f"studied '{sr['page']}': {sr['lines']} lines, "
          f"{sr['conflicts']} conflicts")
    agent.save()

    # the pins, asserted on the session just built. NOTE (flagged in
    # HANDOFF XVI-b): Part VII's engine read these 5,000 words to
    # 3348/253/254/41 — the live-log bracket line; the shipped X-4
    # dict-exact engine (its acceptance delta flagged in Part IX)
    # measures 3359/252/255/41. The canonical store is built by the
    # engine the suites gate, so ITS numbers are the pins.
    assert (snap["known"], snap["deferred"], snap["unlocked"],
            snap["pruned"]) == (3359, 252, 255, 41), snap
    assert (sr["lines"], sr["conflicts"]) == (52, 4), sr
    yes, prov = agent.reading.knows("side")
    assert yes and prov == SIDE_BIO, prov
    yes, prov = agent.reading.knows("men")
    assert yes and prov == "lesson:irregular_plurals", prov
    yes, prov = agent.reading.knows("that")
    assert yes and prov == "read: attested 54244", prov

    # rebirth: the same pins through the RESTORED ledgers
    reborn = Agent(str(STORE))
    assert reborn.reading is not None, "reading.json did not restore"
    yes, prov = reborn.reading.knows("side")
    assert yes and prov == SIDE_BIO, f"reborn: {prov}"
    yes, prov = reborn.reading.knows("men")
    assert yes and prov == "lesson:irregular_plurals", f"reborn: {prov}"
    n = reborn.bases_total()
    assert n >= 3000, n
    line = reborn.respond("verify government = govern+ment").lines()[0]
    assert line.startswith("REFUSE — pron('government')"), line
    line = reborn.respond("analyze brillig").lines()[0]
    assert line == "refuse: 'brillig' is not a form I can read", line
    print(f"rebirth verified: {n} bases, the side biography, the "
          f"government receipt, the alien refusal")

    manifest = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted(STORE.iterdir())}
    (FIX / "canonical_store.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8",
        newline="\n")
    print(f"canonical store pinned: "
          f"{ {k: v[:12] for k, v in manifest.items()} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
