# UniMorph (eng) addenda — receipted draft

## Methodology
Every entry is a double-locked pair: the form's pronunciation extends the lemma's exactly, the spelling is the exact concatenation, and the form is attested (count >= 5) in a 5.2M-word corpus. Rows whose lemma the case census classifies PROPER (sentence-medial capitalization dominance over raw cased sources) are EXCLUDED by that measurement — not by any name list.

Total: 1831 addenda rows (171 excluded as census-proper; the flags ride the full table). Full table: reports/audit_unimorph.tsv.

## Top exemplars (by attestation)

| lemma | form | tags | attested | case evidence |
|---|---|---|---|---|
| expect | expected | V;PST/V;V.PTCP;PST | x1805 | common (16/1490 medial-cap, 3 initial) |
| month | months | N;PL/V;PRS;3;SG | x1565 | common (17/2472 medial-cap, 1 initial) |
| seem | seemed | V;PST/V;V.PTCP;PST | x1489 | common (4/2034 medial-cap, 1 initial) |
| word | words | N;PL/V;PRS;3;SG | x1436 | common (47/6676 medial-cap, 8 initial) |
| morn | morning | V;V.PTCP;PRS | x1379 | common (6/73 medial-cap, 0 initial) |
| accord | according | V;V.PTCP;PRS | x1377 | common (77/663 medial-cap, 2 initial) |
| export | exports | N;PL/V;PRS;3;SG | x1257 | common (172/1044 medial-cap, 34 initial) |
| earning | earnings | N;PL/V;PRS;3;SG | x1118 | common (2/77 medial-cap, 0 initial) |
| operation | operations | N;PL/V;PRS;3;SG | x1050 | common (9/465 medial-cap, 2 initial) |
| product | products | N;PL/V;PRS;3;SG | x1024 | common (40/468 medial-cap, 2 initial) |
| import | imports | N;PL/V;PRS;3;SG | x984 | common (47/472 medial-cap, 6 initial) |
| talk | talks | N;PL/V;PRS;3;SG | x783 | common (20/3169 medial-cap, 56 initial) |
| own | owned | V;PST/V;V.PTCP;PST | x689 | common (21/15531 medial-cap, 4 initial) |
| seem | seems | N;PL/V;PRS;3;SG | x685 | common (4/2034 medial-cap, 1 initial) |
| toward | towards | N;PL/V;PRS;3;SG | x685 | common (16/1290 medial-cap, 28 initial) |

## Reproduction
```
python -m pytest tests/test_audit.py tests/test_case.py -q   # agent repo
```
