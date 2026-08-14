"""mirror: the reasoning-core integration layer.

Five organs, each probe-validated separately, composed here:
  represent — voicing-neutral shape-bigram embeddings (ElfIX features)
  transform — seam-aware binding: bind(base, suffix) -> predicted form
  memory    — a_mem episodes via EpisodeHooks (unchanged)
  loop      — mirror analysis: propose / reflect / settle-or-refuse
  meaning   — PPMI count geometry + the form|meaning rung
"""
from .config import cmu_path, elfix_path, ensure_elfix_importable
from .decode import (Decoded, ShapeDecoder, enumerate_walks,
                     graph_from_counts, infer_starts, snap_counts)
from .embed import BigramSpace, Embedder, load_cmu, shape
from .generate import (Generator, Proposer, load_default_prompt_corpus,
                       load_sents, split_sents)
from .loop import Analysis, MirrorLoop, THETA_DEFAULT
from .surface import AllomorphTable, classify_remainder, final_signature
from .meaning import (MeaningGeometry, PROBE22_TRIPLES, SOURCES,
                      build_corpus, coherence_report, combine_sources,
                      ensure_corpus, ensure_source, relatedness,
                      suffix_offsets)
from .agreement import (COORDINATORS, REFUSAL_TAXONOMY, TIER_OF_BUCKET,
                        between_nouns_v2, build_number_lexicon, frame_v2,
                        mine_strict_cases, mine_v2_cases,
                        predict_recent_noun, predict_register,
                        predict_trigram)
from .audit import (audit_rule, build_form_lexicon, BE_AUX, MODAL_AUX,
                    PERF_AUX)
from .blimp import (AGREEMENT_PARADIGMS, TrigramScorer, aggregate,
                    demonstrative_judge, existential_quant_judge,
                    gender_judge, load_paradigm, npi_judge, ppart_judge,
                    reflexive_judge, run_all, sv_judge)
from .compass import (P7, P8, WINDOW, decode as compass_decode,
                      dial_bit, fold as compass_fold,
                      locality_violations)
from .geometry import cone_identity, counts_of, junction_bigram, mass
from .inflect import (InflectionTable, apply_class, classify,
                      signature as inflect_signature)
from .diagnostics import ImposterReport, imposter_ceiling
from .gate import GateResult, PhonGate, THETA_PHON, evidence_walk
from .lessons import AUDIT_FLOOR, LawBook, Page
from .journey import Itinerary, Journey, JourneyResult, Leg
from .regions import CenteredSpace
from .registers import Register, RegisterBank, UnstampedBank
from .rulers import (PhaseRuler, Stamp, sqrt2_concentration,
                     sqrt2_histogram, sqrt2_phase)
from .rung import Rung
from .stage import (DiscourseStage, Observation, RawTopicSpace,
                    SingleThetaStage)
from .transform import (PREFIXES, SUFFIXES, Transform, mine_pairs,
                        mine_prefix_pairs)

__version__ = "0.1.0"

__all__ = [
    "Embedder", "BigramSpace", "shape", "load_cmu",
    "Transform", "mine_pairs", "mine_prefix_pairs", "SUFFIXES", "PREFIXES",
    "ShapeDecoder", "Decoded", "snap_counts", "graph_from_counts",
    "infer_starts", "enumerate_walks",
    "AllomorphTable", "classify_remainder", "final_signature",
    "Generator", "Proposer", "load_sents", "load_default_prompt_corpus",
    "split_sents",
    "CenteredSpace", "DiscourseStage", "SingleThetaStage", "Observation",
    "Stamp", "PhaseRuler", "sqrt2_phase", "sqrt2_histogram",
    "sqrt2_concentration",
    "Register", "RegisterBank", "UnstampedBank",
    "build_number_lexicon", "mine_strict_cases", "predict_register",
    "predict_recent_noun", "predict_trigram",
    "frame_v2", "mine_v2_cases", "between_nouns_v2", "TIER_OF_BUCKET",
    "REFUSAL_TAXONOMY", "COORDINATORS",
    "imposter_ceiling", "ImposterReport",
    "PhonGate", "GateResult", "THETA_PHON", "evidence_walk",
    "Page", "LawBook", "AUDIT_FLOOR",
    "TrigramScorer", "load_paradigm", "run_all", "demonstrative_judge",
    "sv_judge", "reflexive_judge", "existential_quant_judge",
    "npi_judge", "AGREEMENT_PARADIGMS",
    "audit_rule", "build_form_lexicon", "MODAL_AUX", "PERF_AUX",
    "BE_AUX",
    "gender_judge", "ppart_judge", "aggregate",
    "counts_of", "cone_identity", "junction_bigram", "mass",
    "InflectionTable", "classify", "apply_class", "inflect_signature",
    "RawTopicSpace", "Itinerary", "Journey", "JourneyResult", "Leg",
    "MirrorLoop", "Analysis", "THETA_DEFAULT",
    "MeaningGeometry", "build_corpus", "ensure_corpus", "ensure_source",
    "combine_sources", "coherence_report", "relatedness", "suffix_offsets",
    "SOURCES", "PROBE22_TRIPLES",
    "Rung",
    "elfix_path", "cmu_path", "ensure_elfix_importable",
    "__version__",
]
