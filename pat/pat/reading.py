"""W-2 + X-4: the reading loop (probes 40-44) — the creature reads,
reorganizes itself, and never waits forever.

Per word of a frequency-ordered stream: analyze (gated, word-aware).
REFUSED words that are attested bases either DEFER (derived-looking:
a final phoneme window matches an attested remainder — the
wait-for-the-stem instinct) or SELF-TEACH with read provenance,
checking the shape census at write time (a self-census entry when the
newcomer collides with something already known — the creature's own
ambiguity ledger).

THE ENGINE (X-4, probe 44): under the exact gate, analysis is
pron-index lookups — a bare index over what the session knows, stem
candidates by attested-remainder peeling, the artifact-ladder license.
O(1) per word, so the FULL qualifying vocabulary is readable; the
probe-41 row bank this replaces was the shape-proposal path scored by
matmul, and the exact gate had already made the scores ceremonial.
(One measured delta, flagged in HANDOFF Part IX: licensed non-modal
allomorphs whose shape dipped under theta are now accepted — the dict
engine trusts the gate, not the score.)

THE DEFERRAL POLICY (X-4, law 3): adoption needs a reason, never
silence, never forever —
  `unlocked by <stem>`            the stem arrived; the derived
                                  reading stands (the ledger names it);
  `read:no-such-stem`             NO lexicon word has any putative
                                  stem's pronunciation — the derived
                                  reading is impossible; adopt at once;
  `read: stem <w> exists unread`  the stem exists in the lexicon but
                                  three epochs of revisits never met
                                  it; adopt, naming the unmet stem.
policy=2 (the default law) runs both; policy=1 only the oracle;
policy=0 is Part VII's shipped defer-forever, kept as the pinned
protocol of the Part VII battery (and the P0 catastrophe row: 14k+
words stranded at full scale).

Per epoch, the metabolism: REVISIT deferred words, then PRUNE
read-taught atoms that became derivable — the atom retires but a
ledger alias keeps `know` and `analyze` truthful. Law 3 of Part VII: a
prune must be HOMOPHONE-CERTIFIED (pron identical to the derivation's
mined surface; place != plays never prunes). The `looks_derived`
len >= 5 guard is the dial: 4-phoneme derived words become early atoms
and the prune pass retires them into aliases once their stems arrive —
truths, not confabs.

Provenance classes: birth / taught / read / lesson.
"""
from mirror import PhonGate
from mirror.diagnostics import shape_seq
from mirror.loop import THETA_DEFAULT

STALE_EPOCHS = 3


