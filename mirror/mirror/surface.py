"""G-2: the induced allomorph table (probes 23, 26) — surface realization.

NO hand-written rule anywhere: the allomorph choice for -s and -ed is
LEARNED as an argmax count table keyed by the base's final-segment
signature (kind, manner, place, voiced), with the modal class as
fallback for unseen signatures. The learned table is exportable and
readable — it rediscovers voicing assimilation (voiced finals take
z/d, voiceless take s/t) and epenthesis (sibilant finals take IH-z,
alveolar-stop finals take IH-d) from counts alone.
"""
from collections import Counter, defaultdict

import numpy as np

from .config import ensure_elfix_importable

ensure_elfix_importable()
from elfix.substrate.features import features  # noqa: E402

SUFFIX_KINDS = ("s", "ed")

SURFACE_PHONES = {
    "epen_z": ["IH", "z"], "z": ["z"], "s": ["s"],
    "epen_d": ["IH", "d"], "d": ["d"], "t": ["t"],
}


def final_signature(ph):
    """The base-final segment's articulatory signature (probe 26)."""
    f = features(ph)
    kind = str(getattr(f, "kind", "?"))
    if kind == "vowel":
        return ("vowel", "-", "-", "V+")
    return (kind, str(getattr(f, "manner", "?")),
            str(getattr(f, "place", "?")),
            "V+" if getattr(f, "voiced", False) else "V-")


def classify_remainder(rem, kind):
    """Gold allomorph class of a mined phoneme remainder, or None."""
    toks = [t.lower() for t in rem]
    if kind == "s":
        if len(rem) >= 2 and toks[-1] == "z":
            return "epen_z"
        if toks == ["z"]:
            return "z"
        if toks == ["s"]:
            return "s"
    else:
        if len(rem) >= 2 and toks[-1] == "d":
            return "epen_d"
        if toks == ["d"]:
            return "d"
        if toks == ["t"]:
            return "t"
    return None


def mine_gold(corpus, sfx):
    """(final-signature, allomorph-class) pairs for one suffix."""
    gold = []
    for w in corpus:
        if w.endswith(sfx) and len(w) > len(sfx) + 2:
            base = w[:-len(sfx)]
            if base in corpus:
                b, d = corpus[base], corpus[w]
                if len(d) > len(b) and d[:len(b)] == b:
                    cls = classify_remainder(d[len(b):], sfx)
                    if cls:
                        gold.append((final_signature(b[-1]), cls))
    return gold


class AllomorphTable:
    """Count-induced signature -> allomorph decision table."""

    def __init__(self):
        self.rules = {}          # sfx -> {signature: class}
        self.fallback = {}       # sfx -> modal class
        self.support = {}        # sfx -> {signature: Counter}
        self.accuracy = {}       # sfx -> held-out accuracy
        self.n_test = {}

    def fit(self, corpus, seed=7, train_frac=0.6):
        for sfx in SUFFIX_KINDS:
            gold = mine_gold(corpus, sfx)
            rng = np.random.default_rng(seed)
            rng.shuffle(gold)
            cut = int(len(gold) * train_frac)
            train, test = gold[:cut], gold[cut:]
            table = defaultdict(Counter)
            for s, c in train:
                table[s][c] += 1
            self.support[sfx] = dict(table)
            self.rules[sfx] = {s: c.most_common(1)[0][0]
                               for s, c in table.items()}
            self.fallback[sfx] = Counter(c for _, c in train).most_common(1)[0][0]
            ok = sum(int(self.rules[sfx].get(s, self.fallback[sfx]) == c)
                     for s, c in test)
            self.accuracy[sfx] = ok / len(test) if test else 0.0
            self.n_test[sfx] = len(test)
        return self

    def choose(self, base_pron, sfx):
        sig = final_signature(base_pron[-1])
        return self.rules[sfx].get(sig, self.fallback[sfx])

    def surface(self, base_pron, sfx):
        """base phonemes + suffix category -> full surface phonemes."""
        return list(base_pron) + SURFACE_PHONES[self.choose(base_pron, sfx)]

    def export(self):
        """The learned phonology, human-readable, frequent-first."""
        lines = []
        for sfx in SUFFIX_KINDS:
            lines.append(f"-{sfx}  (held-out accuracy "
                         f"{self.accuracy[sfx] * 100:.1f}% on "
                         f"{self.n_test[sfx]})")
            freq = sorted(self.support[sfx].items(),
                          key=lambda kv: -sum(kv[1].values()))
            for sig, dist in freq:
                total = sum(dist.values())
                cls, cnt = dist.most_common(1)[0]
                lines.append(f"  {str(sig):46s} -> {cls:7s} ({cnt}/{total})")
            lines.append("")
        return "\n".join(lines)
