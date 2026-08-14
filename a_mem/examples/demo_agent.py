"""a_mem demo agent (W-6, D-5): the hybrid loop, runtime-agnostic.

A scripted "agent" processes six episodes (random-embedding stand-ins for
real content), writes each through hook.write_episode, then loses all of
its context. It recovers every episode from a noisy embedding alone via
hook.recall_context (embedding -> id -> anchors -> stage), and finishes
with a page-turned serial procession of three recalled episodes.

Runs from a fresh checkout:  python examples/demo_agent.py
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from amem import EpisodeHooks, Memory

EMB_D = 64
NOISE = 0.10


def main():
    t0 = time.time()
    store = tempfile.mkdtemp(prefix="a_mem_agent_")
    rng = np.random.default_rng(11)

    print("=" * 62)
    print("EPISODE WRITES - write_episode(embedding) per episode end")
    print("=" * 62)
    mem = Memory(seed=7, path=store)
    hooks = EpisodeHooks(mem)
    topics = ["fixed the auth bug", "planned the migration",
              "reviewed the PR", "debugged the flaky test",
              "wrote the design doc", "paired on the refactor"]
    episodes = {}
    for topic in topics:
        emb = rng.normal(size=EMB_D)
        emb /= np.linalg.norm(emb)
        mid = hooks.write_episode(emb, payload_meta={"topic": topic})
        entry = mem.library.get(mid)
        episodes[topic] = (emb, mid)
        print(f"  {mid}  '{topic}'  placed at {tuple(entry.meta['placement'])}"
              f"  overlap={entry.meta['overlap_report']['max_overlap']:.2f}")

    print()
    print("=" * 62)
    print("CONTEXT LOSS - the agent restarts with nothing but the store")
    print("=" * 62)
    mem2 = Memory(seed=99, path=store)          # fresh process, same disk
    hooks2 = EpisodeHooks(mem2)                 # index rebuilt from library
    print(f"  reloaded: {len(mem2.library)} episodes, "
          f"index size {len(hooks2.index)}")

    print()
    print("=" * 62)
    print(f"RECOVERY - noisy embeddings (sigma={NOISE}), recall_context")
    print("=" * 62)
    ok = 0
    recovered = []
    for topic, (emb, mid) in episodes.items():
        noisy = emb + rng.normal(size=EMB_D) * NOISE
        rec = hooks2.recall_context(noisy)
        got = mem2.library.get(rec.identity).meta["topic"]
        good = rec.identity == mid
        ok += int(good)
        recovered.append(rec.identity)
        print(f"  '{topic}'  ->  {rec.identity} ('{got}')  "
              f"[{'ok' if good else 'WRONG'}]  match={rec.scores['embedding_match']:+.2f}"
              f"  completion-conf={rec.confidence:.2f}")
    print(f"\n  identity accuracy: {ok}/{len(topics)}")

    print()
    print("=" * 62)
    print("SERIAL PROCESSION - three recalled episodes, page-turned")
    print("=" * 62)
    for res in mem2.sequence(recovered[:3], dwell=1):
        topic = mem2.library.get(res.target).meta["topic"]
        good = "ok " if res.identity == res.target else "BAD"
        print(f"  '{topic}'  stage holds {res.identity}  [{good}]  dwell={res.dwell}")

    elapsed = time.time() - t0
    print(f"\ndone in {elapsed:.1f}s  (target < 10s: {'PASS' if elapsed < 10 else 'FAIL'})")


if __name__ == "__main__":
    main()
