"""Workshop v1 fixture generation (law 4: artifact over recipe).

Run ONCE at build time; outputs are pinned into data/fixtures/ and read
by tests, which never rebuild them from NLTK. Regenerating fixtures is a
probe, not a refresh — every downstream HANDOFF number must be
re-validated if you do.

Fixtures:
  held_sentences.json   V-2 midpoint acceptance (probe-30A protocol)
  battery.json + battery_store/   V-1 interruption battery: 36 episodes
                        (6 per Brown category, real a_mem grid-47 writes,
                        centered segment centroids), 12 documents with
                        editorial interrupters at positions 3 and 5
  segdocs.json          V-1 strict segmentation regression (probe 30B)
  categories.npz + journeys.json   V-3 category vectors and attested
                        journey prompts (probe-32 protocol)
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from mirror import MeaningGeometry, Proposer
from mirror.config import DATA_DIR
from mirror.generate import load_sents
from mirror.regions import CenteredSpace

FIX = DATA_DIR / "fixtures"
CATS = ["news", "religion", "science_fiction", "romance", "government",
        "hobbies"]
INTERRUPT_CAT = "editorial"


def norm_sent(sent):
    line = " ".join(sent).lower()
    line = re.sub(r"[-]+", " ", line)
    line = re.sub(r"[^a-z' ]", "", line)
    return [w for w in line.split() if w]


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    g = MeaningGeometry()
    corpus_lines = [l.split() for l in
                    open(DATA_DIR / "corpus.txt", encoding="utf-8")]
    cnt = Counter()
    for s in corpus_lines:
        cnt.update(s)
    stop = [w for w, _ in cnt.most_common(120)]
    stop_set = set(stop)
    space = CenteredSpace(g, stop=stop_set)

    import nltk
    from nltk.corpus import brown

    def cat_sentences(cat):
        ss = [norm_sent(s) for s in brown.sents(categories=cat)]
        return [s for s in ss
                if len([w for w in s if w in g and w not in stop_set]) >= 3]

    # ── V-2: held-sentence fixture (probe-30A protocol) ──────────────
    held = [s for s in corpus_lines if len(s) >= 8][-2000:]
    keep = []
    for s in held:
        ws = [w for w in s if w in g and w not in stop_set]
        ws = list(dict.fromkeys(ws))
        if len(ws) >= 5:
            keep.append(s)
        if len(keep) >= 300:
            break
    with open(FIX / "held_sentences.json", "w", encoding="utf-8") as f:
        json.dump({"stop": stop, "sentences": keep}, f)
    print(f"held_sentences.json: {len(keep)} sentences")

    # ── V-1: interruption battery ────────────────────────────────────
    rng = np.random.default_rng(11)
    passages = []
    for c in CATS:
        ss = cat_sentences(c)
        starts = rng.choice(len(ss) - 5, 6, replace=False)
        for st in starts:
            passages.append({"cat": c, "sentences": ss[st:st + 4]})
    rng.shuffle(passages)
    passages = passages[:36]

    interrupters = cat_sentences(INTERRUPT_CAT)[:64]

    # real a_mem episodes, centered segment centroids (law 1)
    from amem import constants as AK
    from amem.api import Memory
    from amem.encoder import Encoder
    from amem.hooks import EpisodeHooks

    store = FIX / "battery_store"
    if store.exists():
        import shutil
        shutil.rmtree(store)
    # zone 2..40 (vs the probe's 2..37): centered same-category centroids
    # trigger more D-3 relocations than probe 31's raw draw and hit
    # PlacementFull at 34/36 in the narrow zone; the shape-aware filter
    # keeps LINE shapes inside grid 47 regardless. Documented in HANDOFF.
    enc = Encoder(grid=47, zone_min=2, zone_max=40,
                  min_sep=AK.PLACE_MIN_SEP, seed=0)
    # autosave off: batch the 36 writes, persist once (Windows os.replace
    # races with the file indexer under rapid successive saves)
    mem = Memory(grid=47, seed=5, path=str(store), autosave=False)
    hook = EpisodeHooks(mem, encoder=enc)
    # RAW segment centroids: the stage's thetas are calibrated on raw
    # cosines (probe 31b; see stage.py law-1 scope note), so the episode
    # bank and the stage cues live in the same raw space
    from mirror.stage import RawTopicSpace
    raw = RawTopicSpace(g, stop=stop_set)
    mids = []
    for i, p in enumerate(passages):
        emb = raw.region([w for s in p["sentences"] for w in s])
        mids.append(hook.write_episode(emb, payload_meta={"passage": i}))
    mem.library.save()
    print(f"battery_store: {len(mids)} episodes written")

    # 12 documents: 3 distinct-category segments, interrupters at
    # final positions 3 and 5
    by_cat = {}
    for i, p in enumerate(passages):
        by_cat.setdefault(p["cat"], []).append(i)
    used = set()
    docs = []
    intr_i = 0
    for d in range(12):
        cats = rng.choice(CATS, 3, replace=False)
        seg_idx = []
        for c in cats:
            free = [i for i in by_cat[c] if i not in used]
            i = free[0] if free else by_cat[c][d % 6]
            used.add(i)
            seg_idx.append(i)
        # real sentence stream with gold episode per position
        stream = []
        for si in seg_idx:
            for sent in passages[si]["sentences"]:
                stream.append({"kind": "real", "words": sent, "gold": si})
        for pos in (3, 5):        # insert at final positions 3 and 5
            gold = stream[pos - 1]["gold"]
            stream.insert(pos, {"kind": "interrupt",
                                "words": interrupters[intr_i], "gold": gold})
            intr_i += 1
        # position buckets (priority: interrupt > seg-start > post > in-seg)
        prev_gold = None
        for j, item in enumerate(stream):
            if item["kind"] == "interrupt":
                item["bucket"] = "at-interrupt"
            elif prev_gold is not None and item["gold"] != prev_gold:
                item["bucket"] = "seg-start"
            elif j > 0 and stream[j - 1]["kind"] == "interrupt":
                item["bucket"] = "post"
            elif j == 0:
                item["bucket"] = "seg-start"
            else:
                item["bucket"] = "in-seg"
            if item["kind"] == "real":
                prev_gold = item["gold"]
        docs.append({"segments": seg_idx, "stream": stream})
    with open(FIX / "battery.json", "w", encoding="utf-8") as f:
        json.dump({"stop": stop, "passages": passages, "mids": mids,
                   "docs": docs}, f)
    print(f"battery.json: {len(docs)} documents, "
          f"{sum(len(d['stream']) for d in docs)} positions")

    # ── V-1: segmentation docs (probe-30B protocol, pinned) ──────────
    rng2 = np.random.default_rng(9)
    cat_pool = {c: cat_sentences(c) for c in CATS}
    segdocs = []
    for _ in range(50):
        cats = rng2.choice(CATS, 3, replace=False)
        doc, bounds, pos = [], [], 0
        for c in cats:
            start = rng2.integers(0, len(cat_pool[c]) - 4)
            seg = cat_pool[c][start:start + 4]
            doc += seg
            pos += len(seg)
            bounds.append(pos)
        segdocs.append({"sentences": doc, "bounds": bounds[:-1]})
    with open(FIX / "segdocs.json", "w", encoding="utf-8") as f:
        json.dump({"stop": stop, "docs": segdocs}, f)
    print(f"segdocs.json: {len(segdocs)} documents")

    # ── V-3: category vectors + attested journey prompts ─────────────
    cat_vec = {}
    for c in CATS:
        ss = cat_pool[c]
        vs = [g.vec(w) for s in ss[:300] for w in s
              if w in g and w not in stop_set]
        v = np.mean(vs, axis=0)
        cat_vec[c] = v / np.linalg.norm(v)
    np.savez(FIX / "categories.npz",
             names=np.array(CATS),
             vecs=np.stack([cat_vec[c] for c in CATS]))

    stack = load_sents(DATA_DIR / "corpus_big.txt")   # the PINNED artifact
    prop = Proposer(stack)
    from mirror.generate import Generator
    gen = Generator(prop, g)
    prompts = {}
    for c in CATS:
        good = []
        for s in cat_pool[c][:400]:
            p = tuple(s[:3])
            if len(p) == 3 and gen.prompt_attested(p):
                good.append(list(p))
            if len(good) >= 2:
                break
        prompts[c] = good
    rng3 = np.random.default_rng(7)
    pairs = [[a, b] for a in CATS for b in CATS if a != b]
    rng3.shuffle(pairs)
    with open(FIX / "journeys.json", "w", encoding="utf-8") as f:
        json.dump({"pairs": pairs[:20], "prompts": prompts,
                   "stop": stop}, f)
    print(f"journeys.json: 20 pairs, prompts per category: "
          f"{ {c: len(p) for c, p in prompts.items()} }")


if __name__ == "__main__":
    main()
