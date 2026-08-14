"""W-5 acceptance (probe 21): the form|meaning rung.

Episodes are [shape | meaning] blocks through grid-47 a_mem; a cue with
one block zeroed retrieves the right episode cross-modally. Measured
100% both directions at chance 4%; assert >= 90%.
"""
from mirror import Rung

BANK = ["water", "music", "money", "house", "school", "church", "light",
        "night", "world", "heart", "field", "horse", "river", "stone",
        "voice", "road", "fire", "door", "glass", "bread", "child",
        "woman", "doctor", "window", "garden"]


def test_cross_modal_recall(embedder, geometry, tmp_path):
    words = [w for w in BANK
             if w in geometry and w in embedder.corpus][:24]
    assert len(words) >= 20, f"bank shrank to {len(words)} words"

    rung = Rung(embedder, geometry)
    mem, hooks, mids = rung.write_bank(words, path=str(tmp_path / "store"))

    for label, kw, floor in (
            ("meaning-only cue -> form episode", dict(form=False), 0.90),
            ("form-only cue -> meaning episode", dict(meaning=False), 0.90)):
        ok = sum(int(hooks.recall_context(rung.episode(w, **kw)).identity
                     == mids[w]) for w in words)
        rate = ok / len(words)
        print(f"\n{label}: {ok}/{len(words)} = {rate:.0%} "
              f"(chance {1 / len(words):.0%})")
        assert rate >= floor, f"{label}: {rate:.0%} < {floor:.0%}"
