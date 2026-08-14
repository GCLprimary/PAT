"""A-4: talk to it.

A REPL: prompt in, structured response out, one line per clause. The
format is honest by construction — every line is an analysis, a neighbor
list, a learned/known acknowledgment, a journey's legs with numbers, or
a refusal that names its reason. No padding, no pretense of chat.

    python -m pat.cli [store_path]
"""
import sys
from pathlib import Path


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    store = argv[0] if argv else str(Path.home() / ".pat")
    print("waking Pat (organs load once)...")
    from .loop import Agent
    agent = Agent(store)
    n = len(agent.known)
    print(f"awake. I know {n} base{'s' if n != 1 else ''}. "
          f"verbs: analyze, relates, remember, know, walk <a> to <b>. "
          f"'quit' saves and exits.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            text = "quit"
        if not text:
            continue
        if text.lower() in ("quit", "exit"):
            agent.save()
            print(f"saved. I know {len(agent.known)} bases; "
                  f"{len(agent.provenance)} of them have receipts.")
            return
        for line in agent.respond(text).lines():
            print(line)


if __name__ == "__main__":
    main()
