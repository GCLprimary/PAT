"""A-5: the life story in one run (< 60 s).

A fresh creature knows 15 bases. It handles a six-clause input with one
alien (contained), refuses an unknown base, is taught it, analyzes its
relatives, walks a journey between two topics — then the process dies,
and a new Agent on the same store analyzes another relative of the
taught base correctly. The provenance log closes the show: everything it
knows, and how it came to know it.

Runs from a fresh checkout:  python examples/demo_creature.py
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def say(agent, text):
    print(f"> {text}")
    for line in agent.respond(text).lines():
        print(f"  {line}")


def main():
    t0 = time.time()
    print("waking the creature...")
    from pat import Agent, get_organs
    organs = get_organs()
    stream = json.loads((FIX / "learning_stream.json").read_text(
        encoding="utf-8"))
    relatives = json.loads((FIX / "relatives.json").read_text(
        encoding="utf-8"))
    comp = json.loads((FIX / "composition_inputs.json").read_text(
        encoding="utf-8"))

    store = tempfile.mkdtemp(prefix="creature_")
    seeds = comp["known0"]
    creature = Agent(store, seed_bases=seeds, organs=organs)
    print(f"  awake in {time.time() - t0:.0f}s; seeded with "
          f"{len(seeds)} bases\n")

    print("=" * 66)
    print("A SIX-CLAUSE INPUT, ONE ALIEN — contained")
    print("=" * 66)

    def modal_form(b):
        """A derived form the modal SEAM can represent (showcase pick;
        the batteries carry the full statistics, allomorphs included)."""
        for sfx, w in relatives.get(b, []):
            mod = organs.transform.modal_phon.get(sfx)
            pron_b = organs.embedder.corpus[b]
            pron_w = organs.embedder.corpus[w]
            if mod and list(pron_w[len(pron_b):]) == mod:
                return w
        return None

    b0, w0 = next((b, f) for b in seeds if (f := modal_form(b)))
    say(creature, f"analyze {w0} and relates to water and translate fire "
                  f"and know {seeds[1]} and analyze {seeds[2]} "
                  f"and relates to music")

    print()
    print("=" * 66)
    print("REFUSAL IS THE TEACHABLE MOMENT")
    print("=" * 66)
    new_b = next(b for b in stream["bases"]
                 if b not in creature.known and relatives.get(b)
                 and len(relatives[b]) >= 2)
    say(creature, f"analyze {new_b}")
    say(creature, f"remember {new_b}")
    sfx1, w1 = relatives[new_b][0]
    say(creature, f"analyze {w1}")

    print()
    print("=" * 66)
    print("A WALK BETWEEN TOPICS")
    print("=" * 66)
    say(creature, "walk church to fire")

    print()
    print("=" * 66)
    print("DEATH AND RESURRECTION")
    print("=" * 66)
    known_before = len(creature.known)
    del creature
    print(f"  the process dies. ({known_before} bases were known)")
    reborn = Agent(store, organs=organs)
    print(f"  a new Agent wakes on the same store: knows "
          f"{len(reborn.known)} bases.")
    sfx2, w2 = relatives[new_b][1]
    say(reborn, f"analyze {w2}")

    print()
    print("=" * 66)
    print("THE RECEIPTS — everything it knows, and how")
    print("=" * 66)
    for p in reborn.provenance:
        how = ("seeded at birth" if p["taught_by"] == "<seeded>" else
               f"taught by '{p['taught_by']}'" +
               (f" after refusing ('{p['refusal'][1]}')"
                if p["refusal"] else ""))
        print(f"  {p['word']:12s} {how}")

    print(f"\ndone in {time.time() - t0:.1f}s  (target < 60s)")


if __name__ == "__main__":
    main()
