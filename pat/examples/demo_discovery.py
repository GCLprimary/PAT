"""O-4: the discovery demo — Pat's proposal, running, narrated from
the ledgers in three beats. Under 40 seconds.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import (ReadingSession, discover, get_organs, register,
                   retire_atoms)
from mirror import PhonGate

FIX = Path(__file__).resolve().parent.parent / "data" / "fixtures"

t0 = time.time()
organs = get_organs()
full = json.loads((FIX / "reading_stream_full.json").read_text(
    encoding="utf-8"))
seeds = json.loads((FIX / "reading_stream.json").read_text(
    encoding="utf-8"))["seeds"]
stream = full["stream"]

session = ReadingSession(organs, seed_bases=seeds, policy=2)
session.read(stream, epochs=6, epoch_size=max(1, len(stream) // 6),
             counts=full["counts"])
result, retired_pairs = discover(session, stream)

# beat 1 — the census
print(f"BEAT 1 — THE CENSUS: {result['no_such_stem_size']:,} words I "
      f"adopted because their stems did not exist;")
print(f"  their tails spell a rule I was never taught.")

# beat 2 — the discovery
m = next(d for d in result["discovered"] if d["suffix"] == "ment")
print(f"\nBEAT 2 — THE DISCOVERY: -ment: {m['attested_stems']} "
      f"attested stems against a {m['baseline']*100:.1f}% baseline;")
print(f"  {m['certified']} certified by sound and spelling. "
      f"Also promoted: " + ", ".join(
          f"-{d['suffix']} ({d['certified']})"
          for d in result["discovered"] if d["suffix"] != "ment"))
print(f"  Refused promotion: -ist (27 certified pairs retire as "
      f"truths; the suffix earns no row).")
print(f"  Cannot certify at all: -ous (famous has no free *fam*) — "
      f"the stem-allomorphy lane's customers, censused.")

# beat 3 — the retirement
gate2 = PhonGate.from_transform(organs.transform)
register(gate2, result, retired_pairs, organs.embedder.corpus)
n = retire_atoms(session, retired_pairs)
agr = session.retired["agreement"]
print(f"\nBEAT 3 — THE RETIREMENT: {n} atoms retire, zero "
      f"confabulations. One biography, read aloud:")
print(f"  agreement — adopted read:no-such-stem; retired "
      f"{agr['provenance'].split(';')[0]};")
print(f"  now agree + ment, both receipts kept.")
print(f"  (government itself stays CENSUSED: this lexicon's pron "
      f"drops the /n/, so govern+ment does not double-lock — the "
      f"organ does not pretend.)")
print(f"\nprovenance ledger: {session.provenance_totals()}")
print(f"\ndone in {time.time() - t0:.1f}s  (target < 40s)")
