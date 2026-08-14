"""mirror workshop demo (V-4): the stage and the journey.

Act 1: read a pinned multi-topic document with editorial interruptions
aloud — watch the discourse stage HOLD through an interruption and turn
deliberately at the real topic boundary, recalling the right episode
from a_mem the whole way.

Act 2 (the crown): a topic-to-topic journey — the itinerary, four legs
of steered text, per-leg centered closure; then the REVERSED itinerary,
side by side. Ends with one refused journey, stated plainly.

Runs from a fresh checkout:  python examples/demo_workshop.py   (< 45 s)
"""
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from mirror import (CenteredSpace, DiscourseStage, Itinerary, Journey,
                    MeaningGeometry, Proposer, RawTopicSpace)
from mirror.config import DATA_DIR
from mirror.generate import load_sents
from amem.api import Memory
from amem.hooks import EpisodeHooks

FIX = DATA_DIR / "fixtures"


def main():
    t0 = time.time()
    print("loading organs...")
    g = MeaningGeometry()
    battery = json.load(open(FIX / "battery.json", encoding="utf-8"))
    raw = RawTopicSpace(g, stop=set(battery["stop"]))
    mem = Memory(grid=47, seed=99, path=str(FIX / "battery_store"),
                 autosave=False)
    hook = EpisodeHooks(mem)
    print(f"  ready in {time.time() - t0:.0f}s\n")

    print("=" * 66)
    print("ACT 1 · THE STAGE — holding through interruptions")
    print("=" * 66)
    doc = battery["docs"][0]
    cats = [battery["passages"][i]["cat"] for i in doc["segments"]]
    print(f"document: {' -> '.join(cats)}, editorial interrupters "
          f"at positions 3 and 5\n")
    stage = DiscourseStage(raw)
    for i, item in enumerate(doc["stream"]):
        v = raw.region(item["words"])
        if v is None:
            continue
        obs = stage.observe(v)
        verdict = ("TURNED" if obs.turned else
                   "held  " if obs.held else "flows ")
        gold_cat = battery["passages"][item["gold"]]["cat"]
        got = hook.recall_context(obs.state).identity
        ok = "ok " if got == battery["mids"][item["gold"]] else "MISS"
        kind = "INTERRUPT" if item["kind"] == "interrupt" else "         "
        text = " ".join(item["words"][:7])
        print(f"  [{i:2d}] {kind} {verdict}  recall {ok} ({gold_cat:15s}) "
              f"| {text}...")
    print("\n  The interrupters at [3] and [5] flow past without capturing")
    print("  the state — recall stays on the current segment. The lone")
    print("  dissonant at [12] is HELD, not obeyed. The one MISS sits at")
    print("  a segment start: the deliberate-turn lag tax, made visible.")

    print()
    print("=" * 66)
    print("ACT 2 · THE JOURNEY — topic to topic, and back")
    print("=" * 66)
    jfix = json.load(open(FIX / "journeys.json", encoding="utf-8"))
    cats_npz = np.load(FIX / "categories.npz", allow_pickle=False)
    cat_vec = {str(n): v for n, v in zip(cats_npz["names"], cats_npz["vecs"])}
    cnt = Counter()
    for line in open(DATA_DIR / "corpus.txt", encoding="utf-8"):
        cnt.update(line.split())
    space = CenteredSpace(g, stop=set(jfix["stop"]), weights=cnt)
    prop = Proposer(load_sents(DATA_DIR / "corpus_big.txt"))
    jr = Journey(prop, g, space)

    a, b = jfix["pairs"][0]
    prompt = jfix["prompts"][a][0]
    print(f"itinerary: {a} -> {b}, 4 legs; prompt: '{' '.join(prompt)}'\n")
    fwd = Itinerary(space, cat_vec[a], cat_vec[b])
    rev = Itinerary(space, cat_vec[b], cat_vec[a])
    r_fwd = jr.travel(prompt, fwd)
    r_rev = jr.travel(prompt, rev)
    print(f"FORWARD ({a} -> {b}):")
    for k, leg in enumerate(r_fwd.legs):
        print(f"  leg {k + 1}: '{' '.join(leg.tokens)}'")
        print(f"         closure ->{b} {leg.closure_to_b:+.3f}   "
              f"->{a} {leg.closure_to_a:+.3f}")
    print(f"\nREVERSED ({b} -> {a}), same prompt:")
    for k, leg in enumerate(r_rev.legs):
        print(f"  leg {k + 1}: '{' '.join(leg.tokens)}'")
        print(f"         closure ->{a} {leg.closure_to_b:+.3f}   "
              f"->{b} {leg.closure_to_a:+.3f}")
    print("\n  the text goes where the itinerary points — both ways.")

    print()
    print("=" * 66)
    print("A REFUSED JOURNEY")
    print("=" * 66)
    salad = ("piano", "gravel", "senator")
    r = jr.travel(salad, fwd)
    print(f"  prompt '{' '.join(salad)}' -> {r.status}")
    print("  I have no attested path out of this prompt. A journey needs")
    print("  a road, not just a destination — I decline to invent one.")

    print(f"\ndone in {time.time() - t0:.1f}s  (target < 45s)")


if __name__ == "__main__":
    main()
