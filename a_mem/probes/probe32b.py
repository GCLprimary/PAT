"""Probe 32b: PROPOSE-TIME STEERED GENERATION (the corrected, working run).
Steering happens at the proposal pool: trigram top-10 reranked by CENTERED
cosine to the interpolated waypoint target (+ 0.05*log count), keep top-4,
beam width 12. All measurement in centered space (global mean removed).
Measured: steer-p cos->B rises +0.083 -> +0.295 monotone, cos->A falls
+0.344 -> +0.099; REVERSED itinerary mirrors (+0.284 -> +0.101 to B,
+0.111 -> +0.324 to A) — causal control. Audit-only steering 2-3x weaker
(end +0.184); unsteered flat ~+0.05.
Laws: center before measuring (mandatory helper); the corridor is set at
proposal time (audit disposes only among what was proposed).
Core rerank inside the beam step:

    pool = tri[ctx2].most_common(10) or bi[last].most_common(6)
    pool = sorted(pool, key=lambda wc: centered(g.vec(wc[0])) @ target
                                       + 0.05*log1p(wc[1]), reverse=True)[:4]
"""
