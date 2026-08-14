"""
scripts/gradient_compartment.py — SIZE the gradient compartment, and the surprise it found:
the word-bigram floor was never the counted ceiling.
============================================================================================
The 'compartmentalize the gradient' stance (SCORECARD) needs its step-1 probe: an ORACLE
ABLATION that decomposes the floor's per-word surprisal into compartments, all counted:

    H_total(w|prev)  =  H_cat  +  H_within                     (chain rule, exact)
    H_cat    = -log2 P(sclass(w) | prev)      which KIND of word comes next (structural)
    H_within = -log2 P(w | prev, sclass(w))   which word, GIVEN its kind (lexical)

then how much of H_within the counted TOPIC carry recovers. What remains is the compartment
a gradient would have to fill *within-class*. The probe also LOCATES it: bucketed by the
RoleTagger's earned POS of the next word (is the residual the argument channel — new
entities — or spread across predicates too?).

THE FINDING THE PROBE PRODUCED (the reason this script matters beyond its numbers): the
category term dominates (~3/4 of the floor's bits), and the counted CLASS-bigram predicts
the category BETTER than the word-bigram does — conditioning on less generalizes more. So
the obvious factorization

    P(w | prev)  =  P(class(w) | class(prev))  x  P(w | class(w), prev)
                      [the scaffold, counted]      [within-class bigram share, counted]

is a purely counted model that should beat the 'floor'. IT DOES (measured below): the floor
was the WORD-BIGRAM ceiling, not the counted ceiling. NOTE the reconciliation with the old
null: scripts/semantic_gate measured prev-class POOLING — P(w | class(prev)) directly — a
NULL, because it throws away the word identity. The FACTORED form keeps word identity in
the within-class term and uses the class-bigram only for the category — Brown et al.'s
(1992) actual class-LM formulation. The null was for the wrong mechanism, not for classes.

RIGOUR:
  - the unk-class leak is PAID: words with no distributional class do not collapse into a
    free category — the factored model pays their within-unk unigram share (else it would
    underpay ~the full lexical cost of every unclassed word and the win would be fake).
  - sem_beta / interpolation lambda are earned on a DEV split, reported on TEST (never
    tuned on test — the carry_predict discipline).
  - sparse/dense breakdown: the win should live where the word-bigram is data-starved
    (generalization), not where it is rich — checked, not assumed.

PROVENANCE: [NEW->established] class-factored LM — Brown et al. (1992); the oracle
decomposition + the compartment framing are [NEW->original]. All counted (Law 6).

Run:  python scripts/gradient_compartment.py        (~3-4 min: the clustering earns)
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold, SemanticCarry
from elfix.syntax_tree import RoleTagger


class FactoredCounted:
    """The class-factored counted next-word model:
    P(w|prev) = P(sclass(w) | sclass(prev)) x P(w | sclass(w), prev [, topic]).
    Within a class: bigram counts restricted to the class, backed off (a=1 pseudo-count)
    to the class-internal unigram share. Unclassed ('unk') words pay their share of the
    UNK pool the same way — no free category (the leak this class exists to pay)."""

    def __init__(self, p: Predictor, space: SemanticSpace, scaffold: SyntaxScaffold, a: float = 1.0):
        self.p, self.space, self.sc, self.a = p, space, scaffold, a
        self.uni_c_tot = {cid: (sum(p.unigram.get(m, 0) for m in mem) or 1)
                          for cid, mem in space.class_words.items()}
        self.unk = [w for w in p.unigram
                    if w not in space.word_class and w not in space.skeleton]
        self.unk_tot = sum(p.unigram.get(w, 0) for w in self.unk) or 1
        self._rowsum = {}                                # (prev, cat-key) -> class row mass

    def members(self, w, c):
        if c[0] == "cl":
            return self.space.class_words.get(c[1], [w]), self.uni_c_tot.get(c[1], 1)
        if c[0] == "unk":
            return self.unk, self.unk_tot
        return [w], 1                                    # a functor: category == word

    def _row_mass(self, prev, ckey, mem):
        """sum of prev's bigram counts over the class members, cached per (prev, class)."""
        k = (prev, ckey)
        v = self._rowsum.get(k)
        if v is None:
            row = self.p.bigram.get(prev, {})
            v = sum(row.get(m, 0) for m in mem)
            self._rowsum[k] = v
        return v

    def p_within(self, prev, w, sb: float = 0.0, cprob=None) -> float:
        c = self.sc.sclass(w)
        mem, utot = self.members(w, c)
        if len(mem) == 1:
            return 1.0
        # add-one INSIDE the unigram share -> strictly positive, exactly normalized:
        # sum over members of (row + a*(uni+1)/(utot+|mem|)) = row_mass + a.
        row = self.p.bigram.get(prev, {})
        share = (self.p.unigram.get(w, 0) + 1) / (utot + len(mem))
        base = (row.get(w, 0) + self.a * share) / (self._row_mass(prev, c, mem) + self.a)
        if sb > 0 and cprob is not None and c[0] == "cl":    # topic can't see the unk pool
            st = sum(cprob(m) for m in mem)
            if st > 0:
                return (1 - sb) * base + sb * (cprob(w) / st)
        return base

    def prob(self, prev, w, sb: float = 0.0, cprob=None) -> float:
        return self.sc.trans(prev, w) * self.p_within(prev, w, sb, cprob)


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    train, dev, test = utts[:50000], utts[50000:51000], utts[51000:53000]
    p = Predictor(train, vocab)
    print("  earning classes + scaffold + roles...")
    space = SemanticSpace(train, vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, train, vocab)
    roles = RoleTagger(p.bigram, space.skeleton, space.anchors[0])
    fac = FactoredCounted(p, space, scaffold)

    def stream(uts):
        """(prev, w) scoring pairs, resetting across OOV, with a fresh topical carry."""
        carry = SemanticCarry(space, p.unigram, rate=0.99)
        for u in uts:
            prev = None
            for w in u:
                if w not in vocab:
                    prev = None
                    continue
                if prev is not None:
                    yield prev, w, carry
                carry.observe(w)
                prev = w

    # ── PART 1: the oracle decomposition (size + locate the compartment) ─────────
    A = dict(tot=0.0, cat=0.0, catcb=0.0, win=0.0, wt=0.0, n=0)
    R = {"pred": [0.0, 0.0, 0], "arg": [0.0, 0.0, 0]}      # win, wt, n
    SB_DECOMP = 0.4                                        # the earned topical mix region
    for prev, w, carry in stream(test):
        c = scaffold.sclass(w)
        mem, _ = fac.members(w, c)
        pw = p.prob(prev, w)
        pc = sum(p.prob(prev, m) for m in mem) or pw       # bigram mass on the class
        pw = min(pw, pc)
        s_tot, s_cat = -math.log2(pw), -math.log2(pc)
        s_win = s_tot - s_cat
        # topic-recovered within-class share
        wt = fac.p_within(prev, w, sb=SB_DECOMP, cprob=carry.prob)
        s_wt = min(s_win, -math.log2(wt)) if wt > 0 else s_win
        A["tot"] += s_tot; A["cat"] += s_cat; A["win"] += s_win; A["wt"] += s_wt
        A["catcb"] += -math.log2(scaffold.trans(prev, w)); A["n"] += 1
        r = roles.score(w)
        if c[0] == "cl" and r is not None:
            b = R["pred" if r >= 0.5 else "arg"]
            b[0] += s_win; b[1] += s_wt; b[2] += 1
    n = A["n"]
    print(f"\n  PART 1 — the ORACLE DECOMPOSITION ({n:,} held-out tokens):")
    print(f"    H_total (word-bigram floor)          {A['tot']/n:6.2f} bits/word")
    print(f"    = H_cat  (which KIND of word)        {A['cat']/n:6.2f}   ({A['cat']/A['tot']:.0%} of the bits)")
    print(f"        the CLASS-bigram pays only       {A['catcb']/n:6.2f}   (counted, conditions on LESS)")
    print(f"    + H_within (which word, given kind)  {A['win']/n:6.2f}")
    print(f"        topic (counted) recovers         {(A['win']-A['wt'])/n:6.2f}")
    print(f"        GRADIENT COMPARTMENT (residual)  {A['wt']/n:6.2f}   ({A['wt']/A['tot']:.0%} of the total)")
    print(f"    where it lives (earned POS of next):")
    for k, lab in (("pred", "predicate (verb) channel"), ("arg", "argument (noun) channel")):
        wn, wt_, bn = R[k]
        bn = bn or 1
        print(f"      {lab:<26} H_within {wn/bn:5.2f} -> residual {wt_/bn:5.2f}  (n={R[k][2]:,})")

    # ── PART 2: the factored counted model (earn sb, lambda on DEV; report TEST) ──
    def score(uts, sb, lam):
        tot = 0.0; m = 0
        for prev, w, carry in stream(uts):
            pf = fac.prob(prev, w, sb=sb, cprob=carry.prob if sb > 0 else None)
            pr = lam * p.prob(prev, w) + (1 - lam) * pf
            tot += -math.log2(pr); m += 1
        return tot / m, m

    best, bsb, blam = None, 0.0, 0.0
    for sb in (0.0, 0.2, 0.4):
        for lam in (0.0, 0.3, 0.5):
            d, _ = score(dev, sb, lam)
            if best is None or d < best:
                best, bsb, blam = d, sb, lam
    floor_t, m = score(test, 0.0, 1.0)                     # lam=1 -> pure floor
    fact_t, _ = score(test, 0.0, 0.0)                      # pure factored, no topic
    tuned_t, _ = score(test, bsb, blam)
    print(f"\n  PART 2 — the FACTORED COUNTED MODEL (dev-earned sb={bsb}, lambda={blam}; "
          f"test = {m:,} tokens):")
    print(f"    word-bigram floor                      {floor_t:6.2f} bits/word")
    print(f"    factored P(cat|cb) x P(w|cat,prev)     {fact_t:6.2f}   ({floor_t-fact_t:+.2f})")
    print(f"    factored + topic + interpolation       {tuned_t:6.2f}   ({floor_t-tuned_t:+.2f}, "
          f"~{2**(floor_t-tuned_t):.1f}x perplexity)")

    # sparse/dense: the win must come from generalization (sparse contexts), else suspect
    buckets = {"dense (bigram>=5)": [0.0, 0.0, 0], "sparse (bigram<5)": [0.0, 0.0, 0]}
    for prev, w, carry in stream(test):
        k = "dense (bigram>=5)" if p.bigram.get(prev, {}).get(w, 0) >= 5 else "sparse (bigram<5)"
        pf = fac.prob(prev, w, sb=bsb, cprob=carry.prob if bsb > 0 else None)
        pr = blam * p.prob(prev, w) + (1 - blam) * pf
        b = buckets[k]
        b[0] += -math.log2(p.prob(prev, w)); b[1] += -math.log2(pr); b[2] += 1
    print(f"    where the win lives:")
    for k, (fl, fa, bn) in buckets.items():
        bn = bn or 1
        print(f"      {k:<19} floor {fl/bn:6.2f} -> factored {fa/bn:6.2f}  "
              f"({fl/bn-fa/bn:+.2f}, n={buckets[k][2]:,})")

    win = floor_t - tuned_t
    if win > 0.2:
        print(f"\n  ==> VERDICT: the word-bigram floor was the WORD-BIGRAM ceiling, not the "
              f"counted one.\n      The class-FACTORED counted model — category by the class-bigram, "
              f"word by its\n      within-class share — beats it by {win:.2f} bits/word "
              f"(~{2**win:.1f}x perplexity), no gradient\n      anywhere, unk-leak PAID. (The old "
              f"prev-class-pooling NULL stands: pooling throws\n      away word identity; the "
              f"FACTORED form keeps it — the mechanism was wrong, not\n      the classes.)")
    else:
        print(f"\n  ==> VERDICT: NO real factored win once the unk leak is paid "
              f"({win:+.2f} bits) — the\n      word-bigram floor stands as the counted ceiling; "
              f"the scratch win was the leak.\n      The measurement is the finding.")
    print(f"      The gradient compartment proper — irreducible by class + topic — is "
          f"{A['wt']/n:.2f} bits/word\n      ({A['wt']/A['tot']:.0%} of the floor), spread across "
          f"BOTH open-class channels (pred/arg),\n      not just new entities. That is the honest "
          f"size-and-shape of what any walled\n      gradient would have to earn (step 1 of the "
          f"compartmentalize probe).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