class ReadingSession:
    def __init__(self, organs, seed_bases, theta=THETA_DEFAULT,
                 policy=2, gate=None):
        """gate: pass a PhonGate to run under a WIDENED arbitration
        ecology (Part XIII: discovered suffixes registered into it);
        default builds the shipped six-suffix gate — every pinned
        battery keeps its vintage."""
        self.organs = organs
        self.emb = organs.embedder
        self.transform = organs.transform
        self.gate = (PhonGate.from_transform(organs.transform)
                     if gate is None else gate)
        self.theta = theta
        self.policy = policy
        self.byb = {}
        for base, sfx, w, _ in organs.transform.pairs:
            self.byb.setdefault(base, {})[sfx] = w
        self.all_rems = set()
        self.rem2sfx = {}
        for sfx, rems in self.gate.attested.items():
            self.all_rems |= rems
            for r in rems:
                self.rem2sfx.setdefault(r, set()).add(sfx)
        self.max_rem = max(len(r) for r in self.all_rems)

        # the stem-existence oracle: every pronunciation in the lexicon
        self._pron_index = {}
        for w, p in self.emb.corpus.items():
            self._pron_index.setdefault(tuple(p), []).append(w)

        self._bare_ix = {}                  # pron -> [known words]
        self.known = {}                     # word -> provenance
        self.retired = {}                   # word -> prune-ledger entry
        self.deferred = {}                  # word -> epochs waited
        self.adoptions = {"unlocked": 0, "no-such-stem": 0,
                          "stale-adopt": 0}
        self.census = []
        self.unlocked = []
        self.homophones = []
        self.epoch = 0
        self._taught_epoch = {}
        self._shape_index = {}              # shape key -> first known base
        self.pages = []                     # L-4: studied Pages
        self.lawbook = None
        self.lesson_conflicts = []
        self._induced = None                # (sg, pl) number lexicon
        for b in seed_bases:
            self.teach(b, "birth")

    # ── the bank (a pron index now — X-4) ────────────────────────────
    def teach(self, base, provenance):
        """Write a base into the index with its provenance;
        census-checked by the caller."""
        if base in self.known:
            return
        self.known[base] = provenance
        self._taught_epoch[base] = self.epoch
        self._bare_ix.setdefault(tuple(self.emb.corpus[base]),
                                 []).append(base)

    def _live(self, words, exclude):
        return [b for b in words
                if b != exclude and b not in self.retired]

    # ── analyze: dict-exact under the gate, word-aware ───────────────
    def analyze_word(self, word, exclude=None):
        """-> (mode, base, sfx, verdict): mode BARE|BOUND|REFUSE,
        verdict OK|HOMOPHONE|None. Identity-certified analyses beat
        homophone claims; retired and excluded stems never testify."""
        pron = tuple(self.emb.corpus[word])
        hits = self._live(self._bare_ix.get(pron, ()), exclude)
        if hits:
            if word in hits:
                return "BARE", word, None, "OK"
            return "BARE", hits[0], None, "HOMOPHONE"
        first_homo = None
        for stem_p, rem in self._stem_candidates(pron):
            for b in self._live(self._bare_ix.get(stem_p, ()), exclude):
                for sfx in sorted(self.rem2sfx[rem]):
                    if not self.gate.licensed(self.emb.corpus[b], sfx,
                                              list(rem)):
                        continue
                    verdict = self.gate.verdict(word, "BOUND", b, sfx)
                    if verdict == "OK":
                        return "BOUND", b, sfx, "OK"
                    if first_homo is None:
                        first_homo = ("BOUND", b, sfx)
        if first_homo is not None:
            return (*first_homo, "HOMOPHONE")
        return "REFUSE", None, None, None

    def _stem_candidates(self, pron):
        out = []
        for k in range(1, self.max_rem + 1):
            rem = tuple(pron[-k:])
            if rem in self.rem2sfx and len(pron) - k >= 2:
                out.append((tuple(pron[:-k]), rem))
        return out

    def _looks_derived(self, word):
        p = self.emb.corpus[word]
        return (len(p) >= 5
                and any(tuple(p[-k:]) in self.all_rems
                        for k in range(1, self.max_rem + 1)))

    def _stem_exists(self, pron):
        """The oracle: does ANY lexicon word carry a putative stem's
        pronunciation?"""
        return any(sp in self._pron_index
                   for sp, _ in self._stem_candidates(pron))

    def _unmet_stem(self, pron):
        """The name of a lexicon stem this word is still waiting on."""
        for sp, _ in self._stem_candidates(pron):
            words = self._pron_index.get(sp)
            if words:
                return words[0]
        return None

    # ── the loop ─────────────────────────────────────────────────────
    def read(self, words, epochs=None, epoch_size=1000, counts=None,
             epoch_probe=None):
        """Read `words` in order, in epochs of epoch_size; after each
        epoch run the metabolism (revisit, prune) and snapshot."""
        counts = counts or {}
        chunks = [words[i:i + epoch_size]
                  for i in range(0, len(words), epoch_size)]
        if epochs is not None:
            chunks = chunks[:epochs]
        snapshots = []
        for chunk in chunks:
            self.epoch += 1
            for w in chunk:
                mode, b, sfx, verdict = self.analyze_word(w)
                if verdict == "HOMOPHONE":
                    self.homophones.append(
                        {"epoch": self.epoch, "word": w, "mode": mode,
                         "base": b, "suffix": sfx,
                         "surface": self.gate.surface_of(
                             b, sfx, self.emb.corpus[w])
                         if mode == "BOUND" else b})
                if mode != "REFUSE" or w in self.known \
                        or w in self.retired:
                    continue
                # X-4 (probe 44): any attested refused word is teach-
                # eligible — the byb-bases-only filter was Part VII's
                # training wheel, off at 10x scale
                pron = tuple(self.emb.corpus[w])
                if self._looks_derived(w):
                    if self.policy >= 1 and not self._stem_exists(pron):
                        self._teach_read(w, "read:no-such-stem", counts)
                        self.adoptions["no-such-stem"] += 1
                    else:
                        self.deferred.setdefault(w, 0)
                else:
                    self._teach_read(
                        w, f"read: attested {counts.get(w, 0)}", counts)
            self._revisit()
            self._prune()
            snap = {
                "epoch": self.epoch, "known": len(self.known),
                "deferred": len(self.deferred),
                "unlocked": len(self.unlocked),
                "pruned": len(self.retired),
                "census": len(self.census),
                "homophones": len(self.homophones),
                "adoptions": dict(self.adoptions),
            }
            if epoch_probe is not None:
                snap.update(epoch_probe(self))
            snapshots.append(snap)
        return {"snapshots": snapshots,
                "provenance_totals": self.provenance_totals()}

    def _teach_read(self, w, provenance, counts):
        key = shape_seq(self.emb.corpus[w])
        hit = self._shape_index.get(key)
        if hit is not None:
            self.census.append({"epoch": self.epoch, "word": w,
                                "collides_with": hit})
        else:
            self._shape_index[key] = w
        self.teach(w, provenance)

    def _revisit(self):
        """The deferred queue meets the stems the stream taught since —
        and under P2, nothing waits past STALE_EPOCHS revisits: adopt,
        naming the unmet stem (law 3: adoption needs a reason)."""
        still = {}
        for w, age in self.deferred.items():
            mode, b, sfx, verdict = self.analyze_word(w)
            if mode == "BOUND":
                self.unlocked.append(
                    {"epoch": self.epoch, "word": w,
                     "unlocked_by": f"{b}+{sfx}", "verdict": verdict})
                self.adoptions["unlocked"] += 1
            elif self.policy >= 2 and age + 1 >= STALE_EPOCHS:
                stem = self._unmet_stem(tuple(self.emb.corpus[w]))
                self._teach_read(
                    w, f"read: stem {stem} exists unread", {})
                self.adoptions["stale-adopt"] += 1
            else:
                still[w] = age + 1
        self.deferred = still

    def _prune(self):
        """Retire read-taught atoms that became derivable — law 3 of
        Part VII: only when the atom's pronunciation is IDENTICAL to
        the derivation's mined surface (homophone-certified)."""
        for b in [w for w, p in self.known.items()
                  if p.startswith("read")]:
            mode, gb, gs, verdict = self.analyze_word(b, exclude=b)
            if mode != "BOUND":
                continue
            surface = self.gate.surface_of(gb, gs, self.emb.corpus[b])
            if surface is None or \
                    tuple(self.emb.corpus[b]) != \
                    tuple(self.emb.corpus[surface]):
                continue                     # uncertified: never prune
            self.retired[b] = {
                "alias": f"derivable: {gb}+{gs}",
                "surface": surface,
                "read_epoch": self._taught_epoch[b],
                "pruned_epoch": self.epoch,
                "provenance": (f"derivable: {gb}+{gs}; read-taught "
                               f"epoch {self._taught_epoch[b]}, pruned "
                               f"epoch {self.epoch}"),
            }
            del self.known[b]

    # ── L-4: study — the fourth provenance class ─────────────────────
    def study(self, page):
        """Ingest a Page (mirror.lessons): every listed word enters
        `known` with provenance `lesson:<page>`; page-vs-induced
        conflicts are ledgered exactly as reading's census is; number
        answers become page-first through the LawBook. Lessons never
        load silently — the returned report carries the conflict count,
        and the ledger keeps the triples."""
        from mirror import LawBook
        from mirror.agreement import build_number_lexicon
        if self._induced is None:
            sg, pl, _ = build_number_lexicon(self.transform.pairs)
            self._induced = (sg, pl)
        self.pages.append(page)
        self.lawbook = LawBook(self.pages, *self._induced)
        new = [c for c in self.lawbook.conflict_ledger
               if c[3] == page.name]
        for word, page_says, induced_says, page_name in new:
            self.lesson_conflicts.append(
                {"epoch": self.epoch, "word": word,
                 "page_says": page_says, "induced_says": induced_says,
                 "page": page_name})
        taught = 0
        for word in page.rows:
            if word in self.emb.corpus and word not in self.known \
                    and word not in self.retired:
                self.teach(word, f"lesson:{page.name}")
                taught += 1
        return {"page": page.name,
                "lines": page.n_lines or len(page),
                "words": len(page), "taught": taught,
                "conflicts": len(new)}

    def number_of(self, word):
        """-> (number, provenance): the LawBook rules when pages are
        studied ('lesson:<page>' or 'induced'); induced-only before."""
        if self.lawbook is not None:
            n = self.lawbook.number_of(word)
            if n is None:
                return None, None
            return n, (self.lawbook.provenance_of(word) or "induced")
        from mirror.agreement import build_number_lexicon, number_of
        if self._induced is None:
            sg, pl, _ = build_number_lexicon(self.transform.pairs)
            self._induced = (sg, pl)
        n = number_of(word, *self._induced)
        return (n, "induced") if n else (None, None)

    # ── truthful answers over the whole ledger ───────────────────────
    def knows(self, word):
        """-> (yes, provenance): retired atoms still answer truthfully
        through their ledger alias."""
        if word in self.known:
            return True, self.known[word]
        if word in self.retired:
            return True, self.retired[word]["provenance"]
        return False, None

    def provenance_totals(self):
        totals = {}
        for p in self.known.values():
            cls = p.split(":")[0].split()[0]
            totals[cls] = totals.get(cls, 0) + 1
        # the retired ledger splits by ITS provenance class too:
        # 'pruned' (derivable aliases) vs 'discovered' (Part XIII's
        # fifth class — suffix-discovery retirements)
        for entry in self.retired.values():
            cls = ("discovered"
                   if entry["provenance"].startswith("discovered:")
                   else "pruned")
            totals[cls] = totals.get(cls, 0) + 1
        return totals

    # ── XVI-b: the session survives death (the front-door fix) ───────
    # The live-log promise ("read-taught epoch 1, pruned epoch 5")
    # is a property of a session; before this, sessions died with the
    # process and a reborn Agent answered as a newborn. Pages already
    # persisted (L-4); this is the same contract for the read ledger.
    def to_state(self):
        """Everything a rebirth needs, JSON-safe. Derived indices
        (pron/byb/remainder) rebuild from the organs; only ledgers and
        their insertion order travel."""
        return {
            "version": 1,
            "policy": self.policy,
            "theta": self.theta,
            "epoch": self.epoch,
            "known": self.known,
            "taught_epoch": self._taught_epoch,
            "retired": self.retired,
            "deferred": self.deferred,
            "adoptions": self.adoptions,
            "census": self.census,
            "unlocked": self.unlocked,
            "homophones": self.homophones,
            "lesson_conflicts_seen": len(self.lesson_conflicts),
            "shape_index": [[k, w]
                            for k, w in self._shape_index.items()],
        }

    @staticmethod
    def _freeze(x):
        """JSON turns nested tuples into nested lists; shape keys are
        tuples of shapes (themselves tuples) — freeze back, deep."""
        if isinstance(x, (list, tuple)):
            return tuple(ReadingSession._freeze(i) for i in x)
        return x

    @classmethod
    def from_state(cls, organs, state, gate=None):
        """Rebuild a session from to_state() output. _bare_ix recovers
        known (live) then retired entries; _live() filters retired at
        query time, so BARE-hit naming order among live words is
        preserved (JSON keeps insertion order)."""
        s = cls(organs, seed_bases=[], theta=state["theta"],
                policy=state["policy"], gate=gate)
        s.epoch = state["epoch"]
        for w, p in state["known"].items():
            s.known[w] = p
            s._bare_ix.setdefault(tuple(s.emb.corpus[w]), []).append(w)
        for w, entry in state["retired"].items():
            s.retired[w] = entry
            s._bare_ix.setdefault(tuple(s.emb.corpus[w]), []).append(w)
        s._taught_epoch = {w: int(e)
                           for w, e in state["taught_epoch"].items()}
        s.deferred = {w: int(a) for w, a in state["deferred"].items()}
        s.adoptions = state["adoptions"]
        s.census = state["census"]
        s.unlocked = state["unlocked"]
        s.homophones = state["homophones"]
        s._shape_index = {cls._freeze(k): w
                          for k, w in state["shape_index"]}
        return s
