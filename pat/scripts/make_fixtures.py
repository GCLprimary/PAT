"""Agent fixture generation (law 3: artifact over recipe, checksums).

Run ONCE at build time. Pins the probe-33 learning stream and the
probe-34 composition inputs as files, with sha256 checksums of the
fixtures AND the corpora they derive from. Tests read fixtures only.
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from mirror import Embedder, MeaningGeometry, Transform, mine_pairs
from mirror.config import DATA_DIR as MIRROR_DATA

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def learning_stream(byb):
    """Probe 33: 30 bases (10 known), 60 tasks, bare-before-derived."""
    rng2 = np.random.default_rng(23)
    cands = sorted([b for b, d in byb.items() if len(d) >= 2 and len(b) >= 4])
    rng2.shuffle(cands)
    bases = cands[:30]
    known0 = bases[:10]
    new = bases[10:]
    tasks = []
    for b in new:
        tasks.append(("bare", b, b))
    for b in bases:
        for sfx, w in list(byb[b].items())[:2]:
            tasks.append(("derived", b, w))
    rng2.shuffle(tasks)
    seen, ordered = set(), []
    deferred = defaultdict(list)
    for t in tasks:
        kind, b, w = t
        if kind == "derived" and b in new and b not in seen:
            deferred[b].append(t)
            continue
        ordered.append(t)
        if kind == "bare":
            seen.add(b)
            ordered += deferred.pop(b, [])
    return {"bases": bases, "known0": known0,
            "tasks": [list(t) for t in ordered[:60]]}


def composition_inputs(byb, geometry):
    """Probe 34: inputs of 1..6 clauses, aliens, teach->use threads —
    the rng consumption replicated verbatim."""
    rng = np.random.default_rng(31)
    cands = sorted([b for b, d in byb.items() if len(d) >= 2 and len(b) >= 4])
    rng.shuffle(cands)
    bases = cands[:40]
    known0 = bases[:15]
    teachable = bases[15:]
    meanw = [w for w in ("water", "music", "school", "church", "river",
                         "fire", "road", "heart") if w in geometry]

    def make_input(k):
        clauses, gold = [], []
        alien_at = rng.integers(0, k) if rng.random() < 0.25 else -1
        teach_pair = None
        if k >= 3 and rng.random() < 0.5:
            b = teachable[rng.integers(len(teachable))]
            forms = list(byb[b].items())
            if forms:
                i = rng.integers(0, k - 1)
                teach_pair = (i, b, forms[0][1], forms[0][0])
        for i in range(k):
            if i == alien_at:
                w = meanw[rng.integers(len(meanw))]
                verb = "translate" if rng.random() < .5 else "rhyme"
                clauses.append(f"{verb} {w}")
                gold.append(["ALIEN"])
                continue
            if teach_pair and i == teach_pair[0]:
                clauses.append(f"remember {teach_pair[1]}")
                gold.append(["LEARNED", teach_pair[1]])
                continue
            if teach_pair and i == teach_pair[0] + 1 + rng.integers(
                    0, max(1, k - teach_pair[0] - 1)) and i > teach_pair[0]:
                clauses.append(f"analyze {teach_pair[2]}")
                gold.append(["DERIVED", teach_pair[1], teach_pair[3]])
                teach_pair = None
                continue
            r = rng.random()
            if r < 0.4:
                b = bases[rng.integers(15)]
                forms = list(byb[b].items())
                sfx, w = forms[rng.integers(len(forms))]
                clauses.append(f"analyze {w}")
                gold.append(["DERIVED", b, sfx])
            elif r < 0.6:
                w = meanw[rng.integers(len(meanw))]
                clauses.append(f"relates to {w}")
                gold.append(["NEIGHBORS"])
            elif r < 0.8:
                b = bases[rng.integers(15)]
                clauses.append(f"know {b}")
                gold.append(["YES", b])
            else:
                b = teachable[rng.integers(len(teachable))]
                clauses.append(f"remember {b}")
                gold.append(["LEARNEDOK", b])
        return clauses, gold

    inputs = []
    for k in range(1, 7):
        for _ in range(12):
            clauses, gold = make_input(k)
            inputs.append({"k": k, "clauses": clauses, "gold": gold})
    threads = sum(1 for inp in inputs for gd in inp["gold"]
                  if gd[0] == "DERIVED" and gd[1] in teachable)
    return {"known0": known0, "teachable": teachable, "inputs": inputs,
            "teach_use_threads": threads}


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    emb = Embedder()
    g = MeaningGeometry()
    # the SHUFFLED pair order is part of the probe protocol (probes 33/34
    # exec probe19, whose module-level pairs are shuffled in place) —
    # byb's per-base suffix order determines the teach-pair forms
    tr = Transform(emb).fit(mine_pairs(emb.corpus))
    byb = defaultdict(dict)
    for base, sfx, w, _ in tr.pairs:
        byb[base][sfx] = w

    stream = learning_stream(byb)
    (FIX / "learning_stream.json").write_text(
        json.dumps(stream, indent=1), encoding="utf-8")
    print(f"learning_stream.json: {len(stream['tasks'])} tasks, "
          f"{len(stream['known0'])}/{len(stream['bases'])} known at start")

    comp = composition_inputs(byb, g)
    (FIX / "composition_inputs.json").write_text(
        json.dumps(comp, indent=1), encoding="utf-8")
    print(f"composition_inputs.json: {len(comp['inputs'])} inputs, "
          f"{comp['teach_use_threads']} teach->use threads")

    # relatives map (first two derived forms per base) covering every
    # base any battery or demo can touch
    all_bases = (set(stream["bases"]) | set(comp["known0"])
                 | set(comp["teachable"]))
    relatives = {b: list(byb[b].items())[:2] for b in sorted(all_bases)}
    (FIX / "relatives.json").write_text(
        json.dumps(relatives, indent=1), encoding="utf-8")

    checks = {
        "learning_stream.json": sha256(FIX / "learning_stream.json"),
        "composition_inputs.json": sha256(FIX / "composition_inputs.json"),
        "relatives.json": sha256(FIX / "relatives.json"),
        "mirror/corpus.txt": sha256(MIRROR_DATA / "corpus.txt"),
        "mirror/corpus_big.txt": sha256(MIRROR_DATA / "corpus_big.txt"),
    }
    (FIX / "checksums.json").write_text(
        json.dumps(checks, indent=1), encoding="utf-8")
    print("checksums.json written:")
    for k, v in checks.items():
        print(f"  {k}: {v[:16]}...")


if __name__ == "__main__":
    main()
