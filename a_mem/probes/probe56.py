"""Probe 56: PAT'S FIRST JOB INTERVIEWS.
A  THE LEXICON AUDITOR
   A1 CMU variant candidates: words whose ORTHOGRAPHY decomposes as
      stemword + known suffix spelling but whose PRON refuses the
      concat -- each mismatch classed (elision / mutation / other)
      with the full receipt. government's dropped /n/ is the
      demonstrated hit; this measures the class.
   A2 UniMorph addenda: double-lock-certified pairs whose (lemma,
      form, tag) row the vendored UniMorph file lacks.
   A3 homophone cross-ref census (the index CMU implies but never
      states).
B  THE VERIFICATION ORACLE
   Ten staged proposals (as if from a fluent model); Pat's ladder
   answers CERTIFY / REFUSE / HOMOPHONE, each with its receipt.
"""
import warnings
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")
exec(open("/home/claude/probe/probe19.py").read().split("from amem.api")[0])

PRON2WORDS = defaultdict(list)
for w, p in corpus.items(): PRON2WORDS[tuple(p)].append(w)
cnt = Counter()
for l in open("/home/claude/elfix/Elfix/data/corpus_big.txt"): cnt.update(l.split())

SUFFIX_PHON = {"ment": ("m", "AH", "n", "t"), "ness": ("n", "AH", "s"),
               "less": ("l", "AH", "s"), "ly": ("l", "IY",),
               "ful": ("f", "AH", "l"), "ing": ("IH", "NG"),
               "er": ("ER",), "est": ("AH", "s", "t")}
def edit1(a, b):
    if abs(len(a) - len(b)) > 1: return None
    if len(a) == len(b):
        d = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        return ("mutation", a[d[0]], b[d[0]]) if len(d) == 1 else None
    if len(a) < len(b): a, b, tag = b, a, "elision"
    else: tag = "insertion"
    for i in range(len(a)):
        if a[:i] + a[i + 1:] == b: return (tag, a[i], "-")
    return None

print("A1 · CMU VARIANT CANDIDATES (ortho decomposes, pron refuses)")
classes = Counter(); samples = []
for w, p in corpus.items():
    if cnt[w] < 3: continue
    for sfx, tail in SUFFIX_PHON.items():
        if not w.endswith(sfx) or len(w) - len(sfx) < 4: continue
        sw = w[:-len(sfx)]
        cand = [sw] + ([sw + "e"] if sw + "e" in corpus else [])
        for s2 in cand:
            if s2 not in corpus or cnt[s2] < 3: continue
            expect = tuple(corpus[s2]) + tail
            actual = tuple(corpus[w])
            if actual == expect: classes["exact"] += 1; break
            e = edit1(list(actual), list(expect))
            if e:
                classes[e[0]] += 1
                if e[0] in ("elision", "mutation") and len(samples) < 10:
                    samples.append((w, s2, sfx, e))
                break
        else:
            continue
        break
tot_mis = classes["elision"] + classes["mutation"] + classes["insertion"]
print(f"  decomposable-and-exact {classes['exact']}   "
      f"MISMATCH candidates {tot_mis} "
      f"(elision {classes['elision']}, mutation {classes['mutation']}, "
      f"insertion {classes['insertion']})")
for w, s2, sfx, (k, a, b) in samples:
    print(f"    {w} = {s2}+{sfx}: pron drops/alters [{a}]  ({k})  "
          f"pron(w)={' '.join(corpus[w])}")

print("\nA2 · UNIMORPH ADDENDA (double-locked pairs the file lacks)")
uni = defaultdict(set)
for line in open("/home/claude/unimorph_eng/eng"):
    q = line.rstrip("\n").split("\t")
    if len(q) == 3: uni[q[0]].add((q[1], q[2]))
TAGMAP = {"ed": ("V;PST", "V;V.PTCP;PST"), "ing": ("V;V.PTCP;PRS",),
          "s": ("N;PL", "V;PRS;3;SG")}
missing = []
for base, sfx, w, rem in pairs:
    if sfx not in TAGMAP or cnt[w] < 5: continue
    if tuple(corpus[base]) + tuple(rem) != tuple(corpus[w]): continue
    rows = uni.get(base, set())
    if not any((w, t) in rows for t in TAGMAP[sfx]):
        missing.append((base, w, sfx))
print(f"  certified pairs absent from UniMorph: {len(missing)}")
for base, w, sfx in missing[:8]:
    print(f"    + {base} -> {w}  [{'/'.join(TAGMAP[sfx])}]  "
          f"(attested x{cnt[w]}, pron-exact, ortho-exact)")

groups = [ws for ws in PRON2WORDS.values() if len({x for x in ws}) >= 2]
print(f"\nA3 · homophone cross-ref index: {len(groups)} pron-groups "
      f"CMU implies but never states (e.g., "
      + "; ".join("/".join(sorted(set(g))[:3]) for g in groups[:3]) + ")")

print("\nB · THE VERIFICATION ORACLE (proposals in, receipts out)")
pair_set = {(b, s): w for b, s, w, r in pairs}
attested = defaultdict(set)
for b, s, w, r in pairs: attested[s].add(tuple(r))
def oracle(word, base, sfx):
    wp, ok = tuple(corpus.get(word, ())), False
    if base not in corpus: return f"REFUSE — '{base}' is not a word I know"
    bp = tuple(corpus[base])
    if not wp: return f"REFUSE — '{word}' is not a form I can read"
    if wp[:len(bp)] != bp:
        return (f"REFUSE — pron('{word}') does not begin with pron('{base}') "
                f"[{' '.join(wp)} vs {' '.join(bp)}]")
    rem = wp[len(bp):]
    if rem not in attested.get(sfx, set()):
        return (f"REFUSE — remainder [{' '.join(rem)}] is not an attested "
                f"form of -{sfx}")
    surf = pair_set.get((base, sfx))
    if surf == word: return f"CERTIFY — {base}+{sfx}, pair-exact, mined"
    if surf and tuple(corpus[surf]) == wp:
        return (f"HOMOPHONE — sounds exactly like {surf} ({base}+{sfx}); "
                f"I cannot tell them apart by ear")
    return f"CERTIFY — {base}+{sfx}, ladder-licensed"
tests = [("painted", "paint", "ed"), ("walking", "walk", "ing"),
         ("melted", "metal", "ed"), ("side", "sigh", "ed"),
         ("famous", "fam", "ous"), ("cheerfully", "cheerful", "er"),
         ("darkness", "dark", "ness"), ("quickly", "quick", "ly"),
         ("government", "govern", "ment"), ("finds", "find", "s")]
for w, b, s in tests:
    print(f"  propose {w} = {b}+{s}?  ->  {oracle(w, b, s)}")
