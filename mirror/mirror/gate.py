"""F-2 + W-1: the phon gate (probes 39-41) — exactness beats similarity.

Part V's finding: the voicing-neutral shape space is many-to-one at the
word level (51.6% of mined bases live in a homoshape collision group;
the open-vocabulary imposter ceiling is exactly 1.0), so shape alone
cannot carry the safety case. The law: scope frames, don't replace
them. Shape keeps families and binding — collapse is a feature there;
phon gets STEM IDENTITY — collapse is a bug there; the arbitration
artifacts get suffixes. No blunt thresholds.

Two mechanisms, applied AFTER the shape loop proposes (base, suffix):

  1. STEM IDENTITY — in the closed world this is SEQUENCE EQUALITY
     (probe 41's law: exactness beats similarity wherever exactness is
     available): obs[:L] == base pron, with L = len(base pron); bare
     acceptance requires full-sequence equality. The anagram leak is
     the proof the cosine could not carry it: 'melted' vs metal+ed
     scores 0.7802 >= theta_p in stem-cosine — sequence equality
     refuses it outright.
  2. SUFFIX ARBITRATION — the observed remainder must be licensed for
     the proposed (base, suffix). Arbitrate with the ARTIFACT, never a
     re-derivation (probe 41's set-vs-table hole):
       a. pair-exact: if (base pron, suffix) has mined remainders, the
          remainder must be one of THEM. This is what separates the
          place->play+s attack (play's -s remainder is z, never s)
          from the voicing-junk trues (coo+s -> coos with remainder s
          IS the mined pair) — evidence no signature-level rule can
          separate, because at (signature, class) granularity they are
          the same datum.
       b. unmined frontier, -s/-ed: the INDUCED ALLOMORPH TABLE
          (surface module's pinned artifact, 99.1%/99.2% held-out)
          licenses exactly the modal class for the base's final
          signature — strict at the frontier, catches unlicensed
          allomorphs by construction.
       c. unmined frontier, other suffixes: the suffix-wide attested
          set (pinned artifact; these suffixes' allomorphy is not
          signature-conditioned).
     The consulted table is checksummed against the pinned artifact by
     test — drift between the import and the pin fails the build.

  Ties are broken by evidence, never by order (law 3): candidates that
  score identically in shape are ranked by stem-phon consonance; a tie
  that survives BOTH mechanisms is refused, not dict-ordered.

VERDICTS (W-1): a standing analysis of a WORD gets a verdict — OK when
the analysis's surface identity is the word itself, HOMOPHONE when the
sound is identical but the identity differs ('find' as fine+ed: the
pronunciations are equal; the claim "sounds identical to fined" is
true and honest, and it is never a confabulation). Verdicts need
orthography, so they live at the word-aware layer (repertoire,
reading); the pron-level MirrorLoop cannot and does not emit them.

Refusal reasons distinguish the mechanisms: "stem mismatch" vs
"remainder not an attested -<sfx> form".

THE DORMANT COSINE PATH. The theta_p = 0.77 stem-cosine gate (probe 39,
Part VI) is retained below (exact=False) as the documented fallback for
future NOISY-INPUT worlds, where observations are not lexicon lookups
and sequence equality is unavailable. It is NOT consulted in the
closed world (probe 41's anagram finding, above). Its provenance
(re-measured on this machine at Part VI build, probe-exact):
  true bindings, phon space: mean 0.9572, p5 0.7778, min 0.7143
  cross-stem imposter cap:   0.7526  ('punching' vs pinch+ing)
  anagram-stem leak: 0.7802 ('melted' vs metal+ed) — the closed-world
    kill that retired this path from active duty
  blunt whole-word gate @0.85 tax: 12.5% (the comparison policy)
  corpus: Elfix/data/cmu_preprocessed.txt sha256
    b9d1ea1efd632602670ac44fe591471bd6fd81d3f1dc55ff4ebab6d8af757dc1
  pair protocol: Transform.fit(mine_pairs(corpus)) seed 7 (the shuffled
  order is part of the protocol, third sighting).
"""
from dataclasses import dataclass

from .surface import AllomorphTable, classify_remainder

THETA_PHON = 0.77
TABLE_SUFFIXES = ("s", "ed")     # the induced table's coverage


