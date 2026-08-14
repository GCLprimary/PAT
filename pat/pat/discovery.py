"""O-1/O-2: suffix discovery (probe 55) — Pat's proposal, human-gated,
now an organ.

FOUNDING DOCUMENT: agent/PROPOSAL.md, written by Pat from its own
ledgers. This module implements that proposal and nothing beyond it:
mine candidate suffixes from the no-such-stem tail census, audit each
candidate (attestation examines the teacher), accept only what the
exactness law can carry, retire wrongly-adopted atoms through
certification.

LAW 1 — DISCOVERY IS AUDITED LIKE ANY TEACHER. A candidate tail must
beat the stem-attestation baseline by an ADDITIVE +15 points (the
probe's earlier multiplicative bar failed because the baseline is
contaminated by the signal itself — random class words carry real
suffixes too; that design note lives here). Minimum stem length 3
phonemes damps accidental short-stem hits.

LAW 2 — ONLY WHAT EXACTNESS CAN CARRY. Concatenative candidates only,
under the DOUBLE-LOCK: pron(word) == pron(stemword) + tail AND
word == stemword + modal_spelling. Mutating and bound-stem classes
(create->creation with its t->sh; famous without a free *fam*;
ability without a free *abil*) are CENSUSED with counts and named
exemplars — the future stem-allomorphy lane's customer list, never
guessed at.

LAW 3 — DISCOVERED KNOWLEDGE WEARS ITS PROVENANCE. `discovered:<sfx>`
is the ledger's FIFTH class (birth / read / lesson / pruned /
discovered), and it survives restart like the others: the artifact is
checksummed, registration is deterministic.

LAW 4 — GREEDY LONGEST-TAIL-FIRST HARVEST. -ment claims its words
before the n-t fragment can; harvested words leave the pool.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

MINSTEM = 3
BASELINE_DRAWS = 1500
BASELINE_SEED = 5
YIELD_BAR = 50
STEM_BAR = 40
MARGIN = 0.15
TOP_CANDIDATES = 12


def no_such_stem_class(session, stream):
    """Recompute the class over the pinned stream (the probe
    protocol): derived-looking words none of whose putative stems'
    pronunciations exist anywhere in the lexicon."""
    out = []
    for w in stream:
        p = tuple(session.emb.corpus[w])
        if session._looks_derived(w) and not session._stem_exists(p):
            out.append(w)
    return out


def discover(session, stream):
    """Phases A/B/C -> (discovered, census, retired_pairs, confabs).

    discovered: [{suffix, tail, certified, attested_stems, rate,
                  baseline, spelling_share, class_yield}]
    census:     [{tail, kind, count, exemplars}] — the mutating/bound
                ledger (law 2's customer list).
    """
    corpus = session.emb.corpus
    pron_index = session._pron_index
    no_such = no_such_stem_class(session, stream)
    rng = np.random.default_rng(BASELINE_SEED)

    def att_rate(words, k, tail=None):
        hit = tot = 0
        for w in words:
            p = tuple(corpus[w])
            if len(p) - k < MINSTEM:
                continue
            if tail is not None and p[-k:] != tail:
                continue
            tot += 1
            hit += int(p[:-k] in pron_index)
        return hit, tot

    # PHASE A — the audit
    cands = []
    baselines = {}
    for k in (4, 3, 2):
        tails = Counter(tuple(corpus[w])[-k:] for w in no_such
                        if len(corpus[w]) - k >= MINSTEM)
        bh, bt = att_rate(rng.choice(no_such, BASELINE_DRAWS).tolist(),
                          k)
        base = bh / max(bt, 1)
        baselines[k] = base
        for t, n in tails.most_common(60):
            if n < YIELD_BAR:
                continue
            h, tt = att_rate(no_such, k, t)
            r = h / max(tt, 1)
            if r >= base + MARGIN and h >= STEM_BAR:
                cands.append((t, k, n, h, r, base))
    cands.sort(key=lambda x: (-x[1], -x[3]))     # law 4: longest first

    # PHASE B/C — certification and harvest. CERTIFICATION and
    # PROMOTION are different events (the probe's own arithmetic):
    # every double-locked pair is a certified truth and RETIRES
    # (capitalist = capital + ist stays true whatever -ist's status),
    # but only candidates whose certified count clears STEM_BAR are
    # PROMOTED into the discovered-suffix table. -ist and the -et
    # fragments retire their pairs and stay off the table — the
    # organ's taste, asserted as canaries.
    discovered, census, retired_pairs = [], [], []
    confabs = 0
    pool = set(no_such)
    for t, k, n, h, r, base in cands[:TOP_CANDIDATES]:
        prs, spell = [], Counter()
        for w in sorted(pool):
            p = tuple(corpus[w])
            if len(p) - k >= 2 and p[-k:] == t and p[:-k] in pron_index:
                for sw in pron_index[p[:-k]]:
                    if w.startswith(sw) and len(w) > len(sw):
                        prs.append((w, sw, w[len(sw):]))
                        spell[w[len(sw):]] += 1
                        break
        if not spell:
            census.append({"tail": list(t), "kind": "no-orthography",
                           "count": h, "exemplars": []})
            continue
        modal, _ = spell.most_common(1)[0]
        certified = [(w, sw) for w, sw, sp in prs if sp == modal]
        mutating = h - len(prs)
        ok_pairs = []
        for w, sw in certified:
            if tuple(corpus[w]) == tuple(corpus[sw]) + t:
                ok_pairs.append((w, sw))
                pool.discard(w)
            else:
                confabs += 1                     # the double-lock's veto
        entry = {"suffix": modal, "tail": list(t),
                 "certified": len(ok_pairs), "attested_stems": h,
                 "rate": round(r, 4), "baseline": round(base, 4),
                 "spelling_share": [spell[modal], sum(spell.values())],
                 "class_yield": n}
        promoted = len(ok_pairs) >= STEM_BAR
        if ok_pairs:
            retired_pairs.append((modal, list(t), ok_pairs, promoted))
        if promoted:
            discovered.append(entry)
            if mutating > 0:
                mut_ex = [w for w, sw, sp in prs if sp != modal][:3]
                census.append({"tail": list(t), "kind": "mutating",
                               "count": mutating, "exemplars": mut_ex})
        else:
            census.append({"tail": list(t),
                           "kind": "certified-below-promotion-bar",
                           "count": len(ok_pairs),
                           "exemplars": [w for w, _ in ok_pairs[:3]]})
    return {"no_such_stem_size": len(no_such),
            "baselines": {str(k): round(v, 4)
                          for k, v in baselines.items()},
            "candidates_cleared_audit": len(cands),
            "discovered": discovered, "census": census,
            "confabs": confabs}, retired_pairs


def write_artifact(result, retired_pairs, out_path):
    payload = dict(result)
    payload["pairs"] = {sfx: {"tail": tail, "promoted": promoted,
                              "pairs": [[w, sw] for w, sw in pairs]}
                        for sfx, tail, pairs, promoted in retired_pairs}
    text = json.dumps(payload, indent=1, sort_keys=True)
    # newline pinned to LF so the file's bytes ARE the hashed text
    # (the Windows text-mode translation burned a checksum before)
    Path(out_path).write_text(text, encoding="utf-8", newline="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def register(gate, result, retired_pairs, corpus):
    """O-2: each candidate enters the arbitration ecology at the
    granularity it EARNED — every certified triple as a pair-exact
    entry (a certified pair is true whatever its suffix's status),
    the tail into the attested set under its modal name (so proposals
    can form), surfaces for verdicts. Only PROMOTED suffixes appear
    in the discovered table; registration is opt-in per gate — the
    shipped six-suffix gates are untouched unless a caller registers.
    """
    for sfx, tail, pairs, promoted in retired_pairs:
        t = tuple(tail)
        gate.attested.setdefault(sfx, set()).add(t)
        for w, sw in pairs:
            gate.pair_rems.setdefault(
                (tuple(corpus[sw]), sfx), set()).add(t)
            gate.surface_words.setdefault((sw, sfx), []).append(w)
    return gate


def retire_atoms(session, retired_pairs):
    """O-2: the wrongly-adopted atoms retire through the EXISTING
    certified pathway, wearing the fifth provenance class. The
    double-lock already certified pron identity; the alias keeps both
    receipts."""
    n = 0
    for sfx, tail, pairs, promoted in retired_pairs:
        for w, sw in pairs:
            if w not in session.known:
                continue
            old = session.known[w]
            session.retired[w] = {
                "alias": f"derivable: {sw}+{sfx}",
                "surface": w,
                "read_epoch": session._taught_epoch.get(w, 0),
                "pruned_epoch": session.epoch,
                "provenance": (f"discovered:{sfx}; was '{old}'; "
                               f"now {sw} + {sfx}, both receipts kept"),
            }
            del session.known[w]
            n += 1
    return n
