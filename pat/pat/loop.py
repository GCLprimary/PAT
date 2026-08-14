"""A-1: the creature's heartbeat.

perceive (input string) -> segment (clauses on connectives) -> per
clause: recall -> act (repertoire) -> respond (structured record) ->
write (ONLY on law-2 teachable moments) -> next.

Law 2 — refusal is the teachable moment: an episode is written only when
a refusal met a confirmation (`remember <b>` after the creature said it
didn't know). Every write logs its provenance: which input taught it,
which refusal made it teachable, when. Silent inference never writes.

Sessions persist: the episode store is a_mem's on-disk library. An Agent
restarted on the same path knows everything it was ever taught — the
original promise of the whole project, asserted at the creature level.
"""
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from amem import constants as AK
from amem.api import Memory
from amem.encoder import Encoder
from amem.hooks import EpisodeHooks

from .organs import get_organs
from .repertoire import Act, ExactRouter, Repertoire

_CONNECTIVES = re.compile(r"\s+(?:and|then)\s+")

GRID = 47
ZONE = (2, 40)


@dataclass
class ClauseResponse:
    clause: str
    act: Act
    line: str


@dataclass
class Response:
    text: str                          # the raw input
    clauses: list = field(default_factory=list)

    def lines(self):
        return [c.line for c in self.clauses]