def evidence_walk(ranked, check):
    """Law 3 in one function: settle among shape-accepted candidates by
    evidence, never by order.

    ranked: [(key, shape_score, evidence_cos)] sorted descending on
    (shape_score, evidence_cos); check(key) -> GateResult.

    Walks candidates in evidence order; the first to pass the gate wins
    — unless the next candidate carries IDENTICAL evidence (same shape
    score, same phon consonance, bit-equal) and also passes, which no
    mechanism can resolve: refuse. Returns ((key, score, cos), None) on
    a settlement, (None, reason) on refusal; the reason is the highest-
    ranked veto's, so a killed imposter names its mechanism.
    """
    top_reason = None
    for i, (key, s, c) in enumerate(ranked):
        res = check(key)
        if not res.ok:
            if top_reason is None:
                top_reason = res.reason
            continue
        for key2, s2, c2 in ranked[i + 1:]:
            if (s2, c2) != (s, c):
                break
            if check(key2).ok:
                return None, "tie unresolved by evidence"
        return (key, s, c), None
    return None, (top_reason or "no analysis stands")


@dataclass(frozen=True)
class GateResult:
    ok: bool
    reason: str              # "" | "stem mismatch" | "remainder not ..."
    stem_cos: float


class PhonGate:
    """The two-mechanism gate. exact=True (the closed-world default)
    checks stems by sequence equality and arbitrates remainders with
    the pair-exact artifact, the induced table (-s/-ed frontier), and
    the suffix-wide attested sets (other-suffix frontier). exact=False
    is the dormant cosine path (module docstring)."""

    def __init__(self, embedder, pairs, prefix_pairs=(),
                 theta=THETA_PHON, table=None, exact=True):
        self.embedder = embedder
        self.theta = theta
        self.exact = exact
        self.attested = {}
        self.pair_rems = {}       # (base pron, sfx) -> mined remainders
        self.surface_words = {}   # (base word, sfx) -> mined derived words
        for base, sfx, w, rem in pairs:
            self.attested.setdefault(sfx, set()).add(tuple(rem))
            key = (tuple(self.embedder.corpus[base]), sfx) \
                if base in self.embedder.corpus else None
            if key:
                self.pair_rems.setdefault(key, set()).add(tuple(rem))
            self.surface_words.setdefault((base, sfx), []).append(w)
        self.prefix_attested = {}
        self.prefix_pair_rems = {}
        for base, pre, w, rem in prefix_pairs:
            self.prefix_attested.setdefault(pre, set()).add(tuple(rem))
            if base in self.embedder.corpus:
                self.prefix_pair_rems.setdefault(
                    (tuple(self.embedder.corpus[base]), pre),
                    set()).add(tuple(rem))
        self.table = (AllomorphTable().fit(embedder.corpus)
                      if table is None else table)

    @classmethod
    def from_transform(cls, transform, theta=THETA_PHON, table=None,
                       exact=True):
        return cls(transform.embedder, transform.pairs,
                   getattr(transform, "prefix_pairs", ()) or (),
                   theta=theta, table=table, exact=exact)

    # ── mechanism 2: arbitration (the artifact ladder) ───────────────
    def licensed(self, base_pron, suffix, rem):
        """Pair-exact mined remainders first; the induced table at the
        -s/-ed frontier; the suffix-wide set elsewhere."""
        key = (tuple(base_pron), suffix)
        if key in self.pair_rems:
            return tuple(rem) in self.pair_rems[key]
        if suffix in TABLE_SUFFIXES:
            cls_ = classify_remainder(rem, suffix)
            return (cls_ is not None
                    and cls_ == self.table.choose(list(base_pron), suffix))
        return tuple(rem) in self.attested.get(suffix, ())

    def licensed_prefix(self, base_pron, prefix, rem):
        key = (tuple(base_pron), prefix)
        if key in self.prefix_pair_rems:
            return tuple(rem) in self.prefix_pair_rems[key]
        return tuple(rem) in self.prefix_attested.get(prefix, ())

    # ── the dormant cosine instruments (see module docstring) ────────
    def stem_cos(self, obs_pron, base_pron):
        """Phon consonance of the observation's stem window against the
        base — measurement/ranking instrument; a GATE only in the
        dormant exact=False mode."""
        obs, base = list(obs_pron), list(base_pron)
        if len(obs) < len(base):
            return 0.0
        return float(self.embedder.phon_vec(obs[:len(base)])
                     @ self.embedder.phon_vec(base))

    def tail_cos(self, obs_pron, base_pron):
        obs, base = list(obs_pron), list(base_pron)
        if len(obs) < len(base):
            return 0.0
        return float(self.embedder.phon_vec(obs[len(obs) - len(base):])
                     @ self.embedder.phon_vec(base))

    def bare_cos(self, obs_pron, base_pron):
        return float(self.embedder.phon_vec(list(obs_pron))
                     @ self.embedder.phon_vec(list(base_pron)))

    # ── mechanism 1 + the gate proper ────────────────────────────────
    def _stem_ok(self, obs_pron, base_pron):
        if self.exact:
            return tuple(obs_pron[:len(base_pron)]) == tuple(base_pron)
        return self.stem_cos(obs_pron, base_pron) >= self.theta

    def check_bare(self, obs_pron, base_pron):
        c = self.bare_cos(obs_pron, base_pron)
        ok = (tuple(obs_pron) == tuple(base_pron) if self.exact
              else c >= self.theta)
        if not ok:
            return GateResult(False, "stem mismatch", c)
        return GateResult(True, "", c)

    def check_bound(self, obs_pron, base_pron, suffix):
        c = self.stem_cos(obs_pron, base_pron)
        if len(obs_pron) <= len(base_pron) \
                or not self._stem_ok(obs_pron, base_pron):
            return GateResult(False, "stem mismatch", c)
        rem = list(obs_pron[len(base_pron):])
        if not self.licensed(base_pron, suffix, rem):
            return GateResult(
                False, f"remainder not an attested -{suffix} form", c)
        return GateResult(True, "", c)

    def check_prefix(self, obs_pron, base_pron, prefix):
        c = self.tail_cos(obs_pron, base_pron)
        L = len(base_pron)
        if self.exact:
            tail_ok = (len(obs_pron) > L
                       and tuple(obs_pron[len(obs_pron) - L:])
                       == tuple(base_pron))
        else:
            tail_ok = len(obs_pron) > L and c >= self.theta
        if not tail_ok:
            return GateResult(False, "stem mismatch", c)
        rem = list(obs_pron[:len(obs_pron) - L])
        if not self.licensed_prefix(base_pron, prefix, rem):
            return GateResult(
                False, f"remainder not an attested {prefix}- form", c)
        return GateResult(True, "", c)

    # ── verdicts (word-aware layer) ──────────────────────────────────
    def verdict(self, word, mode, base, suffix=None):
        """OK when the standing analysis's surface identity is the word
        itself; HOMOPHONE when sound-identical but a different identity
        ('find' as fine+ed). Never called on refusals."""
        if mode == "BARE":
            return "OK" if word == base else "HOMOPHONE"
        return ("OK" if word in self.surface_words.get((base, suffix), ())
                else "HOMOPHONE")

    def surface_of(self, base, suffix, obs_pron=None):
        """A mined derived word for (base, suffix), if any. With
        obs_pron given, only a surface whose pronunciation EQUALS the
        observation may be named — a homophone claim must never point
        at a word it does not actually sound like (the gross/grows
        lesson: 'gross' licenses as a grow-pron stem + s via the
        gros+s pair; naming 'grows', whose remainder is z, would be a
        lie the honesty battery catches)."""
        words = self.surface_words.get((base, suffix), ())
        if obs_pron is None:
            return words[0] if words else None
        obs = list(obs_pron)
        for w in words:
            if list(self.embedder.corpus.get(w, ())) == obs:
                return w
        return None

    # ── the comparison policy (tests only): the blunt gate ───────────
    def blunt_cos(self, obs_pron, base_pron, modal_remainder):
        """Whole-word phon consonance against base + MODAL remainder —
        the gate design probe 39 measured the ~12.5% true-accept tax on.
        Kept for the no-tax inequality, never wired into analyze."""
        return float(self.embedder.phon_vec(list(obs_pron))
                     @ self.embedder.phon_vec(
                         list(base_pron) + list(modal_remainder)))
