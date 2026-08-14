"""E-2: the wug battery (probe 52) — generalization, measured on
stems that do not exist.

Novel stems are built attested-onset x attested-nucleus x attested-coda
from the lexicon's monosyllables and verified pron-absent: LEGALITY IS
ATTESTATION. The armchair is not a gold standard (law 2), twice:

  1. AFFRICATE FINALS TAKE EPENTHESIS. The naive textbook sibilant set
     {s, z, sh, zh} refuses the affricates; the induced phon table
     (99.1% held-out) says CH/JH-final stems take epen_z — and the
     table is right (church -> churches). The corrected gold below
     carries the affricates. (This build re-enacted the lesson live:
     the first gold transcription missed the corpus's uppercase
     digraph codes and graded the table wrong; the table won again.)
  2. KN-/VL-/TS- ONSETS ARE ATTESTED — Knupp, Knut, Vlad, Vlach,
     Tsang, Tsai carry them — so the attestation gate refuses the
     textbook's "illegal" label. (And the corpus goes further: Khmer,
     M'Bow, N'Dour, Sri, Zbig attest km-, mb-, nd-, sr-, zb-.) Only
     truly-unattested onsets refuse.

Inflection is by the SHIPPED induced phon table, selective: an unseen
final signature REFUSES, and the refusal is counted, never patched.
"""
import numpy as np

from .config import ensure_elfix_importable
from .surface import SURFACE_PHONES, final_signature

ensure_elfix_importable()
from elfix.substrate.features import features  # noqa: E402

# the corrected textbook rule (law 2's first canary): affricates are
# sibilant-family for epenthesis; phone codes are corpus-exact
# (single-letter consonants lowercase, digraphs uppercase)
SIBILANT_FINALS = frozenset({"s", "z", "SH", "ZH", "CH", "JH"})


def _is_vowel(p):
    return str(getattr(features(p), "kind", "?")) == "vowel"


def _voiced(p):
    return bool(getattr(features(p), "voiced", False)) or _is_vowel(p)


def monosyllable_parts(corpus):
    """Attested onsets/nuclei/codas from one-vowel pronunciations,
    with exemplar words per onset (the attestation receipts)."""
    onsets, nuclei, codas = {}, set(), set()
    prons = set()
    for w, pron in corpus.items():
        prons.add(tuple(pron))
        vi = [i for i, p in enumerate(pron) if _is_vowel(p)]
        if len(vi) == 1:
            i = vi[0]
            onsets.setdefault(tuple(pron[:i]), []).append(w)
            nuclei.add(pron[i])
            codas.add(tuple(pron[i + 1:]))
    return onsets, nuclei, codas, prons


def novel_stems(corpus, n=300, seed=50):
    """n novel stems (attested parts, pron-absent, nonempty coda)."""
    onsets, nuclei, codas, prons = monosyllable_parts(corpus)
    rng = np.random.default_rng(seed)
    on_l = sorted(onsets)
    nu_l = sorted(nuclei)
    co_l = sorted(codas)
    stems, seen = [], set()
    while len(stems) < n:
        o = on_l[rng.integers(len(on_l))]
        nu = nu_l[rng.integers(len(nu_l))]
        co = co_l[rng.integers(len(co_l))]
        if not co:
            continue
        stem = tuple(o) + (nu,) + tuple(co)
        if stem in prons or stem in seen:
            continue
        seen.add(stem)
        stems.append(stem)
    return stems


def textbook_gold(final, sfx):
    """The CORRECTED textbook allomorph (affricates included)."""
    if sfx == "s":
        if final in SIBILANT_FINALS:
            return "epen_z"
        return "z" if _voiced(final) else "s"
    if final in ("t", "d"):
        return "epen_d"
    return "d" if _voiced(final) else "t"


def wug_inflect(table, stem, sfx):
    """Selective: the induced table's rule for the stem's final
    signature, or None (REFUSE — unseen signature)."""
    return table.rules[sfx].get(final_signature(stem[-1]))


def wug_surface(stem, cls):
    return list(stem) + SURFACE_PHONES[cls]
