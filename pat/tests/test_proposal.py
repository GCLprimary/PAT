"""B-0: the proposal ritual — emits, cites, and builds nothing.

Law 3 is hard: the ritual runs on the full-vocabulary session, writes
PROPOSAL.md with >= 25 cited ledger entries by count and class, and
the proposed organ does NOT exist anywhere in the codebase — asserted
by the absence of any suffix-discovery module. The proposal ships
verbatim in HANDOFF Part XII for the human gate.
"""
import json
from pathlib import Path

import pytest

from pat import ReadingSession
from pat.propose_organ import propose, scan_ledgers

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"
PROPOSAL = Path(__file__).resolve().parent.parent / "PROPOSAL.md"


@pytest.fixture(scope="module")
def session(organs):
    full = json.loads((FIX / "reading_stream_full.json").read_text(
        encoding="utf-8"))
    seeds = json.loads((FIX / "reading_stream.json").read_text(
        encoding="utf-8"))["seeds"]
    s = ReadingSession(organs, seed_bases=seeds, policy=2)
    s.read(full["stream"], epochs=6,
           epoch_size=max(1, len(full["stream"]) // 6),
           counts=full["counts"])
    return s


def test_ritual_emits_one_evidence_cited_proposal(session):
    top_name, top_count, text = propose(session, PROPOSAL)
    print(f"\nnominated: {top_name} ({top_count} entries)")
    assert PROPOSAL.exists()
    assert text.count("\n- `") >= 25, "fewer than 25 cited entries"
    assert "acceptance inequality" in text.lower()
    assert "not an implementation" in text
    # the ranking is deterministic and the nomination is the largest
    ranked = scan_ledgers(session)
    assert ranked[0][0] == top_name
    assert ranked[0][1] == max(c for _, c, _ in ranked)


def test_law_three_honored_then_gated():
    """Part XII's law 3 said: never built in the Part that proposes
    it. Part XIII's founding document is the ACCEPTED proposal — the
    human gate said yes, and agent/discovery.py exists BY THAT
    DECISION, citing PROPOSAL.md as its founding document. What must
    still hold forever: the SHIPPED transform inventory stays the six
    mined suffixes (discovery registers opt-in, per gate, never into
    the shipped artifacts), and the proposal predates the organ."""
    import pat as agent_pkg
    disc = Path(agent_pkg.__file__).parent / "discovery.py"
    assert disc.exists(), "the gated organ went missing"
    head = disc.read_text(encoding="utf-8")[:600]
    assert "PROPOSAL.md" in head, \
        "discovery.py no longer cites its founding document"
    assert PROPOSAL.exists()
    from mirror.transform import SUFFIXES
    assert len(SUFFIXES) == 6, \
        "discovery leaked into the SHIPPED suffix inventory"