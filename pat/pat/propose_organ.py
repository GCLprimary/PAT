"""B-0: the proposal ritual — the creature nominates its own next
organ, and builds nothing.

LAW 3 (Part XII): A PROPOSAL IS NOT AN IMPLEMENTATION. This module
scans the creature's OWN ledgers — the adoption ledger, the deferral
queue, the censuses, the prune aliases — ranks the hygiene classes by
evidence count, and emits exactly ONE organ proposal as PROPOSAL.md:
the highest-evidence item, citing ledger entries by count and class,
with a one-paragraph mechanism sketch and a proposed acceptance
inequality. The proposed organ is NEVER built in the Part that
proposes it; the human gate reads the proposal in the HANDOFF.

This is the first formal self-proposed organ. The stem-existence
oracle was the dress rehearsal (a mechanism the ledgers begged for,
built a Part later); this ritual makes the begging legible.
"""
from collections import Counter
from pathlib import Path


def scan_ledgers(session):
    """-> ranked [(class_name, count, sample_entries)] over every
    ledger the session keeps."""
    classes = []
    adoptions = session.adoptions
    no_such = [(w, p) for w, p in session.known.items()
               if p == "read:no-such-stem"]
    stale = [(w, p) for w, p in session.known.items()
             if p.startswith("read: stem ")]
    classes.append(("adopted:no-such-stem", len(no_such), no_such))
    classes.append(("adopted:stale-stem", len(stale), stale))
    classes.append(("deferred-final", len(session.deferred),
                    [(w, f"waited {a} epochs")
                     for w, a in session.deferred.items()]))
    classes.append(("self-census", len(session.census),
                    [(c["word"], f"collides with {c['collides_with']}")
                     for c in session.census]))
    classes.append(("homophone-verdicts", len(session.homophones),
                    [(h["word"], f"sounds like {h.get('surface')}")
                     for h in session.homophones]))
    classes.append(("prune-aliases", len(session.retired),
                    [(w, e["alias"])
                     for w, e in session.retired.items()]))
    return sorted(classes, key=lambda c: -c[1])


def tail_census(session, entries, max_tail=4, top=10):
    """The evidence inside the top class: recurring phoneme tails among
    the cited words — the shape of the missing rule."""
    tails = Counter()
    for w, _ in entries:
        pron = session.emb.corpus.get(w)
        if not pron or len(pron) < max_tail + 2:
            continue
        for k in (2, 3, 4):
            tails[tuple(pron[-k:])] += 1
    return tails.most_common(top)


def propose(session, out_path):
    """Emit PROPOSAL.md — one organ, evidence-cited, unbuilt."""
    ranked = scan_ledgers(session)
    top_name, top_count, top_entries = ranked[0]
    tails = tail_census(session, top_entries)
    cited = top_entries[:25]

    lines = []
    lines.append("# PROPOSAL — one organ, nominated by the ledgers")
    lines.append("")
    lines.append("**Law 3 of Part XII: this proposal is not an "
                 "implementation. Nothing below is built.**")
    lines.append("")
    lines.append("## The evidence, ranked (every ledger, by count)")
    lines.append("")
    for name, count, _ in ranked:
        marker = "  <-- the nomination" if name == top_name else ""
        lines.append(f"- {name}: **{count}**{marker}")
    lines.append("")
    lines.append(f"## The nominated hygiene item: `{top_name}` "
                 f"({top_count} entries)")
    lines.append("")
    lines.append(f"Twenty-five cited entries (of {top_count}), "
                 f"word and ledger line:")
    lines.append("")
    for w, p in cited:
        lines.append(f"- `{w}` — {p}")
    lines.append("")
    lines.append("Recurring phoneme tails across the class (the shape "
                 "of the missing rule):")
    lines.append("")
    for tail, n in tails:
        lines.append(f"- `{' '.join(tail)}` x {n}")
    lines.append("")
    lines.append("## Mechanism sketch (one paragraph)")
    lines.append("")
    lines.append(
        "A SUFFIX-DISCOVERY ORGAN. The no-such-stem class is dominated "
        "by words whose true suffix is not one of the six the "
        "transform mines (-ment, -tion, -ity and kin live in the tails "
        "above): the stem exists as a WORD-PIECE the lexicon never "
        "lists bare, so the oracle rightly says no-such-stem and the "
        "creature rightly adopts an atom. The organ would mine "
        "candidate suffix categories from this ledger's own tail "
        "census, audit each candidate with the Part IX consonance "
        "auditor against the pinned corpus (attestation examines the "
        "teacher), fit modal forms through the existing Transform "
        "protocol, and re-read the ledger: adopted atoms that become "
        "derivable under a discovered suffix retire into aliases "
        "through the SAME certified prune pass that already exists. "
        "No new physics — the miner, the auditor, the table, and the "
        "prune pass, composed.")
    lines.append("")
    lines.append("## Proposed acceptance inequality")
    lines.append("")
    lines.append(
        "A discovered suffix S is ADOPTED only if: (a) its mined pair "
        "count is >= 200; (b) its consonance audit on the pinned "
        "corpus clears the Part IX floor (30%) and its held-out SEAM "
        "binding cosine sits within the shipped six's band (>= 0.99); "
        "and (c) re-reading the no-such-stem ledger converts >= 15% "
        "of the class into certified aliases with ZERO new "
        "confabulations (the honesty invariant is unconditional and "
        "stays so). Refused candidates are ledgered with their audit "
        "numbers, per law 2.")
    lines.append("")
    lines.append(f"*Emitted by the ritual from a {len(session.known)}-"
                 f"word session; the human gate decides.*")
    text = "\n".join(lines)
    Path(out_path).write_text(text, encoding="utf-8")
    return top_name, top_count, text
