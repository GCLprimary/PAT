# Data

`cmu_sample.txt` and `stress_sample.txt` are 25k-line samples of ElfIX's
`data/cmu_preprocessed.txt` (135k entries) and `data/stress.txt` — the CMU
Pronouncing Dictionary, preprocessed. `cmu_sample.txt` is a **seeded uniform
random draw** (seed 42), regenerable with `python make_samples.py`; an earlier
alphabetical head-cut sample skewed the BPE baseline and is gone.
`stress_sample.txt` is still the old head-cut — regenerate it by dropping the
full `stress.txt` here and re-running `make_samples.py`.

- `cmu_sample.txt`  — `word \t PHONEME PHONEME ...`  (ASCII ARPABET, no stress digits)
- `stress_sample.txt` — `word \t stress_pattern`  (digit count = syllable count)

**To run on the full corpus:** copy `cmu_preprocessed.txt` and/or `stress.txt`
from your ElfIX archive into this folder. That's it — `elfix/data_io.py`
auto-detects each full file when present and falls back to the sample otherwise,
per file independently (so a full `cmu_preprocessed.txt` with no `stress.txt`
uses the full corpus + the stress sample). `cmu_preprocessed.txt` is already in
place here, so the gate runs at full scale by default. (CRLF is fine; the
loaders split on whitespace.)

`corpus.txt` is the **running-text corpus** — the Brown corpus in the ElfIX
contract: one sentence per line, lowercased, `[a-z' space]` only, internal
apostrophes kept (`don't`, `atlanta's`), hyphens split. 54,756 sentences, ~1.0M
words, 98.4% CMU coverage. Built by `make_corpus.py` (needs `nltk`); consumed by
`elfix/running_text.py`. Phonemes come from `cmu_preprocessed.txt`, NOT nltk's
cmudict — one source of truth (Law 3).

Provenance: CMU Pronouncing Dictionary (public domain), preprocessed in ElfIX;
Brown Corpus (via NLTK) for the running text.

`corpus.txt` (Brown-derived running text) is **not distributed** — its
source license is research-use. Rebuild it locally with `python make_corpus.py`
(fetches the Brown corpus via NLTK). The headline gates (`syllable_eval.py`,
`milestone1.py`) run on the CMU data and do not require it.

`text_sample.txt` is a short public-domain excerpt (opening of Jane Austen's
*Pride and Prejudice*, 1813) used only as a running-text demo fixture. Public
domain: no distribution restriction.
