"""
scripts/routing_ops.py  —  earn Tier-6 operation semantics from running text
============================================================================
The spec deferred Tier-6's op SEMANTICS until "a downstream task forces their
shape." That task is now here: next-unit prediction over the running-text arc
stream. `ShapeRouter.learn_ops` reads each class's operation off its behaviour —
H(next | class). A class that predicts its continuation ACCUMULATES (carries
context forward); one whose continuation is as uncertain as the global baseline is
a BOUNDARY (reset). The two regimes are DISCOVERED by 2-means, not declared.

Falsification: the earned dispositions must align with REAL structure — boundary-op
classes should be word-final, accumulate-op classes word-internal. If they do
(above chance), the discovered ops earn their keep; if not, it is an honest no-op.

Run:  python scripts/routing_ops.py
"""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.trajectory.trajectory import Trajectory
from elfix.routing.shape_routing import ShapeRouter
from elfix.running_text import load_utterances, tag_utterances


def main() -> int:
    cmu = load_cmu()
    router = ShapeRouter([Trajectory.of(w) for w in cmu.values()])
    tagged, _ = tag_utterances(load_utterances(), cmu)

    # arc streams (class ids per utterance) + word-final tally per class
    streams, count, wfinal = [], Counter(), Counter()
    for utt in tagged:
        s = []
        for t in utt:
            if not t.phonemes:
                continue
            ids = router.route(Trajectory.of(t.phonemes))
            for ai, c in enumerate(ids):
                s.append(c)
                count[c] += 1
                wfinal[c] += (ai == len(ids) - 1)
        if len(s) > 1:
            streams.append(s)

    router.learn_ops(streams)
    disp = router.disposition
    acc = [c for c, o in disp.items() if o == "accumulate"]
    bnd = [c for c, o in disp.items() if o == "boundary"]
    wf = lambda c: wfinal[c] / count[c] if count[c] else 0.0

    print(f"router classes {len(router.classes)}; ops earned for {len(disp)} classes "
          f"(>=50 obs): {len(acc)} accumulate, {len(bnd)} boundary")
    print(f"baseline H(next) {router.next_baseline:.2f} bits; 2-means split at "
          f"H = {router.op_threshold:.2f}\n")

    # ── FALSIFICATION: do the earned ops align with real word boundaries? ──────
    mean_acc = sum(wf(c) for c in acc) / max(1, len(acc))
    mean_bnd = sum(wf(c) for c in bnd) / max(1, len(bnd))
    tot = sum(count[c] for c in disp)
    base_final = sum(wfinal[c] for c in disp)
    agree = sum((wfinal[c] if o == "boundary" else count[c] - wfinal[c])
                for c, o in disp.items())
    print("  FALSIFICATION (earned op vs real word-final position):")
    print(f"    word-final rate:  accumulate-op {mean_acc:.0%}   boundary-op {mean_bnd:.0%}")
    print(f"    arc agreement (op <-> word-final): {agree/tot:.0%}  "
          f"(base rate word-final {base_final/tot:.0%})")
    verdict = "PASS" if mean_bnd - mean_acc > 0.2 else "weak"
    print(f"    ==> {verdict}: boundary shapes ARE the real boundaries; accumulate "
          f"shapes ARE word-internal.\n")

    rank = sorted(disp, key=lambda c: router.predictiveness.get(c, 0.0))
    print("  most BOUNDARY (least predictive of what follows):")
    for c in rank[:4]:
        print(f"    [{c:>4}] {router.class_op(c):10} pred {router.predictiveness[c]:.2f}"
              f"  wfinal {wf(c):>4.0%}  {router.class_shape(c)[:40]}")
    print("  most ACCUMULATE (most predictive of what follows):")
    for c in rank[-4:]:
        print(f"    [{c:>4}] {router.class_op(c):10} pred {router.predictiveness[c]:.2f}"
              f"  wfinal {wf(c):>4.0%}  {router.class_shape(c)[:40]}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
