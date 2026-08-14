"""A-2: the repertoire — five verbs, and the alien law.

The creature does five things: analyze, relates, remember, know, walk.
Anything else is refused BY NAME ("'translate' is not something I do") —
one bad clause poisons nothing (law 4), and the refusal spine is total
(law 1): every analysis either stands at theta = 0.98 or is refused.

Routing is exact-verb in the closed word-world, shipped behind the
Router protocol (the decode-boundary pattern) so richer routing can
attach later without touching the loop.

F-2: analyze runs GATED (mirror's phon gate, probe 39). Shape proposes,
phon disposes: shape-accepted candidates are walked in evidence order
(shape score, then stem-phon consonance) and the winner must pass
stem-scoped phon identity plus suffix arbitration. Homoshape imposters
that survived on argmax tie order (the cell/seal luck) are now refusals
or correct attributions by measurement.
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from mirror import Itinerary, PhonGate
from mirror.loop import THETA_DEFAULT

VERBS = ("analyze", "relates", "remember", "know", "walk",
         "audit", "verify")


@dataclass(frozen=True)
class Act:
    verb: str                 # the routed verb, or "alien"
    kind: str                 # BARE|DERIVED|NEIGHBORS|LEARNED|KNOWN|YES|NO|
                              # JOURNEY|REFUSE
    detail: tuple = ()        # verb-specific payload
    reason: str = ""          # refusals name their reason


@runtime_checkable
class Router(Protocol):
    """route(clause) -> (verb, args) — exact-verb in the closed world."""

    def route(self, clause):
        ...


class ExactRouter:
    def route(self, clause):
        toks = clause.strip().split()
        if not toks:
            return ("alien", ("",))
        verb = toks[0].lower()
        if verb == "walk":
            if len(toks) == 4 and toks[2].lower() == "to":
                return ("walk", (toks[1].lower(), toks[3].lower()))
            return ("alien", (verb,))
        if verb == "audit":
            return ("audit", (toks[1].lower(),)) if len(toks) == 2 \
                else ("audit", ("",))
        if verb == "verify":
            from .shell import parse_verify
            parsed = parse_verify(toks)
            return ("verify", parsed) if parsed \
                else ("verify", None)
        if verb in VERBS:
            return (verb, (toks[-1].lower(),)) if len(toks) >= 2 \
                else ("alien", (verb,))
        return ("alien", (verb,))


class Repertoire:
    """The five verbs, over a known-base set the loop maintains."""

    def __init__(self, organs, theta=THETA_DEFAULT, gate=None):
        self.organs = organs
        self.theta = theta
        self.gate = (PhonGate.from_transform(organs.transform)
                     if gate is None else gate)
        self._bound_cache = {}
        self._shape_cache = {}

    def _shape(self, base):
        if base not in self._shape_cache:
            self._shape_cache[base] = self.organs.shape_vec(base)
        return self._shape_cache[base]

    def _bound(self, base, suffix):
        key = (base, suffix)
        if key not in self._bound_cache:
            self._bound_cache[key] = self.organs.bound_vec(base, suffix)
        return self._bound_cache[key]

    # ── analyze: the gated mirror loop over what the creature knows ──
    @staticmethod
    def _settle(ranked, check, verdict_of):
        """Word-aware settlement (W-1): among gate-passing candidates,
        prefer the identity-certified one (verdict OK); otherwise the
        honest homophone claim; all-vetoed -> the top veto's reason."""
        passing, top_reason = [], None
        for key, s, c in ranked:
            res = check(key)
            if res.ok:
                passing.append(key)
            elif top_reason is None:
                top_reason = res.reason
        if not passing:
            return None, None, (top_reason or "no analysis stands")
        for key in passing:
            if verdict_of(key) == "OK":
                return key, "OK", None
        return passing[0], "HOMOPHONE", None

    def analyze(self, word, known):
        emb = self.organs.embedder
        if word not in emb.corpus:
            return Act("analyze", "REFUSE",
                       reason=f"'{word}' is not a form I can read")
        pron = list(emb.corpus[word])
        obs = emb.shape_vec(pron)
        gate = self.gate
        s1 = {b: float(obs @ self._shape(b)) for b in known}
        cands = [b for b, s in s1.items() if s >= self.theta]
        if cands:
            ranked = sorted(
                ((b, s1[b], gate.bare_cos(pron, emb.corpus[b]))
                 for b in cands), key=lambda t: (-t[1], -t[2], t[0]))
            key, verdict, why = self._settle(
                ranked, lambda b: gate.check_bare(pron, emb.corpus[b]),
                lambda b: gate.verdict(word, "BARE", b))
            if key is None:
                return Act("analyze", "REFUSE", reason=why)
            if verdict == "OK":
                return Act("analyze", "BARE", (key,))
            return Act("analyze", "HOMOPHONE", (key, None, key),
                       reason=f"sounds identical to '{key}' — I cannot "
                              f"tell them apart by ear")
        s2 = {}
        for b in known:
            for sfx in self.organs.transform.suffixes:
                v = self._bound(b, sfx)
                if v is not None:
                    s2[(b, sfx)] = float(obs @ v)
        cands = [k for k, s in s2.items() if s >= self.theta]
        if cands:
            ranked = sorted(
                ((k, s2[k], gate.stem_cos(pron, emb.corpus[k[0]]))
                 for k in cands), key=lambda t: (-t[1], -t[2], t[0]))
            key, verdict, why = self._settle(
                ranked,
                lambda k: gate.check_bound(pron, emb.corpus[k[0]], k[1]),
                lambda k: gate.verdict(word, "BOUND", k[0], k[1]))
            if key is None:
                return Act("analyze", "REFUSE", reason=why)
            if verdict == "OK":
                return Act("analyze", "DERIVED", key)
            surface = gate.surface_of(key[0], key[1], obs_pron=pron)
            name = f"'{surface}'" if surface else f"{key[0]}+-{key[1]}"
            return Act("analyze", "HOMOPHONE",
                       (key[0], key[1], surface),
                       reason=f"sounds identical to {name} — I cannot "
                              f"tell them apart by ear")
        return Act("analyze", "REFUSE", reason="no analysis stands")

    # ── relates: dense meaning neighbors, content-filtered ───────────
    def relates(self, word):
        g = self.organs.geometry
        if word not in g:
            return Act("relates", "REFUSE",
                       reason=f"'{word}' is not in my meaning vocabulary")
        function_words = set(g.vocab[:g.content_cut])
        v = g.vec(word)
        sims = sorted(((float(v @ g.vec(o)), o) for o in g.vocab[:2000]
                       if o != word and o not in function_words),
                      reverse=True)
        return Act("relates", "NEIGHBORS", tuple(o for _, o in sims[:3]))

    # ── know: the truth from the library ─────────────────────────────
    def know(self, word, known):
        return Act("know", "YES" if word in known else "NO", (word,))

    # ── walk: the crown as a verb (V-3 gates unchanged) ──────────────
    def walk(self, a, b):
        g = self.organs.geometry
        if a not in g or b not in g:
            missing = a if a not in g else b
            return Act("walk", "REFUSE",
                       reason=f"'{missing}' is not in my meaning vocabulary")
        prompt = self.organs.attested_prompt_for(a)
        if prompt is None:
            return Act("walk", "REFUSE",
                       reason=f"I have no attested path out of '{a}'")
        itinerary = Itinerary(self.organs.space, g.vec(a), g.vec(b))
        result = self.organs.journey.travel(prompt, itinerary)
        if result.status != "OK":
            return Act("walk", "REFUSE",
                       reason=f"the journey refused: {result.status}")
        return Act("walk", "JOURNEY",
                   (prompt, tuple((tuple(l.tokens), l.closure_to_b,
                                   l.closure_to_a) for l in result.legs)))

    # ── the alien law ────────────────────────────────────────────────
    def alien(self, verb):
        return Act("alien", "REFUSE",
                   reason=f"'{verb}' is not something I do")
