"""Probe suite 9: capacity and the calibration beat.

CAPACITY
  K1: classification capacity -- library of k patterns, fresh noisy
      re-imprints classified by nearest signature; accuracy vs k.
  K2: simultaneous residency -- imprint k patterns into ONE field
      (no wipes), then cue each with half-anchors; margin vs k.
  K3: sequential interference -- after k sequential imprints, recall
      quality by age (recency curve).

CALIBRATION
  F1: measure the flat field -- plenum (uniform) field, indraw only,
      collect the instrument's self-portrait.
  F2: usefulness -- classification accuracy at max k, raw vs
      flat-field-corrected signatures.
"""
import numpy as np
from gauge import Gauge, GRID, N, C, SEED
from gauge5 import GaugeV5

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(7)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

V, D = 0.45, 0.05
LINE = [(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)]

# pattern bank: constellation at 8 positions + line at 4 -> 12 identities
bank = []
for i, (cx, cy) in enumerate([(3, 3), (15, 14), (3, 14), (14, 3),
                              (9, 3), (3, 9), (14, 9), (9, 14)]):
    bank.append((f"C{i}", SEED, cx, cy))
for i, (cx, cy) in enumerate([(2, 2), (11, 16), (2, 16), (11, 2)]):
    bank.append((f"L{i}", LINE, cx, cy))

def imprint_sig(pts, cx, cy, seed):
    e = GaugeV5(seed=seed, violence=V, decay=D, decode_amp=0.0)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    return e.sig.copy(), (e.w > 0.4).astype(float)

def make_anchors(pts, cx, cy):
    e = Gauge(False, seed=21, violence=0.0, decay=D)
    e.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        e._decay_traps("audit")
        e._sustain()
    return (e.w > 0.4)

print("building library (12 identities)...")
lib = {}
for name, pts, cx, cy in bank:
    sig, o = imprint_sig(pts, cx, cy, seed=42)
    lib[name] = dict(sig=sig, orig=o, anchors=make_anchors(pts, cx, cy),
                     pts=pts, cx=cx, cy=cy)
names_all = [b[0] for b in bank]

print()
print("=" * 68)
print("K1 · CLASSIFICATION CAPACITY — accuracy vs library size k")
print("     probes: 2 fresh seeds per identity; nearest-cosine to library")
print("=" * 68)
probe_sigs = {}
for name, pts, cx, cy in bank:
    probe_sigs[name] = [imprint_sig(pts, cx, cy, seed=s)[0] for s in (77, 101)]
print("k    accuracy   min pairwise sig cos in library")
for k in (3, 5, 8, 10, 12):
    sub = names_all[:k]
    correct = tot = 0
    for name in sub:
        for ps in probe_sigs[name]:
            pick = max(sub, key=lambda n: cos(ps, lib[n]["sig"]))
            correct += int(pick == name)
            tot += 1
    worst = min(cos(lib[a]["sig"], lib[b]["sig"])
                for i, a in enumerate(sub) for b in sub[i + 1:])
    print(f"{k:2d}   {correct}/{tot} = {correct / tot * 100:4.0f}%   max confusable pair cos: {worst:.3f}"
          .replace("max confusable pair cos", "min pairwise cos"))
# also report the most-confused pair at k=12
sub = names_all
pairs = [(cos(lib[a]["sig"], lib[b]["sig"]), a, b)
         for i, a in enumerate(sub) for b in sub[i + 1:]]
pairs.sort(reverse=True)
print(f"     most similar pair at k=12: {pairs[0][1]}~{pairs[0][2]} cos={pairs[0][0]:.3f}")

print()
print("=" * 68)
print("K2 · SIMULTANEOUS RESIDENCY — k patterns in ONE field, cue each")
print("=" * 68)
def resident_recall(k, seed=5):
    subs = names_all[:k]
    e = GaugeV5(seed=seed, violence=V, decay=D, decode_amp=0.0)
    for n in subs:
        L = lib[n]
        e.stamp(L["pts"], L["cx"], L["cy"])
        for _ in range(4):
            e.beat(write_sig=False)
    margins = []
    for n in subs:
        r = GaugeV5(seed=seed + 1, violence=V, decay=D, decode_amp=0.0)
        r.a = e.a.copy(); r.w = e.w.copy()
        cells = np.argwhere(lib[n]["anchors"])
        sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
        for y, x in sel:
            r.a[y, x] += 10.0 / N
        r._renorm()
        for _ in range(3):
            r.beat(write_sig=False)
        own = cos(r.w, lib[n]["orig"])
        others = np.mean([cos(r.w, lib[m]["orig"]) for m in subs if m != n]) if k > 1 else 0.0
        margins.append(own - others)
    return float(np.mean(margins)), float((e.w > 0.4).mean())

print("k    mean cue-margin   field defined frac")
for k in (1, 2, 3, 4, 6):
    m, f = resident_recall(k)
    print(f"{k}    {m:+.3f}           {f:.3f}")

print()
print("=" * 68)
print("K3 · SEQUENTIAL INTERFERENCE — imprint 5 in order, recall by age")
print("=" * 68)
subs = names_all[:5]
e = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
order = list(subs)
for n in order:
    L = lib[n]
    e.stamp(L["pts"], L["cx"], L["cy"])
    for _ in range(4):
        e.beat(write_sig=False)
print("age (0=newest)   survival of its trap cells   cue-margin")
for age, n in enumerate(reversed(order)):
    surv = float((e.w > 0.4)[lib[n]["orig"] > 0].mean())
    r = GaugeV5(seed=9, violence=V, decay=D, decode_amp=0.0)
    r.a = e.a.copy(); r.w = e.w.copy()
    cells = np.argwhere(lib[n]["anchors"])
    sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
    for y, x in sel:
        r.a[y, x] += 10.0 / N
    r._renorm()
    for _ in range(3):
        r.beat(write_sig=False)
    own = cos(r.w, lib[n]["orig"])
    others = np.mean([cos(r.w, lib[m]["orig"]) for m in subs if m != n])
    print(f"{age}                {surv:.2f}                        {own - others:+.3f}")

print()
print("=" * 68)
print("F1 · FLAT FIELD — plenum indraw, the instrument's self-portrait")
print("=" * 68)
fe = GaugeV5(seed=1, violence=V, decay=D, decode_amp=0.0)
fe.a[:] = 1.0 / N
fe.w[:] = 0.0
for _ in range(6):
    fe._indraw_tick(write_sig=True)
    fe._renorm()
sig_flat = fe.sig.copy()
print(f"  sig_flat (3x3): ")
print(np.round(sig_flat.reshape(3, 3) / max(sig_flat.max(), 1e-12), 3))

print()
print("=" * 68)
print("F2 · CALIBRATION USEFULNESS — classification at k=12, raw vs corrected")
print("=" * 68)
def correct(sig):
    out = np.zeros(9)
    for i in range(9):
        out[i] = sig[i] / sig_flat[i] if sig_flat[i] > 1e-12 else 0.0
    return out
for mode, fn in (("raw      ", lambda s: s), ("corrected", correct)):
    ok = tot = 0
    for name in names_all:
        for ps in probe_sigs[name]:
            pick = max(names_all, key=lambda n: cos(fn(ps), fn(lib[n]["sig"])))
            ok += int(pick == name)
            tot += 1
    print(f"  {mode}: {ok}/{tot} = {ok / tot * 100:.0f}%")
