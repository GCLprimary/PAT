"""
scripts/sentence_quality.py  —  bounded, subject->predicate-arced generation
============================================================================
The sentence-arc gate found a real subject->predicate structure (nominative pronouns
early, accusative late) and a boundary signal, but position does NOT help next-class
PREDICTION — so these are STRUCTURE levers, measured by structure, not perplexity.
This scores them:

  sent-len   mean generated sentence length vs REAL text (boundaries should stop the
             run-on; too short or too long both wrong).
  subj-pos   mean sentence-position of NOMINATIVE pronouns (i, we, he, she) — should be
             EARLY (low); obj-pos of ACCUSATIVE pronouns (him, them, her) — should be LATE.
  + content / fn-rate (must not regress).

Run:  python scripts/sentence_quality.py        (~2-3 min: the clustering earns)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elfix.data_io import load_cmu
from elfix.running_text import load_utterances
from elfix.predict import Predictor
from elfix.semantic import SemanticSpace, SyntaxScaffold
from elfix.session import Session

SUBJ = {"i", "we", "he", "she", "they"}
OBJ = {"him", "them", "her", "us", "me"}
CONFIGS = {
    "grammar":      dict(grammar=1.0),
    "+boundaries":  dict(grammar=1.0, boundaries=True),
    "+arc":         dict(grammar=1.0, boundaries=True, position_bias=1.5),
}


def _posrole(sentences, group):
    """Mean normalized position of words from `group` across sentences."""
    vals = []
    for s in sentences:
        for i, w in enumerate(s):
            if w in group and len(s) > 1:
                vals.append(i / (len(s) - 1))
    return sum(vals) / len(vals) if vals else None


def main() -> int:
    cmu = load_cmu()
    vocab = set(cmu)
    utts = load_utterances()
    p = Predictor(utts[:50000], vocab)
    print("  earning classes + scaffold...")
    space = SemanticSpace(utts[:50000], vocab, unigram=p.unigram)
    scaffold = SyntaxScaffold(space, utts[:50000], vocab)
    skel = space.skeleton
    prompts = [u for u in utts[50000:50060] if 6 <= len(u) <= 18]

    real_len = sum(len(u) for u in utts[50000:50200]) / 200
    real_subj = _posrole([u for u in utts[50000:50400]], SUBJ)
    real_obj = _posrole([u for u in utts[50000:50400]], OBJ)
    print(f"  REAL TEXT: sent-len {real_len:.1f}   subj-pos {real_subj:.2f}   "
          f"obj-pos {real_obj:.2f}\n")

    def split(words):
        out, cur = [], []
        for w in words:
            if w == ".":
                if cur:
                    out.append(cur); cur = []
            else:
                cur.append(w)
        if cur:
            out.append(cur)
        return out

    agg = {name: {"len": [], "fn": [], "content": [], "sents": []} for name in CONFIGS}
    examples = {}
    for pi, u in enumerate(prompts):
        for name, kw in CONFIGS.items():
            s = Session(p, cmu, space=space, scaffold=scaffold, learn=False)
            s.read(" ".join(u))
            out = s.respond(n=28, temperature=0.7, rng_seed=pi, remember=False, **kw)
            words = [w for w, _, _ in out]
            sents = split(words)
            content = [w for w in words if w != "." and w not in skel]
            nw = max(1, len([w for w in words if w != "."]))
            agg[name]["len"].append(sum(len(s) for s in sents) / max(1, len(sents)))
            agg[name]["fn"].append(1 - len(content) / nw)
            agg[name]["content"].append(len(content) / nw)
            agg[name]["sents"].extend(sents)
            if pi == 1:
                examples[name] = " ".join(words)

    print(f"  example continuation of: '{' '.join(prompts[1])[:52]}...'")
    for name in CONFIGS:
        print(f"    {name:<12} {examples.get(name, '')}")
    print(f"\n  metrics (mean over {len(prompts)} prompts):")
    print(f"    {'config':<12}{'sent-len':>9}{'subj-pos':>9}{'obj-pos':>9}"
          f"{'content%':>9}{'fn-rate':>8}")
    print(f"    {'(real text)':<12}{real_len:>9.1f}{real_subj:>9.2f}{real_obj:>9.2f}"
          f"{'--':>9}{'--':>8}")
    for name in CONFIGS:
        a = agg[name]
        sp = _posrole(a["sents"], SUBJ)
        op = _posrole(a["sents"], OBJ)
        ml = sum(a["len"]) / len(a["len"])
        print(f"    {name:<12}{ml:>9.1f}{(sp if sp is not None else 0):>9.2f}"
              f"{(op if op is not None else 0):>9.2f}"
              f"{sum(a['content'])/len(a['content']):>8.0%}{sum(a['fn'])/len(a['fn']):>7.0%}")

    arc = agg["+arc"]
    ml = sum(arc["len"]) / len(arc["len"])
    sp, op = _posrole(arc["sents"], SUBJ), _posrole(arc["sents"], OBJ)
    bounded = abs(ml - real_len) < abs(28 - real_len)        # vs the unbounded 28-word run-on
    arced = (sp is not None and op is not None and sp < op)  # subjects before objects
    print(f"\n  ==> {'STRUCTURE HELPS' if bounded and arced else 'PARTIAL'}: boundaries "
          f"bound the run-on to ~{ml:.0f}-word\n      sentences (real {real_len:.0f}), and "
          f"the arc places subjects ({sp:.2f}) before objects ({op:.2f}),\n      like real "
          f"text ({real_subj:.2f} vs {real_obj:.2f}) -- the subject->predicate shape. "
          f"Output is\n      bounded and role-ordered (still not fully parseable; this is "
          f"the SHAPE of syntax,\n      counted, not a parser).")
    return 0 if bounded and arced else 1


if __name__ == "__main__":
    raise SystemExit(main())
