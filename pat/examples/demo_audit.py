"""J-4: the audit demo — Pat's first job, three beats. Under 45 s.

Beat 1: one audit line with its receipt read aloud. Beat 2: the
government line — the refusal that is also the finding. Beat 3: the
oracle transcript, the probe's ten proposals as a 10/10 regression.
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pat import Agent

t0 = time.time()

with tempfile.TemporaryDirectory() as store:
    pat = Agent(store)

    print("BEAT 1 — THE AUDIT LINE, receipt read aloud:")
    line = pat.respond("audit cmu").lines()[0]
    print(f"  > audit cmu\n  {line}")
    print("  one row of it: abnormally = abnormal + ly — the lexicon "
          "drops one /l/;")
    print("  the degemination family, 168 elisions strong, 138 of "
          "them certified by the")
    print("  stem-final/tail-initial test. Every row carries its "
          "receipt.")

    print("\nBEAT 2 — THE REFUSAL THAT IS ALSO THE FINDING:")
    line = pat.respond("verify government = govern+ment").lines()[0]
    print(f"  > verify government = govern+ment\n  {line}")
    print("  (the dropped /n/, on the record — the same fact that "
          "kept government out of")
    print("  Part XIII's harvest now reads as an audit finding with "
          "its phones attached)")

    print("\nBEAT 3 — THE ORACLE TRANSCRIPT (ten proposals, pinned):")
    for clause in ("verify painted = paint+ed",
                   "verify walking = walk+ing",
                   "verify melted = metal+ed",
                   "verify side = sigh+ed",
                   "verify famous = fam+ous",
                   "verify cheerfully = cheerful+er",
                   "verify darkness = dark+ness",
                   "verify quickly = quick+ly",
                   "verify government = govern+ment",
                   "verify finds = find+s"):
        print(f"  > {clause}\n    {pat.respond(clause).lines()[0]}")

print(f"\ndone in {time.time() - t0:.1f}s  (target < 45s)")
