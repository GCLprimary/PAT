"""Probe 37 (corrected): THE ENGLISH TEST -- agreement with attractors.
Number lexicon from the system's own mined -s pairs (12,563 sg / 12,563 pl,
ambiguous dropped). FIRST RUN was a broken ruler: 'first DET-N = subject'
mislabels sentence-initial adjuncts (register 44% was the heuristic
failing, not the mechanism; recent-noun 61% was the tell).
STRICT FRAME: sentence-initial DET-N subject; material must be a PP chain
(preposition-launched); between-nouns count only when det/prep-preceded.
MEASURED (240 cases, 12 true attractors, held 5% of pinned corpus_big):
  trigram      87% / 67%
  recent-noun  94% / 17%   <- seduced by the attractor, as the paradigm predicts
  REGISTER     94% / 83%   (10/12) -- holds the opener to the verb
Finding: subject identification is the frontier, not agreement itself.
Caveat: n=12 attractors -- directional, pin the fixture, band the gate.
"""
