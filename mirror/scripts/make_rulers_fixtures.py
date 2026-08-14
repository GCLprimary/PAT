"""Rulers & Registers fixture generation (law: artifact over recipe).

SEPARATE from make_fixtures.py on purpose: regenerating the workshop
fixtures is a probe, and this script must never trigger it. Run ONCE at
build time; outputs pinned under data/fixtures/.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from mirror import Embedder, Transform, mine_pairs
from mirror.agreement import (build_number_lexicon, mine_strict_cases,
                              predict_trigram, train_ngram_counts)
from mirror.config import DATA_DIR

FIX = DATA_DIR / "fixtures"


def rulers_events():
    """Hidden 20-cycle at phase 7 in noise (probe 36b protocol)."""
    rng = np.random.default_rng(41)
    ks = rng.choice(200, 60, replace=False)
    cycle = [int(7 + 20 * k) for k in ks]
    noise = [int(p) for p in rng.integers(0, 4000, 40)]
    return {"events": sorted(cycle + noise), "true_phase": 7,
            "n_cycle": len(cycle), "n_noise": len(noise)}


def register_streams():
    """Pinned dependency streams (probe 36 protocol)."""
    rng = np.random.default_rng(43)
    singles = []
    for gap in (2, 5, 10, 20, 40):
        for _ in range(20):
            p = int(rng.integers(0, 1000))
            f = "sg" if rng.random() < 0.5 else "pl"
            singles.append({"gap": gap, "events": [
                ["open", p, f], ["close", p + gap]], "gold": [f]})
    nested = []
    for _ in range(60):
        p = int(rng.integers(0, 1000))
        outer = int(rng.integers(8, 41))
        d1 = int(rng.integers(1, outer - 4))
        d2 = int(rng.integers(1, outer - d1 - 2))
        fa = "sg" if rng.random() < 0.5 else "pl"
        fb = "sg" if fa == "pl" else "pl"          # opposite: decidable
        nested.append({"events": [
            ["open", p, fa], ["open", p + d1, fb],
            ["close", p + d1 + d2], ["close", p + outer]],
            "gold": [fb, fa]})
    return {"singles": singles, "nested": nested}


def agreement_cases(emb, tr):
    """Mine ONCE from the pinned corpus_big (probe-37 split), pin the
    case list with the trigram control's predictions baked in."""
    sg, pl, ambiguous = build_number_lexicon(tr.pairs)
    with open(DATA_DIR / "corpus_big.txt", encoding="utf-8") as f:
        sents = [l.split() for l in f if len(l.split()) >= 6]
    rng = np.random.default_rng(5)
    idx = rng.permutation(len(sents))
    cut = int(len(sents) * 0.95)
    train = [sents[i] for i in idx[:cut]]
    held = [sents[i] for i in idx[cut:]]

    cases = mine_strict_cases(held, sg, pl)
    bi, tri = train_ngram_counts(train)
    pinned = []
    for c in cases:
        pinned.append({
            "sentence": " ".join(c["tokens"]),
            "subj_n": c["subj_n"], "gold": c["gold"],
            "attractor": c["attractor"],
            "between_nouns": c["between_nouns"],
            "trigram_pred": predict_trigram(c, bi, tri),
        })
    n_attr = sum(1 for c in pinned if c["attractor"])
    return {"lexicon_sizes": {"sg": len(sg), "pl": len(pl),
                              "ambiguous_dropped": len(ambiguous)},
            "n_cases": len(pinned), "n_attractors": n_attr,
            "cases": pinned}


def imposter_split(emb, tr):
    """Pinned known/withheld split for the ceiling (probe 35), with
    law-4 hygiene applied and recorded."""
    byb = defaultdict(dict)
    for base, sfx, w, _ in tr.pairs:
        byb[base][sfx] = w
    rng = np.random.default_rng(29)
    cands = sorted([b for b, d in byb.items()
                    if len(d) >= 2 and len(b) >= 4])
    rng.shuffle(cands)
    known = cands[:40]
    withheld = cands[40:80]
    known_set = set(known)

    def forms(bases):
        out, dropped = [], []
        for b in bases:
            for sfx, w in byb[b].items():
                if w in known_set:
                    dropped.append(w)          # the 'listing' pattern
                else:
                    out.append([b, sfx, w])
        return out, dropped

    known_forms, d1 = forms(known)
    unknown_forms, d2 = forms(withheld)
    return {"known_bases": known, "known_forms": known_forms,
            "unknown_forms": unknown_forms,
            "hygiene_dropped": d1 + d2}


def battery_banks():
    """Snapshot the agent batteries' base banks and observed words into a
    mirror fixture (layer-3 realized-ceiling tests read mirror fixtures
    only; provenance: the agent repo's pinned fixtures)."""
    agent_fix = DATA_DIR.parent.parent / "pat" / "data" / "fixtures"
    stream = json.loads((agent_fix / "learning_stream.json").read_text(
        encoding="utf-8"))
    comp = json.loads((agent_fix / "composition_inputs.json").read_text(
        encoding="utf-8"))
    comp_observed = []
    for inp in comp["inputs"]:
        for cl, gd in zip(inp["clauses"], inp["gold"]):
            if cl.split()[0] == "analyze" and gd[0] == "DERIVED":
                comp_observed.append([cl.split()[-1], gd[1]])
    return {
        "learning_bases": stream["bases"],
        "learning_observed": [[w, b] for _, b, w in stream["tasks"]],
        "composition_bases": comp["known0"] + comp["teachable"],
        "composition_observed": comp_observed,
        "provenance": "agent/data/fixtures (pinned, checksummed there)",
    }


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    emb = Embedder()
    tr = Transform(emb).fit(mine_pairs(emb.corpus))

    ev = rulers_events()
    (FIX / "rulers_events.json").write_text(json.dumps(ev), encoding="utf-8")
    print(f"rulers_events.json: {ev['n_cycle']} cycle + {ev['n_noise']} noise")

    st = register_streams()
    (FIX / "register_streams.json").write_text(json.dumps(st),
                                               encoding="utf-8")
    print(f"register_streams.json: {len(st['singles'])} singles, "
          f"{len(st['nested'])} nested")

    ag = agreement_cases(emb, tr)
    (FIX / "agreement_cases.json").write_text(json.dumps(ag, indent=1),
                                              encoding="utf-8")
    print(f"agreement_cases.json: {ag['n_cases']} cases, "
          f"{ag['n_attractors']} attractors; lexicon {ag['lexicon_sizes']}")

    imp = imposter_split(emb, tr)
    (FIX / "imposter_split.json").write_text(json.dumps(imp, indent=1),
                                             encoding="utf-8")
    print(f"imposter_split.json: {len(imp['known_bases'])} known bases, "
          f"{len(imp['known_forms'])} known forms, "
          f"{len(imp['unknown_forms'])} unknown forms, "
          f"{len(imp['hygiene_dropped'])} hygiene-dropped: "
          f"{imp['hygiene_dropped']}")

    banks = battery_banks()
    (FIX / "battery_banks.json").write_text(json.dumps(banks),
                                            encoding="utf-8")
    print(f"battery_banks.json: learning {len(banks['learning_bases'])} "
          f"bases / {len(banks['learning_observed'])} observed; "
          f"composition {len(banks['composition_bases'])} bases / "
          f"{len(banks['composition_observed'])} observed")


if __name__ == "__main__":
    main()
