"""Probe suite 1: coherence, survival, sieve theorem, memory discriminability."""
import numpy as np
from engine import Engine, GRID, C, SEED, TRAP_T

np.set_printoptions(precision=3, suppress=True)

print("=" * 64)
print("P0 · COHERENCE — bounds, NaN, determinism, dead-field null")
print("=" * 64)
e = Engine(seed=1)
e.stamp(SEED, 4, 4)
for _ in range(12):
    e.beat()
ok_bounds = (0 <= e.a).all() and (e.a <= 1).all() and (0 <= e.w).all() and (e.w <= 1).all()
ok_nan = not (np.isnan(e.a).any() or np.isnan(e.w).any() or np.isnan(e.sig).any())
e2 = Engine(seed=1); e2.stamp(SEED, 4, 4)
for _ in range(12):
    e2.beat()
ok_det = np.array_equal(e.a, e2.a) and np.array_equal(e.sig, e2.sig)
# null: empty field, no signature -> must stay dead through beats
e3 = Engine(seed=7)
for _ in range(6):
    e3.beat()
null_dead = e3.act_mass() == 0 and e3.defined_count() == 0 and e3.sig.sum() == 0
print(f"bounds a,w in [0,1]:        {ok_bounds}")
print(f"no NaN anywhere:            {ok_nan}")
print(f"deterministic under seed:   {ok_det}")
print(f"empty field stays nothing:  {null_dead}  (mass={e3.act_mass():.4f})")

print()
print("=" * 64)
print("P1 · SURVIVAL — aligned vs random 7-point seeds, quiet dynamics")
print("    (no strokes: pure decay + member sustainment, 250 ticks)")
print("=" * 64)
trials = 120
surv_al, surv_rn = [], []
for t in range(trials):
    ea = Engine(seed=1000 + t)
    cx = 3 + ea.rng.integers(0, GRID - 11)
    cy = 3 + ea.rng.integers(0, GRID - 11)
    ea.stamp(SEED, cx, cy, w0=0.0)
    ea.quiet_ticks(250)
    surv_al.append(ea.act_mass())
    er = Engine(seed=5000 + t)
    xs = er.rng.integers(0, GRID, 7)
    ys = er.rng.integers(0, GRID, 7)
    for x, y in zip(xs, ys):
        er.a[y, x] = 1.0
    er.quiet_ticks(250)
    surv_rn.append(er.act_mass())
surv_al, surv_rn = np.array(surv_al), np.array(surv_rn)
print(f"aligned seed  — mean surviving mass {surv_al.mean():7.3f} | survived(>0.5): {(surv_al > 0.5).mean() * 100:5.1f}%")
print(f"random burst  — mean surviving mass {surv_rn.mean():7.3f} | survived(>0.5): {(surv_rn > 0.5).mean() * 100:5.1f}%")

print()
print("=" * 64)
print("P2 · SIEVE THEOREM — saturated field parity split")
print("=" * 64)
es = Engine(seed=2)
es.a[:] = 1.0
es.w[:] = 0.8
es.last_passed = es.last_rejected = 0
es._indraw_tick(write_sig=False)
print(f"one tick on saturated field: passed={es.last_passed}  rejected={es.last_rejected}")
print(f"theorem: same-parity non-center cells = 264 each  ->  {'CONFIRMED' if es.last_passed == 264 and es.last_rejected == 264 else 'VIOLATED'}")

print()
print("=" * 64)
print("P3 · MEMORY — does the zero point discriminate between pasts?")
print("    protocol: imprint pattern, 8 beats, save signature; wipe field;")
print("    read-only rebuild (6 beats, sig frozen); compare rebuilt trap map")
print("    to each original trap map (cosine). Diagonal should beat rows.")
print("=" * 64)
patterns = {
    "NW-constellation": (SEED, 3, 3),
    "SE-constellation": (SEED, 15, 14),
    "NE-line": ([(0, 0), (3, 0), (6, 0), (9, 0), (0, 3), (3, 3)], 12, 3),
}
sigs, originals, rebuilt = {}, {}, {}
for name, (pts, cx, cy) in patterns.items():
    ep = Engine(seed=42)
    ep.stamp(pts, cx, cy)
    for _ in range(8):
        ep.beat()
    sigs[name] = ep.sig.copy()
    originals[name] = (ep.w > TRAP_T).astype(float)
    ep.clear_field()
    for _ in range(6):
        ep.beat(write_sig=False)
    rebuilt[name] = ep.w.copy()

def cos(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u.ravel() @ v.ravel() / (nu * nv)) if nu > 0 and nv > 0 else 0.0

names = list(patterns)
print("\nsignature vectors (9-dim, normalized):")
for n in names:
    s = sigs[n] / max(sigs[n].max(), 1e-9)
    print(f"  {n:18s} {s}")
print("\nsignature pairwise cosine:")
for i, n1 in enumerate(names):
    row = "  ".join(f"{cos(sigs[n1], sigs[n2]):.3f}" for n2 in names)
    print(f"  {n1:18s} {row}")
print("\nrebuilt-vs-original trap-map cosine (rows: rebuilt-from-sig; cols: original pattern):")
header = "  ".join(f"{n[:10]:>10s}" for n in names)
print(f"  {'':18s} {header}")
for n1 in names:
    row = "  ".join(f"{cos(rebuilt[n1], originals[n2]):10.3f}" for n2 in names)
    print(f"  {n1:18s} {row}")

print()
print("=" * 64)
print("P4 · CROSSTALK — superpose k signatures, retrieval fidelity vs k")
print("=" * 64)
pat_bank = [(SEED, 3, 3), (SEED, 15, 14), (SEED, 3, 14), (SEED, 15, 3),
            (SEED, 9, 3), (SEED, 3, 9)]
bank_sigs, bank_orig = [], []
for k, (pts, cx, cy) in enumerate(pat_bank):
    ep = Engine(seed=99)
    ep.stamp(pts, cx, cy)
    for _ in range(8):
        ep.beat()
    bank_sigs.append(ep.sig.copy())
    bank_orig.append((ep.w > TRAP_T).astype(float))
print("k  mean cosine(rebuild, each stored original)   cosine(rebuild, unstored control)")
control = bank_orig[-1]
for k in range(1, 6):
    er = Engine(seed=99)
    er.sig = np.sum(bank_sigs[:k], axis=0)
    for _ in range(6):
        er.beat(write_sig=False)
    stored = np.mean([cos(er.w, bank_orig[j]) for j in range(k)])
    ctrl = cos(er.w, control)
    print(f"{k}  {stored:36.3f}   {ctrl:.3f}")