class Agent:
    def __init__(self, store_path, seed_bases=None, router=None,
                 organs=None):
        self.organs = organs if organs is not None else get_organs()
        self.repertoire = Repertoire(self.organs)
        self.router = router if router is not None else ExactRouter()
        self.store_path = Path(store_path)
        enc = Encoder(grid=GRID, zone_min=ZONE[0], zone_max=ZONE[1],
                      min_sep=AK.PLACE_MIN_SEP, seed=0)
        self.memory = Memory(grid=GRID, seed=5, path=str(self.store_path),
                             autosave=False)
        self.hook = EpisodeHooks(self.memory, encoder=enc)

        # restart recovery: everything ever taught, from the library
        self.known = {}
        for mid in self.memory.library.mids():
            word = self.memory.library.get(mid).meta.get("word")
            if word:
                self.known[word] = mid

        self._prov_file = self.store_path / "provenance.json"
        self.provenance = []
        if self._prov_file.exists():
            self.provenance = json.loads(
                self._prov_file.read_text(encoding="utf-8"))
        self._last_refusals = {}       # word -> (input, reason)
        self.reading = None            # W-2: attached by read()

        # XVI-b: the read ledger survives death too — restored BEFORE
        # pages re-study so lessons land on the lived session
        self._reading_file = self.store_path / "reading.json"
        if self._reading_file.exists():
            from .reading import ReadingSession
            self.reading = ReadingSession.from_state(
                self.organs,
                json.loads(self._reading_file.read_text(
                    encoding="utf-8")))

        # L-4: lesson provenance survives death — studied pages are
        # ledgered in pages.json (separate from the word-provenance
        # contract) and re-studied from their pinned files at rebirth
        # (falling back to mirror's DATA_DIR by file name, so a store
        # built on one machine re-studies on another)
        self._pages_file = self.store_path / "pages.json"
        self.pages_ledger = []
        if self._pages_file.exists():
            self.pages_ledger = json.loads(
                self._pages_file.read_text(encoding="utf-8"))
            for entry in self.pages_ledger:
                p = Path(entry["path"]) if entry.get("path") else None
                if p is None or not p.exists():
                    from mirror.config import DATA_DIR as _MDATA
                    name = entry.get("file") or (p.name if p else "")
                    p = _MDATA / name if name else None
                if p is not None and p.exists():
                    self._study_page(p, ledgered=False)

        if seed_bases:
            for b in seed_bases:
                self.teach(b, taught_by="<seeded>", refusal=None)

    # ── persistence (Windows indexer races retried) ──────────────────
    def save(self):
        for attempt in range(4):
            try:
                self.memory.library.save()
                break
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.2)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._prov_file.write_text(
            json.dumps(self.provenance, indent=1), encoding="utf-8")
        if self.reading is not None:
            self._reading_file.write_text(
                json.dumps(self.reading.to_state()), encoding="utf-8")

    def bases_total(self):
        """The whole ledger's yes-count: taught episodes, read/lesson
        provenance, and pruned aliases (which still answer truthfully)."""
        bases = set(self.known)
        if self.reading is not None:
            bases |= set(self.reading.known)
            bases |= set(self.reading.retired)
        return len(bases)

    # ── the write half of the loop (law 2) ───────────────────────────
    def teach(self, base, taught_by, refusal):
        if base in self.known:
            return self.known[base]
        emb = self.organs.embedder
        if base not in emb.corpus:
            return None
        mid = self.hook.write_episode(
            self.organs.shape_vec(base),
            payload_meta={"word": base, "taught_by": taught_by})
        self.known[base] = mid
        self.provenance.append({
            "word": base, "mid": mid, "taught_by": taught_by,
            "refusal": refusal,
            "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        self.save()
        return mid

    # ── L-4: the study capability ────────────────────────────────────
    def study(self, page_path):
        """Study a pinned lesson page: the reading session ingests it
        (fourth provenance class), and the pages ledger persists so a
        reborn Agent re-studies it from the same pinned file."""
        return self._study_page(Path(page_path), ledgered=True)

    def _study_page(self, path, ledgered):
        from mirror import Page
        from .reading import ReadingSession
        if self.reading is None:
            self.reading = ReadingSession(self.organs,
                                          seed_bases=list(self.known))
        report = self.reading.study(Page.load(path))
        if ledgered:
            self.pages_ledger.append({
                "page": report["page"], "path": str(path),
                "file": Path(path).name,
                "conflicts": report["conflicts"],
                "when": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"),
            })
            self.store_path.mkdir(parents=True, exist_ok=True)
            self._pages_file.write_text(
                json.dumps(self.pages_ledger, indent=1),
                encoding="utf-8")
        return report

    # ── W-2: the read capability ─────────────────────────────────────
    def read(self, words, epochs=None, epoch_size=1000, counts=None,
             epoch_probe=None):
        """Read a frequency-ordered word stream (reading.py). The
        session's vocabulary lives in its own row bank — the a_mem
        episode store is untouched (its grid is sized for taught
        episodes, not a lexicon); after a read, know/analyze consult
        the reading ledger too, truthfully."""
        from .reading import ReadingSession
        if self.reading is None:
            self.reading = ReadingSession(self.organs,
                                          seed_bases=list(self.known))
        return self.reading.read(words, epochs=epochs,
                                 epoch_size=epoch_size, counts=counts,
                                 epoch_probe=epoch_probe)

    # ── perceive -> segment -> act -> respond ────────────────────────
    def segment(self, text):
        text = text.replace("﻿", "").replace("​", "")
        return [c.strip() for c in _CONNECTIVES.split(text.strip())
                if c.strip()]

    def _handle(self, clause, source_text):
        verb, args = self.router.route(clause)
        if verb == "analyze":
            act = self._analyze_act(args[0])
            if act.kind == "REFUSE":
                self._last_refusals[args[0]] = (source_text, act.reason)
        elif verb == "relates":
            act = self.repertoire.relates(args[0])
        elif verb == "know":
            act = self._know_act(args[0])
        elif verb == "walk":
            act = self.repertoire.walk(*args)
        elif verb == "remember":
            base = args[0]
            if base in self.known:
                act = Act("remember", "KNOWN", (base,))
            elif base not in self.organs.embedder.corpus:
                act = Act("remember", "REFUSE",
                          reason=f"'{base}' is not a form I can learn")
            else:
                refusal = self._last_refusals.get(base)
                self.teach(base, taught_by=source_text,
                           refusal=list(refusal) if refusal else None)
                act = Act("remember", "LEARNED", (base,))
        elif verb == "audit":
            act = self._audit_act(args[0] if args else "")
        elif verb == "verify":
            act = self._verify_act(args)
        else:
            act = self.repertoire.alien(args[0] if args else "")
        return act

    # ── J-2: the audit and verify verbs (Part XIV) ───────────────────
    def _audit_act(self, target):
        from .shell import AUDIT_TARGETS, AuditDesk
        if target not in AUDIT_TARGETS:
            return Act("audit", "REFUSE",
                       reason="I can audit cmu, unimorph, homophones")
        if not hasattr(self, "_audit_desk"):
            self._audit_desk = AuditDesk(self.organs)
        path, n, voice = self._audit_desk.run(target)
        return Act("audit", "REPORT", (target, str(path), n, voice))

    def _verify_act(self, parsed):
        from .shell import Oracle
        if parsed is None:
            return Act("verify", "REFUSE",
                       reason="say it as: verify <word> = "
                              "<base>+<suffix>")
        if not hasattr(self, "_oracle"):
            self._oracle = Oracle(self.organs)
        verdict, line = self._oracle.verify(*parsed)
        return Act("verify", verdict, parsed, reason=line)

    def _analyze_act(self, word):
        """The read session's bank, when one exists, extends what the
        creature knows; without one this is the plain repertoire."""
        if self.reading is None:
            return self.repertoire.analyze(word, self.known)
        if word not in self.organs.embedder.corpus:
            return Act("analyze", "REFUSE",
                       reason=f"'{word}' is not a form I can read")
        mode, b, sfx, verdict = self.reading.analyze_word(word)
        if mode == "REFUSE":
            return Act("analyze", "REFUSE", reason="no analysis stands")
        if verdict == "HOMOPHONE":
            pron = self.organs.embedder.corpus[word]
            surface = (self.reading.gate.surface_of(b, sfx, pron)
                       if mode == "BOUND" else b)
            name = f"'{surface}'" if surface else f"{b}+-{sfx}"
            return Act("analyze", "HOMOPHONE", (b, sfx, surface),
                       reason=f"sounds identical to {name} — I cannot "
                              f"tell them apart by ear")
        if mode == "BARE":
            return Act("analyze", "BARE", (b,))
        return Act("analyze", "DERIVED", (b, sfx))

    def _know_act(self, word):
        """know answers over the whole ledger: taught episodes, read
        provenance, and prune aliases — truthfully."""
        if self.reading is not None:
            yes, prov = self.reading.knows(word)
            if yes:
                return Act("know", "YES", (word,), reason=prov)
        return self.repertoire.know(word, self.known)

    def respond(self, text):
        response = Response(text)
        for clause in self.segment(text):
            act = self._handle(clause, text)
            response.clauses.append(
                ClauseResponse(clause, act, render(clause, act)))
        return response


def render(clause, act):
    """One honest line per clause — analysis, neighbors, acknowledgment,
    journey legs, or a refusal naming its reason. No padding."""
    k = act.kind
    if act.verb == "verify" and act.reason.startswith(
            ("CERTIFY", "REFUSE —", "HOMOPHONE")):
        return act.reason                # the oracle line IS the receipt
    if k == "REFUSE":
        return f"refuse: {act.reason}"
    if k == "REPORT":
        target, path, n, voice = act.detail
        return f"audited {target}: {voice}  [report: {path}]"
    if k == "HOMOPHONE":
        return f"'{clause.split()[-1]}' {act.reason}"
    if k == "BARE":
        return f"'{clause.split()[-1]}' is the bare form of "\
               f"'{act.detail[0]}'"
    if k == "DERIVED":
        base, sfx = act.detail
        return f"'{clause.split()[-1]}' = '{base}' + -{sfx}"
    if k == "NEIGHBORS":
        return f"'{clause.split()[-1]}' relates to: " + \
            ", ".join(act.detail)
    if k == "LEARNED":
        return f"learned '{act.detail[0]}' — you taught me just now"
    if k == "KNOWN":
        return f"I already know '{act.detail[0]}'"
    if k == "YES":
        if act.reason:
            return f"yes, I know '{act.detail[0]}' ({act.reason})"
        return f"yes, I know '{act.detail[0]}'"
    if k == "NO":
        return f"no, I do not know '{act.detail[0]}'"
    if k == "JOURNEY":
        prompt, legs = act.detail
        lines = [f"walking from '{' '.join(prompt)}':"]
        for i, (tokens, to_b, to_a) in enumerate(legs):
            lines.append(f"  leg {i + 1}: {' '.join(tokens)}  "
                         f"[->dest {to_b:+.3f}  ->origin {to_a:+.3f}]")
        return "\n".join(lines)
    return f"({k})"
