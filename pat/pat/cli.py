"""A-4 + XVI-b: talk to it — through a door that opens on the real Pat.

A REPL: prompt in, structured response out, one line per clause. The
format is honest by construction — every line is an analysis, a neighbor
list, a learned/known acknowledgment, an oracle receipt, a journey's
legs with numbers, or a refusal that names its reason. No padding, no
pretense of chat.

    pat [store_path] [--store PATH]

The store: an explicit path wins; otherwise ~/.pat. On the very first
boot (no ~/.pat yet) the shipped canonical store — Pat's lived session:
seeds, the pinned 5,000-word read, the studied page — is copied there,
so a fresh clone wakes the Pat that passed the batteries, not a newborn.
(Part XVI's bounced gate: the launcher used to boot an empty store and
list the v0 verbs; the smoke test caught Pat forgetting who he is.)
"""
import argparse
import shutil
import sys
from pathlib import Path

CANONICAL_STORE = Path(__file__).resolve().parent.parent / "data" / "store"

VERB_LINE = ("verbs: analyze <w>, relates <w>, remember <w>, know <w>, "
             "walk <a> to <b>, verify <w> = <base>+<suffix>, "
             "audit <cmu|unimorph|homophones>. 'quit' saves and exits.")


def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="pat",
        description="Pat — a provenance-complete, geometric "
                    "smart-controller agent.")
    ap.add_argument("store_pos", nargs="?", default=None,
                    metavar="store_path",
                    help="episode-store directory (positional form)")
    ap.add_argument("--store", default=None,
                    help="episode-store directory (flag form; wins over "
                         "the positional)")
    return ap.parse_args(argv)


def resolve_store(args, home=None):
    """-> (store_path, seeded): explicit path as given; default ~/.pat,
    seeded from the shipped canonical store on first boot."""
    explicit = args.store or args.store_pos
    if explicit:
        return Path(explicit), False
    home = Path.home() if home is None else Path(home)
    store = home / ".pat"
    if not store.exists() and (CANONICAL_STORE / "store.json").exists():
        shutil.copytree(CANONICAL_STORE, store)
        return store, True
    return store, False


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    store, seeded = resolve_store(args)
    print("waking Pat (organs load once)...")
    from .loop import Agent
    agent = Agent(str(store))
    if seeded:
        print(f"first boot: seeded {store} from the shipped canonical "
              f"store (the lived session, receipts included).")
    n = agent.bases_total()
    print(f"awake. I know {n} base{'s' if n != 1 else ''}. {VERB_LINE}")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            text = "quit"
        if not text:
            continue
        if text.lower() in ("quit", "exit"):
            agent.save()
            print(f"saved. the ledger holds {agent.bases_total()} bases "
                  f"({len(agent.provenance)} taught receipts).")
            return
        try:
            for line in agent.respond(text).lines():
                print(line)
        except OSError as e:
            # the slim clone: corpus_big.txt ships compressed; walk and
            # audit need it reconstituted — refuse by name, don't crash
            if "corpus_big" in str(e):
                print("refuse: corpus_big.txt is not built on this "
                      "machine — run: python mirror/scripts/"
                      "build_corpus_big.py")
            else:
                raise


if __name__ == "__main__":
    main()
