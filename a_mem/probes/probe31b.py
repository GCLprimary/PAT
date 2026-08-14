"""Probe 31b: DUAL-THRESHOLD stage (the winning working-memory policy).
integrate at theta_c=0.45 (generous consonance); page-turn ONLY on a
mutually-coherent pending pair at theta_a=0.65 (strict commitment), onto
their blend. Measured on the interruption battery (36 episodes, editorial
interrupters): AT-INTERRUPT 71% (memoryless 1%, single-theta v1 18%),
in-seg 99%, post 94%, overall 83% vs v1 69%; cost = seg-start 64%
(deliberate-turn lag tax). Law: consonance and commitment are different
judgments needing different bars.
Reference implementation of the stage update:

    if state is None: state = v; pend = None
    elif cos(state, v) >= THETA_C:
        state = norm(BLEND*state + (1-BLEND)*v); pend = None
    elif pend is not None and cos(pend, v) >= THETA_A:
        state = norm(pend + v); pend = None          # deliberate turn
    else:
        pend = v                                     # lone dissonant: HOLD
"""
