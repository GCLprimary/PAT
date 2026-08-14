"""Probe suite 15: D-1 encoder -- embedding -> constellation -> a_mem loop.

Encoder: project embedding onto 2 fixed random axes -> grid position;
sign of a 3rd projection -> shape. Separation (D-3): if placed < 5 Chebyshev
from an existing identity, relocate along a deterministic probe sequence.
Write: imprint at encoded placement, store radius-channel signature (V2).
Recall: noisy embedding -> encode -> imprint probe -> classify vs library.
Accuracy vs noise sigma; relocation count; encode stability.
"""
import numpy as np
from gauge import GRID, SEED
import importlib
p14 = importlib.import_module("probe14_lib") if False else None

# reuse GaugeCap by importing from probe14 without running it: inline minimal copy
exec(open("probe14.py").read().split('bank = []')[0])  # defs: cos, V, D, LINE, GaugeCap

EMB_D = 64
rng = np.random.default_rng(3)
AX = rng.normal(size=(3, EMB_D))
AX /= np.linalg.norm(AX, axis=1, keepdims=True)

def encode(emb, placed):
    px = int(round((np.tanh(emb @ AX[0]) + 1) / 2 * 12)) + 2   # 2..14
    py = int(round((np.tanh(emb @ AX[1]) + 1) / 2 * 12)) + 2
    shape = SEED if (emb @ AX[2]) > 0 else LINE
    reloc = 0
    cx, cy = px, py
    while any(max(abs(cx - ox), abs(cy - oy)) < 5 for ox, oy in placed):
        cx = 2 + (cx + 4 - 2) % 13
        if cx == px:
            cy = 2 + (cy + 4 - 2) % 13
        reloc += 1
        if reloc > 12:
            break
    return shape, cx, cy, reloc

def imprint_sig(pts, cx, cy, seed):
    e = GaugeCap(seed=seed, violence=V, decay=D)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    return e.sig_rad.ravel().copy()

K = 12
episodes = [rng.normal(size=EMB_D) for _ in range(K)]
episodes = [e / np.linalg.norm(e) for e in episodes]

print(f"writing {K} episodes through the encoder...")
placed, lib, meta = [], {}, {}
total_reloc = 0
for i, emb in enumerate(episodes):
    shape, cx, cy, reloc = encode(emb, placed)
    total_reloc += reloc
    placed.append((cx, cy))
    lib[i] = imprint_sig(shape, cx, cy, 42)
    meta[i] = (shape, cx, cy)
print(f"  relocations at write: {total_reloc} across {K} episodes")
ov = min(max(abs(a[0] - b[0]), abs(a[1] - b[1]))
         for i, a in enumerate(placed) for b in placed[i + 1:])
print(f"  min pairwise placement distance after separation: {ov} (target >= 5)")

print()
print("sigma   end-to-end acc   same-placement rate")
for sigma in (0.05, 0.10, 0.20):
    ok = same = tot = 0
    for i, emb in enumerate(episodes):
        for s in (77, 101):
            noisy = emb + np.random.default_rng(s + i).normal(size=EMB_D) * sigma
            noisy /= np.linalg.norm(noisy)
            shape, cx, cy, _ = encode(noisy, [p for j, p in enumerate(placed) if j != i])
            same += int((cx, cy) == meta[i][1:])
            sig = imprint_sig(shape, cx, cy, s)
            pick = max(lib, key=lambda j: cos(sig, lib[j]))
            ok += int(pick == i)
            tot += 1
    print(f"{sigma:.2f}    {ok}/{tot} = {ok / tot * 100:3.0f}%        {same / tot * 100:3.0f}%")
