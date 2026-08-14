# CMUdict variant candidates — receipted errata draft

## Methodology
Every entry below decomposes orthographically as stem + suffix spelling with both halves attested (count >= 3), yet its pronunciation refuses the concatenation by exactly one phone (edit-distance-1). Each row carries the full receipt: expected phones, actual phones, the altered phone, and the mismatch class. Nothing is asserted without its phones.

Total: 459 candidates (elision 168, mutation 273, insertion 18) against 2993 exact decompositions. Full table: reports/audit_cmu.tsv.

## Top exemplars (by corpus attestation)

| word | decomposition | expected | actual | class |
|---|---|---|---|---|
| government | govern+ment | g AH v ER n m AH n t | g AH v ER m AH n t | elision |
| interest | inter+est | IH n t ER AH s t | IH n t r AH s t | mutation |
| number | numb+er | n AH m ER | n AH m b ER | insertion |
| longer | long+er | l AO NG ER | l AO NG g ER | insertion |
| evening | even+ing | IY v IH n IH NG | IY v n IH NG | elision |
| finally | final+ly | f AY n AH l l IY | f AY n AH l IY | elision (degemination) |
| leading | lead+ing | l EH d IH NG | l IY d IH NG | mutation |
| generally | general+ly | JH EH n ER AH l l IY | JH EH n ER AH l IY | elision (degemination) |
| falling | fall+ing | f AO l IH NG | f AA l IH NG | mutation |
| wilderness | wilder+ness | w AY l d ER n AH s | w IH l d ER n AH s | mutation |
| officer | office+er | AO f IH s ER | AO f AH s ER | mutation |
| usually | usual+ly | j UW ZH AH w AH l l IY | j UW ZH AH w AH l IY | elision (degemination) |
| closing | close+ing | k l OW s IH NG | k l OW z IH NG | mutation (voicing-sz) |
| housing | house+ing | h AW s IH NG | h AW z IH NG | mutation (voicing-sz) |
| reading | read+ing | r EH d IH NG | r IY d IH NG | mutation |

## Reproduction
```
python -m pytest tests/test_audit.py tests/test_case.py -q   # agent repo
```
