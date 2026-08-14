"""M-4: the chapters demo — the metabolism, narrated.

Act 1: a mini world synthesizes into chapters (receipts conserved, by
count, out loud). Act 2: one member-cued circulation with the gate
narrating — a_mem proposes, the exact stem check identifies, and a
pruned alias answers from its stem's chapter. Coda: one drift receipt
— meaning moved, nothing pruned. Under 45 seconds.
"""
import json
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import (ChapterAddresser, Circulation, ReadingSession,
                   cells_of, get_organs, receipts_of, synthesize)
from amem.api import Memory
from mirror import Page, PhonGate
from mirror.config import DATA_DIR as MIRROR_DATA

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"

t0 = time.time()
fx = json.loads((FIX / "reading_stream.json").read_text(encoding="utf-8"))
organs = get_organs()
emb = organs.embedder

# ── Act 1: synthesis conserves receipts ──────────────────────────────
session = ReadingSession(organs, seed_bases=fx["seeds"], policy=2)
session.read(fx["stream"][:5000], epochs=5, epoch_size=1000,
             counts=fx["counts"])
session.study(Page.load(MIRROR_DATA / "page_irregular_plurals.txt"))
n_in = len(session.known) + len(session.retired)
chapters = synthesize(session)
after = receipts_of(chapters)
placed = sum(len(c.ledger) for c in chapters.values())
print(f"ACT 1 — SYNTHESIS: {n_in} receipts in, {placed} out, "
      f"{len(after)} provenance classes conserved {after}")
side = next((a for a, c in chapters.items() if "side" in c.ledger), None)
if side:
    print(f"  'side' lives in '{side}'s chapter: "
          f"\"{chapters[side].ledger['side']}\"")

# ── Act 2: a_mem proposes, the gate identifies ───────────────────────
gate = PhonGate.from_transform(organs.transform)
byb = defaultdict(dict)
for base, sfx, w, _ in organs.transform.pairs:
    byb[base][sfx] = w
fams = [(b, d) for b, d in byb.items() if len(d) >= 3][:150]
if not any(b == "sigh" for b, _ in fams):
    fams.append(("sigh", byb["sigh"]))
addr = ChapterAddresser(gate, [b for b, _ in fams], emb.corpus)
with tempfile.TemporaryDirectory() as tmp:
    mem = Memory(seed=3, path=str(Path(tmp) / "cx"), autosave=False)
    g = int(mem.grid)
    circ = Circulation(mem, gate, addr, emb)
    for b, _ in fams:
        mid = mem.write(cells_of(emb.shape_vec(emb.corpus[b]), g),
                        meta={"anchor": b})
        circ.anchor_of[mid] = b
    cue = "side"
    r = mem.recall(cue=cells_of(emb.shape_vec(emb.corpus[cue]), g))
    ranked = sorted(r.scores, key=r.scores.get, reverse=True)[:12]
    proposed = [circ.anchor_of[m] for m in ranked
                if m in circ.anchor_of]
    got, how = circ.recall_chapter(cue)
    print(f"\nACT 2 — CIRCULATION, cued by '{cue}':")
    print(f"  a_mem proposed {len(proposed)}: {proposed[:3]}...")
    print(f"  the first to pass the stem check was '{got}' ({how})")
    if side:
        print(f"  and '{cue}' lives in that chapter as a certified "
              f"alias: \"{session.retired.get(cue, {}).get('provenance', chapters[side].ledger.get(cue))}\"")

# ── Coda: one drift receipt ──────────────────────────────────────────
from mirror.meaning_rows import drift_census
fams300 = [(b, d) for b, d in byb.items() if len(d) >= 3][:200]
n, coherence, drift = drift_census(fams300, vocab_n=6000)
if drift:
    d = min(drift, key=lambda x: x["margin"])
    ch = chapters.get(d["anchor"])
    if ch is not None:
        ch.drift.append(d)
    print(f"\nCODA — one drift receipt (census: {n} checked, "
          f"coherence {coherence:.0f}%, {len(drift)} moved):")
    print(f"  '{d['word']}' was born of '{d['anchor']}'; its meaning "
          f"has moved (now nearer '{d['nearer']}', margin "
          f"{d['margin']:+.2f}) — receipt attached, nothing pruned")

print(f"\ndone in {time.time() - t0:.1f}s  (target < 45s)")
