"""Checkpointed full-corpus verification of the two headline gates.

Uses the repo's OWN functions (learn_bpe merge loop semantics, score, score_multi,
geometry variants) — nothing reimplemented except incremental checkpointing.
Fidelity note: BPE here is greedy+deterministic, so merges[:m] from one long run
equals learn_bpe(corpus, m) exactly; we learn 800 merges once and score prefixes.
Run repeatedly; each run resumes and does <= BUDGET seconds of merge work.
"""
import pickle, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import os
CKPT = Path(os.environ.get("VCKPT", "/tmp/verify_ckpt"))
CKPT.mkdir(exist_ok=True)
BUDGET = 85
MAX_MERGES = 800

from elfix.data_io import load_cmu, build_morpheme_gold
from elfix.syllable import build_syllable_gold
from elfix.emergent.emergent_unit import (
    geometry_boundaries, geometry_boundaries_emergent, discover, auto_quanta,
    syllable_boundaries)
from elfix.emergent.appendix import discover_appendices, geometry_boundaries_additive
from elfix.trajectory.trajectory import Trajectory
from scripts.milestone1 import bpe_boundaries, score
from scripts.syllable_eval import score_multi


def stage(name, fn):
    p = CKPT / f"{name}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    t0 = time.time()
    val = fn()
    p.write_bytes(pickle.dumps(val))
    print(f"[stage done] {name} ({time.time()-t0:.0f}s)")
    return val


def main():
    cmu = load_cmu(Path(__file__).parent/"data"/os.environ["VCMU"]) if os.environ.get("VCMU") else load_cmu()
    corpus = list(cmu.values())

    # ── incremental BPE merges (repo loop verbatim, checkpointed) ──
    mp = CKPT / "merges.pkl"
    if mp.exists():
        seqs, merges = pickle.loads(mp.read_bytes())
    else:
        seqs, merges = [list(w) for w in corpus if len(w) > 1], []
    t0 = time.time()
    while len(merges) < MAX_MERGES and time.time() - t0 < BUDGET:
        pairs = Counter()
        for s in seqs:
            for a, b in zip(s, s[1:]):
                pairs[(a, b)] += 1
        if not pairs:
            break
        (x, y), _ = pairs.most_common(1)[0]
        merges.append((x, y))
        merged = x + "\u2063" + y
        new = []
        for s in seqs:
            out, i = [], 0
            while i < len(s):
                if i < len(s) - 1 and s[i] == x and s[i + 1] == y:
                    out.append(merged); i += 2
                else:
                    out.append(s[i]); i += 1
            new.append(out)
        seqs = new
    mp.write_bytes(pickle.dumps((seqs, merges)))
    print(f"merges: {len(merges)}/{MAX_MERGES}")
    if len(merges) < MAX_MERGES:
        print("== re-run to continue ==")
        return

    # ── geometry sides (cheap-ish, each its own checkpoint) ──
    syl_gold = stage("syl_gold", lambda: build_syllable_gold(cmu))
    g_syl = stage("g_syl", lambda: score_multi(syl_gold, syllable_boundaries))
    m_gold = stage("m_gold", lambda: build_morpheme_gold(cmu))
    g_m1 = stage("g_m1", lambda: score(m_gold, geometry_boundaries))
    quanta = stage("quanta", lambda: auto_quanta([Trajectory.of(w) for w in corpus]))
    inv = stage("inv", lambda: discover(corpus, quanta=quanta))
    eb = stage("eb", lambda: score(m_gold, lambda ph: geometry_boundaries_emergent(
        ph, inv, quanta, both_sides=True)))
    appendix = stage("appendix", lambda: discover_appendices(corpus))
    ad = stage("ad", lambda: score(m_gold, lambda ph: geometry_boundaries_additive(
        ph, appendix)))

    # ── BPE prefix scoring at each m, per-m checkpoints ──
    for m in (20, 30, 50, 100, 200, 400, 800):
        pref = merges[:m]
        stage(f"bpe_syl_{m}", lambda: score_multi(
            syl_gold, lambda ph: bpe_boundaries(ph, pref)))
        stage(f"bpe_m1_{m}", lambda: score(
            m_gold, lambda ph: bpe_boundaries(ph, pref)))

    # ── report ──
    print("\n===== SYLLABLE (full corpus) =====")
    print(f"geometry  P {g_syl[0]:.3f}  R {g_syl[1]:.3f}  F1 {g_syl[2]:.3f}  seg/w {g_syl[3]:.2f}")
    rows = {m: pickle.loads((CKPT/f"bpe_syl_{m}.pkl").read_bytes())
            for m in (50, 100, 200, 400, 800)}
    bm = min(rows, key=lambda m: abs(rows[m][3] - g_syl[3]))
    b = rows[bm]
    print(f"BPE m={bm}  P {b[0]:.3f}  R {b[1]:.3f}  F1 {b[2]:.3f}  seg/w {b[3]:.2f}")
    for m, r in sorted(rows.items()):
        print(f"   (m={m:<3} F1 {r[2]:.3f} seg/w {r[3]:.2f})")

    print("\n===== MORPHEME / milestone1 (full corpus) =====")
    print(f"gold examples: {len(m_gold):,}  emergent units: {len(inv):,}  "
          f"quanta {quanta}  appendix shapes: {len(appendix)}")
    print(f"geometry (contour)    P {g_m1[0]:.3f}  R {g_m1[1]:.3f}  F1 {g_m1[2]:.3f}  seg/w {g_m1[3]:.2f}")
    print(f"+ emergent (subtract) P {eb[0]:.3f}  R {eb[1]:.3f}  F1 {eb[2]:.3f}  seg/w {eb[3]:.2f}")
    print(f"+ appendix (additive) P {ad[0]:.3f}  R {ad[1]:.3f}  F1 {ad[2]:.3f}  seg/w {ad[3]:.2f}")
    m1rows = {m: pickle.loads((CKPT/f"bpe_m1_{m}.pkl").read_bytes())
              for m in (20, 30, 50, 100, 200, 400, 800)}
    for tag, gran in (("contour", g_m1[3]), ("additive", ad[3])):
        mm = min(m1rows, key=lambda m: abs(m1rows[m][3] - gran))
        r = m1rows[mm]
        print(f"BPE @ {tag} gran (m={mm}): P {r[0]:.3f}  R {r[1]:.3f}  F1 {r[2]:.3f}  seg/w {r[3]:.2f}")
    best = max(g_m1[2], eb[2], ad[2])
    mm = min(m1rows, key=lambda m: abs(m1rows[m][3] - (ad[3] if best == ad[2] else g_m1[3])))
    print(f"\nTier 3 gate: {'PASS' if best >= m1rows[mm][2] else 'FAIL'} "
          f"(best geometry F1 {best:.3f} vs matched BPE {m1rows[mm][2]:.3f})")
    print("== VERIFICATION COMPLETE ==")


if __name__ == "__main__":
    main()
