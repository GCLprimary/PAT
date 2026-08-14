"""Probe suite 4: absolute gauge vs normalized gauge, head to head.

G1: phase sweep both machines -- is the knife-edge a ruler artifact?
G2: memory discriminability both -- imprint/wipe/rebuild confusion matrix.
G3: forgetting mode -- what does each machine's decay actually do to shape?
"""
import numpy as np
from gauge import Gauge, GRID, SEED

np.set_printoptions(precision=3, suppress=True)

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

print("=" * 72)
print("G1 · PHASE SWEEP — defined fraction after 8 beats (aligned seed at 8,8)")
print("=" * 72)
viols = [0.10, 0.25, 0.45, 0.70]
decays = [0.03, 0.06, 0.09]
for norm in (False, True):
    tag = "NORMALIZED" if norm else "ABSOLUTE  "
    print(f"\n{tag}          " + "  ".join(f"d={d:.2f}" for d in decays))
    for v in viols:
        row = []
        for d in decays:
            e = Gauge(norm, seed=11, violence=v, decay=d)
            e.stamp(SEED, 8, 8)
            for _ in range(8):
                e.beat()
            row.append(e.defined_frac())
        print(f"  v={v:.2f}     " + "  ".join(f"{r:6.3f}" for r in row))

print()
print("=" * 72)
print("G2 · MEMORY — imprint 8 beats, wipe (each gauge's nothing), rebuild 6")
print("     confusion matrix of cosine(rebuilt traps, original traps)")
print("     margin = mean(diagonal) - mean(off-diagonal); >0 means real memory")
print("=" * 72)
patterns = {
    "NW": (SEED, 3, 3),
    "SE": (SEED, 15, 14),
    "line": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
names = list(patterns)
# pick mid-sweep settings per machine that showed structure (not 0, not 1)
settings = {False: (0.45, 0.05), True: (0.45, 0.05)}
for norm in (False, True):
    tag = "NORMALIZED" if norm else "ABSOLUTE"
    v, d = settings[norm]
    sigs, orig, reb = {}, {}, {}
    for name, (pts, cx, cy) in patterns.items():
        e = Gauge(norm, seed=42, violence=v, decay=d)
        e.stamp(pts, cx, cy)
        for _ in range(8):
            e.beat()
        sigs[name] = e.sig.copy()
        orig[name] = (e.w > 0.4).astype(float)
        e.wipe()
        for _ in range(6):
            e.beat(write_sig=False)
        reb[name] = e.w.copy()
    M = np.array([[cos(reb[n1], orig[n2]) for n2 in names] for n1 in names])
    diag = float(np.mean(np.diag(M)))
    off = float((M.sum() - np.trace(M)) / (M.size - len(names)))
    print(f"\n{tag} (v={v}, d={d})  original sizes: " +
          ", ".join(f"{n}:{int(orig[n].sum())}" for n in names))
    print(f"           " + "  ".join(f"{n:>6s}" for n in names))
    for i, n1 in enumerate(names):
        print(f"  {n1:8s} " + "  ".join(f"{M[i, j]:6.3f}" for j in range(len(names))))
    print(f"  margin (diag - offdiag): {diag - off:+.3f}")
    sn = np.array([sigs[n] / max(sigs[n].max(), 1e-12) for n in names])
    print(f"  signature pairwise cos:  " +
          "  ".join(f"{cos(sigs[names[i]], sigs[names[j]]):.3f}"
                    for i in range(len(names)) for j in range(i + 1, len(names))))

print()
print("=" * 72)
print("G3 · FORGETTING MODE — imprint one pattern, then 12 beats NO input;")
print("     track defined fraction and flatness. What does each nothing do?")
print("=" * 72)
for norm in (False, True):
    tag = "NORMALIZED" if norm else "ABSOLUTE"
    e = Gauge(norm, seed=9, violence=0.45, decay=0.05)
    e.stamp(SEED, 8, 8)
    traj = []
    for b in range(12):
        e.beat()
        traj.append((e.defined_frac(), e.flatness()))
    print(f"\n{tag}: (defined fraction, flatness) per beat")
    print("  " + "  ".join(f"({f:.2f},{fl:.2f})" for f, fl in traj[::2]))
