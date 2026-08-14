"""Probe suite 11: beat-to-beat tenant swapping, three drive methods.

Two identities alternate on the stage (page-turn before every install).
  M-a: anchor cue        -- flatten + half anchors of the target
  M-b: core swap/selector -- flatten + install a NOISY signature of the
       target; machine classifies it against the library and deploys the
       winning anchor set itself (the autonomous loop, per beat)
  M-c: core swap/direct   -- flatten + install signature only, decoded
       by inverse-spiral painting (amp 0.25), no anchors at all
Rates: 1, 2, 3 beats per tenant, 12 beats total each run.
Score: fraction of beats the correct tenant holds the stage; mean purity.
"""
import numpy as np
from gauge import Gauge, GRID, N, SEED
from gauge5 import GaugeV5

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(7)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

patterns = {
    "A": (SEED, 3, 3),
    "B": (SEED, 15, 14),
    "C": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
names = list(patterns)
V, D = 0.45, 0.05

lib = {}
for name, (pts, cx, cy) in patterns.items():
    ea = Gauge(False, seed=21, violence=0.0, decay=D)
    ea.stamp(pts, cx, cy, w0=0.0)
    for _ in range(80):
        ea._decay_traps("audit")
        ea._sustain()
    en = GaugeV5(seed=42, violence=V, decay=D, decode_amp=0.0)
    en.stamp(pts, cx, cy)
    for _ in range(8):
        en.beat()
    lib[name] = dict(anchors=(ea.w > 0.4), sig=en.sig.copy(),
                     orig=(en.w > 0.4).astype(float))

# noisy incoming cores for the selector method
noisy_sig = {}
for name, (pts, cx, cy) in patterns.items():
    e = GaugeV5(seed=77, violence=V, decay=D, decode_amp=0.0)
    e.stamp(pts, cx, cy)
    for _ in range(8):
        e.beat()
    noisy_sig[name] = e.sig.copy()

def deploy_anchors(e, name):
    cells = np.argwhere(lib[name]["anchors"])
    sel = cells[rng.choice(len(cells), size=max(1, len(cells) // 2), replace=False)]
    for y, x in sel:
        e.a[y, x] += 10.0 / N
    e._renorm()

def stage(e):
    scores = {n: cos(e.w, lib[n]["orig"]) for n in names}
    top = max(scores, key=scores.get)
    second = max(v for n, v in scores.items() if n != top)
    return top, scores[top] - second

def run(method, period, total=12, seed=5):
    e = GaugeV5(seed=seed, violence=V, decay=D,
                decode_amp=(0.25 if method == "c" else 0.0))
    e.wipe()
    tenants = ["A", "B"]
    correct = 0
    purities = []
    classify_ok = 0
    installs = 0
    t = 0
    while t < total:
        target = tenants[(t // period) % 2]
        # page-turn + install
        e.wipe()
        e.sig[:] = 0
        if method == "a":
            deploy_anchors(e, target)
        elif method == "b":
            pick = max(names, key=lambda n: cos(noisy_sig[target], lib[n]["sig"]))
            classify_ok += int(pick == target)
            installs += 1
            deploy_anchors(e, pick)
        elif method == "c":
            e.sig = lib[target]["sig"].copy()
        for _ in range(period):
            e.beat(write_sig=False)
            top, pur = stage(e)
            correct += int(top == target)
            purities.append(pur if top == target else -pur)
            t += 1
            if t >= total:
                break
    extra = f"   classify {classify_ok}/{installs}" if method == "b" else ""
    return correct / total, float(np.mean(purities)), extra

print("=" * 66)
print("BEAT-TO-BEAT ALTERNATION — A/B, page-turn every install")
print("  score: correct-tenant beats / total; mean signed purity")
print("=" * 66)
labels = {"a": "M-a anchor cue        ",
          "b": "M-b core swap/selector",
          "c": "M-c core swap/direct  "}
for period in (1, 2, 3):
    print(f"\nrate: {period} beat(s) per tenant, 12 beats")
    for m in ("a", "b", "c"):
        acc, pur, extra = run(m, period)
        print(f"  {labels[m]}  correct {acc * 100:4.0f}%   purity {pur:+.3f}{extra}")

print()
print("=" * 66)
print("CONTROL — hot alternation at rate 1 (no page-turn), anchor cue")
print("=" * 66)
e = GaugeV5(seed=5, violence=V, decay=D, decode_amp=0.0)
e.wipe()
correct = 0
for t in range(12):
    target = ["A", "B"][t % 2]
    deploy_anchors(e, target)
    e.beat(write_sig=False)
    top, _ = stage(e)
    correct += int(top == target)
print(f"  correct: {correct}/12 = {correct / 12 * 100:.0f}%  (page-turn's necessity, re-confirmed)")
