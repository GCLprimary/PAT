"""G-4 acceptance (probes 24, 27): the selective generator v2.

CONVERGENCE UPDATE (probe-machine corpora imported as pinned artifacts):
the GAP gate is back to SPEC-LITERAL — with the probe corpora the gap
measures 55 (>= 50 restored; it was 46 on the locally-rebuilt corpus,
banded by owner ruling at the time). The salad gate keeps its structural
form: the rng lottery still deals ~1 attested-English draw per hundred
('dark really fixed'), so salad >= 99/100 PLUS the hard law — a garbage
continuation is impossible: any non-refused salad prompt must be
attested by the proposer's own counts AND clear the coherence gate.

Probe 24's v1 failure (selectivity gap -5) stays in the repo as
evidence: a_mem/probes/probe24.py.
"""
import numpy as np
import pytest

from mirror import Proposer, split_sents
from mirror.generate import canonical_setup, load_default_prompt_corpus


@pytest.fixture(scope="module")
def gen_setup(geometry):
    return canonical_setup(geometry)


def run_selectivity(gen, prompts_id, prompts_ood):
    r_id = r_ood = 0
    coh, leaks = [], []
    for p in prompts_id:
        out, _ = gen.generate(p)
        r_id += int(out is None)
        if out:
            coh.append(gen.coherence(out, gen.topic_vec(p)))
    for p in prompts_ood:
        out, _ = gen.generate(p)
        r_ood += int(out is None)
        if out:
            leaks.append((p, out))
    return r_id, r_ood, coh, leaks


def test_selectivity_and_coherence(gen_setup):
    gen, prompts_id, prompts_ood = gen_setup
    r_id, r_ood, coh, leaks = run_selectivity(gen, prompts_id, prompts_ood)
    gap = r_ood - r_id
    print(f"\nin-domain refused {r_id}%  salad refused {r_ood}%  gap {gap}  "
          f"coherence {np.mean(coh):+.3f}")
    for p, out in leaks:
        print(f"  lottery-attested salad: '{' '.join(p)}' -> '{' '.join(out)}'")

    # gap: spec-literal, restored on the probe-machine corpora
    assert r_ood >= 99, f"salad refusal {r_ood}/100 < 99"
    assert gap >= 50, f"selectivity gap {gap} < 50 (spec-literal)"
    assert float(np.mean(coh)) >= 0.30, \
        f"emitted coherence {np.mean(coh):+.3f} < +0.30"

    # the STRUCTURAL hard law: garbage continuation is impossible — any
    # non-refused salad must be attested by the proposer's own counts
    # and its continuation must clear the coherence gate
    for p, out in leaks:
        assert gen.prompt_attested(p), \
            f"LAW BROKEN: unattested salad '{' '.join(p)}' was continued"
        assert gen.coherence(out, gen.topic_vec(p)) >= gen.theta_m, \
            f"LAW BROKEN: incoherent continuation of '{' '.join(p)}'"


def test_probe24_salad_showpieces_refuse(gen_setup):
    """The three salad showpieces from probe 24's recipe (Brown vocab,
    the exact rng stream) — v1 notoriously continued salads; v2 must
    refuse these."""
    gen, _, _ = gen_setup
    brown = load_default_prompt_corpus()
    brown_train, _, rng = split_sents(brown)
    prop_b = Proposer(brown_train)
    v_brown = prop_b.salad_vocab()
    showpieces = [tuple(rng.choice(v_brown, 3, replace=False))
                  for _ in range(100)][:3]
    print()
    for p in showpieces:
        out, status = gen.generate(p)
        print(f"  SALAD '{' '.join(p)}' -> {status}")
        assert out is None, \
            f"probe-24 showpiece '{' '.join(p)}' was continued: {out}"


def test_dual_corpus_wiring(gen_setup):
    """The dual-corpus law: the proposer volume-scales (registry stack),
    the meaning geometry coherence-scales (Brown dense, 300-dim)."""
    gen, _, _ = gen_setup
    assert gen.g.dim == 300                       # Brown dense stays
    brown_vocab = len(Proposer(load_default_prompt_corpus()).uni)
    assert len(gen.p.uni) > brown_vocab * 1.5, \
        "proposer counts do not come from the larger stack"


def test_v3_flag_exists_but_v2_is_default(gen_setup, geometry):
    """G-5: the composite audit ships behind the flag; the sweep failed
    promotion (equal gap, strictly lower coherence at every lambda), so
    v2 stays default."""
    from mirror import Generator
    gen, _, _ = gen_setup
    assert gen.audit == "v2"
    g3 = Generator(gen.p, geometry, audit="v3", lam=0.1)
    cont = ["the", "government", "policy"]
    assert g3.path_action(cont) >= 0.0            # the machinery exists