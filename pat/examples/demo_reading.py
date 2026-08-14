"""W-4: the reading demo — the creature learns to read, out loud.

Born with 15 bases, it reads the pinned stream (5 epochs — long enough
for the metabolism to show a certified prune), reports what reading
did to it (taught / deferred / unlocked / pruned-with-receipt /
self-census), then answers for itself: a read-taught base with
provenance, an unlocked word crediting its stem, one homophone verdict
in plain language, one refusal, and the ledger totals. Under 60 s.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import Agent

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"

t0 = time.time()
fx = json.loads((FIX / "reading_stream.json").read_text(encoding="utf-8"))

with tempfile.TemporaryDirectory() as store:
    agent = Agent(store, seed_bases=fx["seeds"])
    print(f"born knowing {len(agent.known)} bases "
          f"({', '.join(fx['seeds'][:5])}, ...)")

    report = agent.read(fx["stream"][:5000], epochs=5, epoch_size=1000,
                        counts=fx["counts"])
    session = agent.reading
    snap = report["snapshots"][-1]
    print(f"\nread 5,000 words in 5 epochs: taught "
          f"{snap['known'] - 15 + snap['pruned']}, "
          f"deferred {snap['deferred']}, unlocked {snap['unlocked']}, "
          f"pruned {snap['pruned']}, self-census {snap['census']}")
    if session.unlocked:
        u = session.unlocked[0]
        print(f"  first unlock: '{u['word']}' — {u['unlocked_by']} "
              f"({u['verdict']})")
    if session.retired:
        w, entry = next(iter(session.retired.items()))
        print(f"  a certified prune: '{w}' — {entry['provenance']}")
    if session.census:
        c = session.census[0]
        print(f"  a census entry: '{c['word']}' shares a shape with "
              f"'{c['collides_with']}'")

    read_base = next(w for w, p in session.known.items()
                     if p.startswith("read"))
    unlocked_word = (session.unlocked[0]["word"] if session.unlocked
                     else None)
    homo = next((h for h in session.homophones if h["mode"] == "BOUND"
                 and h["surface"]), None)

    print("\n— and now, asked directly —")
    for line in agent.respond(f"know {read_base}").lines():
        print(f"  {line}")
    if unlocked_word:
        for line in agent.respond(f"analyze {unlocked_word}").lines():
            print(f"  {line}")
    if homo:
        for line in agent.respond(f"analyze {homo['word']}").lines():
            print(f"  {line}")
    for line in agent.respond("analyze brillig").lines():
        print(f"  {line}")

    # L-4: the schooled act — the creature studies a page aloud
    from mirror.config import DATA_DIR as MIRROR_DATA
    sr = agent.study(MIRROR_DATA / "page_irregular_plurals.txt")
    print(f"\n— then it studies a page —")
    print(f"  '{sr['page']}': {sr['lines']} lines read; "
          f"{sr['conflicts']} conflicts with what I'd inferred; "
          f"corrections ledgered")
    num, prov = session.number_of("men")
    conflict = next(c for c in session.lesson_conflicts
                    if c["word"] == "men")
    print(f"  asked 'is men singular or plural?': {num} — the lesson "
          f"says so ({prov}); I had inferred "
          f"{conflict['induced_says'].split(':')[1]} from men+s")

    totals = session.provenance_totals()
    print(f"\nprovenance ledger: {totals}")

print(f"\ndone in {time.time() - t0:.1f}s  (target < 60s)")
