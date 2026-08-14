"""Frame-tiers & phon-gate fixture generation (F-1/F-2; probes 38-39).

SEPARATE from make_fixtures.py and make_rulers_fixtures.py on purpose:
regenerating the workshop or rulers fixtures is a probe, and this script
must never trigger it. Run ONCE at build time; outputs pinned under
data/fixtures/.

Protocol notes (the shuffled order is part of the protocol, third
sighting): byb insertion order, collision-group order, and per-base
suffix order all derive from Transform.fit's shuffled pair list
(seed 7); the corpus split is seed 5 (probe 37/38); the collision
census walk is seed 9 (probe 39).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from mirror import Embedder, Transform, mine_pairs
from mirror.agreement import (build_number_lexicon, mine_strict_cases,
                              mine_v2_cases, predict_trigram,
                              train_ngram_counts, DET_V2,
                              EXPERIMENTAL_TIERS)
from mirror.config import DATA_DIR
from mirror.diagnostics import shape_seq

FIX = DATA_DIR / "fixtures"


def agreement_v2(emb, tr):
    """Probe 38: mine ONCE from the pinned corpus_big (seed-5 split),
    pin the case list with tier tags and the trigram control baked in;
    record the refusal taxonomy counts and the strict-subset agreement."""
    sg, pl, ambiguous = build_number_lexicon(tr.pairs)
    with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
        sents = [l.split() for l in f if len(l.split()) >= 6]
    rng = np.random.default_rng(5)
    idx = rng.permutation(len(sents))
    cut = int(len(sents) * 0.95)
    train = [sents[i] for i in idx[:cut]]
    held = [sents[i] for i in idx[cut:]]

    cases, refusals = mine_v2_cases(held, sg, pl)
    bi, tri = train_ngram_counts(train)
    # the strict frame certifies its core: v2 cases the strict miner
    # also accepts (same sentence, same subject, same verb) — the
    # subset the tier-1 regression is asserted on
    strict_keys = {(tuple(c["tokens"]), c["subj_i"], c["verb_i"])
                   for c in mine_strict_cases(held, sg, pl)}
    strict_agree = [0, 0]
    pinned = []
    for c in cases:
        s = c["tokens"]
        pinned.append({
            "sentence": " ".join(s),
            "subj_i": c["subj_i"], "verb_i": c["verb_i"],
            "subj_n": c["subj_n"], "gold": c["gold"],
            "attractor": c["attractor"],
            "between_nouns": c["between_nouns"],
            "bucket": c["bucket"], "tier": c["tier"],
            "strict_certified":
                (tuple(s), c["subj_i"], c["verb_i"]) in strict_keys,
            "trigram_pred": predict_trigram(c, bi, tri),
        })
        if s[0] in DET_V2 and (s[1] in sg or s[1] in pl):
            strict_agree[0] += int(c["subj_i"] == 1)
            strict_agree[1] += 1
    buckets = {}
    for c in pinned:
        buckets[c["bucket"]] = buckets.get(c["bucket"], 0) + 1
    return {
        "lexicon_sizes": {"sg": len(sg), "pl": len(pl),
                          "ambiguous_dropped": len(ambiguous)},
        "n_strict_certified":
            sum(1 for c in pinned if c["strict_certified"]),
        "n_cases": len(pinned),
        "n_attractors": sum(1 for c in pinned if c["attractor"]),
        "buckets": buckets,
        "refusals": dict(refusals),
        "strict_subset_agreement": strict_agree,
        "experimental_tiers": list(EXPERIMENTAL_TIERS),
        "cases": pinned,
    }


def phon_gate_sets(emb, tr):
    """Probe 39: the collision census -> pinned attack / true / disamb /
    wrong-suffix sets (seed 9, consecutive-pair walk, homophones out of
    scope, caps 120/200/120/150)."""
    byb = defaultdict(dict)
    for base, sfx, w, rem in tr.pairs:
        byb[base][sfx] = (w, tuple(rem))
    attested = defaultdict(set)
    for _, sfx, _, rem in tr.pairs:
        attested[sfx].add(tuple(rem))

    groups = defaultdict(list)
    for b in byb:
        groups[shape_seq(emb.corpus[b])].append(b)
    coll = [g for g in groups.values() if len(g) >= 2]

    rng = np.random.default_rng(9)
    attacks, trues, disamb, homophones = [], [], [], 0
    for g in coll:
        rng.shuffle(g)
        for i in range(len(g) - 1):
            B1, B2 = g[i], g[i + 1]
            if emb.corpus[B1] == emb.corpus[B2]:
                homophones += 1          # true homophones: out of scope
                continue
            for sfx, (w2, _) in byb[B2].items():
                if sfx in byb.get(B1, {}) or sfx in tr.modal_phon:
                    attacks.append([B1, B2, sfx, w2])
                    break
            for sfx, (w1, _) in byb[B1].items():
                trues.append([B1, sfx, w1])
                break
            disamb.append([B1, B2])
    attacks, trues, disamb = attacks[:120], trues[:200], disamb[:120]

    wrong, ambiguous_skipped = [], 0
    for b, d in byb.items():
        if len(d) >= 2:
            sfxs = list(d.keys())
            right, wrong_s = sfxs[0], sfxs[1]
            obs = emb.corpus[d[right][0]]
            if tuple(obs[len(emb.corpus[b]):]) in attested[wrong_s]:
                ambiguous_skipped += 1   # remainder attested cross-suffix
                continue
            wrong.append([b, right, wrong_s, d[right][0]])
            if len(wrong) >= 150:
                break

    return {
        "n_collision_groups": len(coll),
        "n_homophone_pairs_skipped": homophones,
        "n_cross_suffix_ambiguous_skipped": ambiguous_skipped,
        "attacks": attacks, "trues": trues, "disamb": disamb,
        "wrong_suffix": wrong,
    }


def attested_allomorphs(tr):
    """The pinned arbitration table: suffix -> attested phoneme
    remainders, from the transform's full mined pair list (the probe-39
    protocol; 'training pairs' = the transform's fit corpus)."""
    attested = defaultdict(set)
    for _, sfx, _, rem in tr.pairs:
        attested[sfx].add(tuple(rem))
    return {s: sorted(list(r) for r in rems)
            for s, rems in sorted(attested.items())}


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))

    ag = agreement_v2(emb, tr)
    (FIX / "agreement_v2_cases.json").write_text(
        json.dumps(ag, indent=1), encoding="utf-8")
    print(f"agreement_v2_cases.json: {ag['n_cases']} cases, "
          f"{ag['n_attractors']} attractors; buckets {ag['buckets']}; "
          f"refusals {ag['refusals']}; strict-subset agreement "
          f"{ag['strict_subset_agreement'][0]}/"
          f"{ag['strict_subset_agreement'][1]}")

    pg = phon_gate_sets(emb, tr)
    (FIX / "phon_gate_sets.json").write_text(
        json.dumps(pg, indent=1), encoding="utf-8")
    print(f"phon_gate_sets.json: {pg['n_collision_groups']} collision "
          f"groups; {len(pg['attacks'])} attacks, {len(pg['trues'])} "
          f"trues, {len(pg['disamb'])} disamb, "
          f"{len(pg['wrong_suffix'])} wrong-suffix "
          f"({pg['n_homophone_pairs_skipped']} homophone pairs and "
          f"{pg['n_cross_suffix_ambiguous_skipped']} cross-suffix-"
          f"ambiguous skipped)")

    at = attested_allomorphs(tr)
    (FIX / "attested_allomorphs.json").write_text(
        json.dumps(at, indent=1), encoding="utf-8")
    print("attested_allomorphs.json: " +
          ", ".join(f"-{s}: {len(r)}" for s, r in at.items()))


if __name__ == "__main__":
    main()
