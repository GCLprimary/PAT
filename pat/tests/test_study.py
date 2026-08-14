"""L-4: the schooled twin — study(), the fourth provenance class.

After studying the irregular-plurals page the session reports 'men' as
plural WITH lesson provenance AND the conflict against its induced
classification in the same breath — instruction that corrects an
inference, ledgered, never silent. Pages override classifications;
the attested pairs and the gate are untouched.
"""
import pytest

from pat import ReadingSession
from mirror import Page
from mirror.config import DATA_DIR as MIRROR_DATA


@pytest.fixture(scope="module")
def studied(organs):
    session = ReadingSession(organs, seed_bases=["detail", "lawsuit"])
    report = session.study(
        Page.load(MIRROR_DATA / "page_irregular_plurals.txt"))
    return session, report


def test_study_reports_and_ledgers(studied):
    session, report = studied
    print(f"\nstudy report: {report}")
    assert report["page"] == "irregular_plurals"
    assert report["lines"] == 52 and report["words"] == 104
    assert report["conflicts"] >= 3
    words = {c["word"] for c in session.lesson_conflicts}
    assert {"people", "men", "children"} <= words


def test_men_is_plural_with_lesson_provenance(studied):
    """The same breath: the answer, its provenance, and the conflict."""
    session, _ = studied
    num, prov = session.number_of("men")
    assert num == "pl" and prov == "lesson:irregular_plurals"
    yes, kprov = session.knows("men")
    assert yes and kprov == "lesson:irregular_plurals"
    conflict = next(c for c in session.lesson_conflicts
                    if c["word"] == "men")
    assert conflict["page_says"] == "page:pl"
    assert conflict["induced_says"] == "induced:sg"
    print(f"\n'men' -> {num} ({prov}); ledgered conflict: {conflict}")


def test_fourth_provenance_class(studied):
    session, _ = studied
    totals = session.provenance_totals()
    print(f"\nprovenance totals after study: {totals}")
    assert totals.get("lesson", 0) >= 90     # 104 words, most in CMU
    assert totals.get("birth", 0) == 2


def test_off_page_untouched(studied, organs):
    """The page never reaches past its own rows: induced answers and
    the analyze gate are exactly as before study."""
    session, _ = studied
    num, prov = session.number_of("tables")
    assert num == "pl" and prov == "induced"
    mode, b, sfx, verdict = session.analyze_word("details")
    assert (mode, b, sfx, verdict) == ("BOUND", "detail", "s", "OK")
