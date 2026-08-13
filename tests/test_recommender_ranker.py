"""Wave 3, Milestone 3 — cosine ranking, Top-N, tie-breaking & fallback tests.

Covers TC-REC-006 (Top-N default-3 ranking on the canonical query), TC-REC-007
(determinism and tie-breaking by corpus order then title), TC-REC-008 (cold
start / min-skills guidance without crash), and TC-REC-009 (zero-match and
partial-match fallbacks), plus the result data model, Top-N clamping, matched-
skill marking, threshold behavior, and no-module-scope-fitting isolation.

Reference: SPEC.md Part III — FR-242 (cosine Top-N), FR-243 (determinism),
FR-244 (cold start / zero-match / partial-match fallbacks), FR-238/FR-245
(result data model).
"""

import os
import subprocess
import sys

import pytest

from decodebot.recommender import (
    DEFAULT_MIN_SKILLS,
    DEFAULT_TOP_N,
    MAX_TOP_N,
    STATUS_GUIDANCE,
    STATUS_OK,
    STATUS_PARTIAL_MATCH,
    STATUS_ZERO_MATCH,
    CareerProfile,
    Corpus,
    RecommendationOutcome,
    RecommendationResult,
    SkillSet,
    build_feature_pipeline,
    build_recommendation,
    builtin_corpus,
    clamp_top_n,
    guidance_outcome,
    matched_skills_text,
    partial_match_outcome,
    similarity_percent,
    zero_match_outcome,
)
from decodebot.recommender import corpus as corpus_module

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CANONICAL_QUERY = "Python, SQL, Machine Learning"


@pytest.fixture(autouse=True)
def _clear_cache():
    corpus_module._CACHE.clear()
    yield
    corpus_module._CACHE.clear()


def _profile(title, skills, description=""):
    if isinstance(skills, str):
        skills = [skill.strip() for skill in skills.split(",")]
    return CareerProfile(
        title=title,
        skills=SkillSet.from_list(skills),
        description=description,
    )


def _run_subprocess(script):
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


class TestTopNRanking:
    """TC-REC-006: default-3 ranking on the canonical query."""

    def test_canonical_query_returns_exactly_three(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        assert outcome.status == STATUS_OK
        assert len(outcome.results) == 3

    def test_similarities_descend(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        scores = [result.similarity for result in outcome.results]
        assert scores == sorted(scores, reverse=True)

    def test_ranks_assigned_sequentially(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        assert [result.rank for result in outcome.results] == [1, 2, 3]

    def test_results_are_structured(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        for result in outcome.results:
            assert isinstance(result, RecommendationResult)
            assert result.title
            assert len(result.skills) > 0
            assert 0.0 <= result.similarity <= 1.0

    def test_top_n_one_returns_single_result(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, top_n=1)
        assert len(outcome.results) == 1
        assert outcome.results[0].rank == 1

    def test_top_n_larger_than_corpus_returns_all(self):
        corpus = Corpus(
            profiles=(
                _profile("Backend Developer", "Python, SQL, FastAPI"),
                _profile("Data Scientist", "Python, SQL, Machine Learning"),
            )
        )
        outcome = build_recommendation(corpus, CANONICAL_QUERY, top_n=5)
        assert len(outcome.results) == 2

    def test_two_entry_corpus_clamps_top_n(self):
        corpus = Corpus(
            profiles=(
                _profile("Backend Developer", "Python, SQL, FastAPI"),
                _profile("Data Scientist", "Python, SQL, Machine Learning"),
            )
        )
        outcome = build_recommendation(corpus, CANONICAL_QUERY)
        assert len(outcome.results) == 2


class TestClampTopN:
    def test_default_is_three(self):
        assert clamp_top_n(None, 24) == 3

    def test_default_bounded_by_corpus(self):
        assert clamp_top_n(None, 2) == 2

    def test_above_max_capped_at_ten(self):
        assert clamp_top_n(50, 24) == MAX_TOP_N

    def test_larger_than_corpus_clamped(self):
        assert clamp_top_n(4, 2) == 2

    def test_one_returns_one(self):
        assert clamp_top_n(1, 24) == 1

    def test_non_integer_falls_back_to_default(self):
        assert clamp_top_n("nonsense", 24) == DEFAULT_TOP_N


class TestDeterminism:
    """TC-REC-007: byte-identical output; ties broken by corpus order, then title."""

    def test_repeated_runs_identical(self):
        first = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        second = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        assert first == second
        assert [r.title for r in first.results] == [r.title for r in second.results]

    def test_two_pipelines_identical(self):
        pipeline = build_feature_pipeline(builtin_corpus())
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, pipeline=pipeline)
        expected = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        assert outcome == expected

    def test_ties_broken_by_corpus_order_not_title(self):
        corpus = Corpus(
            profiles=(
                _profile("Zulu", ["Python", "SQL", "Machine Learning"], "First."),
                _profile("Alpha", ["Python", "SQL", "Machine Learning"], "Second."),
            )
        )
        outcome = build_recommendation(corpus, CANONICAL_QUERY)
        assert [r.title for r in outcome.results] == ["Zulu", "Alpha"]
        assert outcome.results[0].similarity == outcome.results[1].similarity

    def test_tie_break_stable_across_runs(self):
        corpus = Corpus(
            profiles=(
                _profile("Zulu", ["Python", "SQL", "Machine Learning"], "First."),
                _profile("Alpha", ["Python", "SQL", "Machine Learning"], "Second."),
            )
        )
        assert build_recommendation(corpus, CANONICAL_QUERY) == build_recommendation(
            corpus, CANONICAL_QUERY
        )


class TestColdStartGuidance:
    """TC-REC-008: fewer than the minimum skills yields friendly guidance."""

    def test_none_input_returns_guidance(self):
        outcome = build_recommendation(builtin_corpus(), None)
        assert outcome.status == STATUS_GUIDANCE
        assert not outcome.has_results
        assert outcome.message

    def test_empty_input_returns_guidance(self):
        outcome = build_recommendation(builtin_corpus(), "")
        assert outcome.status == STATUS_GUIDANCE

    def test_two_skills_returns_guidance(self):
        outcome = build_recommendation(builtin_corpus(), "Python, SQL")
        assert outcome.status == STATUS_GUIDANCE
        assert not outcome.has_results

    def test_guidance_message_lists_example_skills(self):
        outcome = build_recommendation(builtin_corpus(), "Python")
        assert "Python" in outcome.message
        assert "SQL" in outcome.message
        assert "Machine Learning" in outcome.message
        assert str(DEFAULT_MIN_SKILLS) in outcome.message

    def test_no_exception_for_cold_start(self):
        outcome = build_recommendation(builtin_corpus(), "Python, SQL")
        assert outcome.status == STATUS_GUIDANCE

    def test_min_skills_override(self):
        outcome = build_recommendation(builtin_corpus(), "Python, SQL", min_skills=2)
        assert outcome.status == STATUS_OK
        assert len(outcome.results) == 3

    def test_guidance_outcome_helper(self):
        outcome = guidance_outcome(Exception("boom"))
        assert outcome.status == STATUS_GUIDANCE
        assert "Python" in outcome.message


class TestZeroMatch:
    """TC-REC-009: out-of-vocabulary query → zero-match status."""

    def test_all_unknown_skills_zero_match(self):
        outcome = build_recommendation(builtin_corpus(), "Qwzx, Kvlm, Zjmt")
        assert outcome.status == STATUS_ZERO_MATCH
        assert not outcome.has_results
        assert outcome.message

    def test_zero_match_message_is_helpful(self):
        outcome = build_recommendation(builtin_corpus(), "Qwzx, Kvlm, Zjmt")
        assert "skills" in outcome.message.lower()

    def test_zero_match_helper(self):
        outcome = zero_match_outcome()
        assert outcome.status == STATUS_ZERO_MATCH
        assert outcome.message


class TestPartialMatch:
    """TC-REC-009: threshold exclusion empties list → partial-match fallback."""

    def test_impossible_threshold_returns_partial_match(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, threshold=1.5)
        assert outcome.status == STATUS_PARTIAL_MATCH
        assert outcome.has_results
        assert outcome.message

    def test_partial_match_returns_best_profiles(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, threshold=1.5)
        assert len(outcome.results) == 3

    def test_partial_match_label_clear(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, threshold=1.5)
        assert "partial" in outcome.message.lower()

    def test_inclusive_threshold_keeps_ok_status(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, threshold=0.0)
        assert outcome.status == STATUS_OK

    def test_threshold_filters_below_floor(self):
        baseline = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        floor = sum(result.similarity for result in baseline.results) / len(baseline.results)
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY, threshold=floor)
        assert outcome.status == STATUS_OK
        assert len(outcome.results) >= 1
        assert len(outcome.results) <= 3
        for result in outcome.results:
            assert result.similarity >= floor

    def test_partial_match_helper(self):
        result = RecommendationResult(title="X", skills=SkillSet.from_list(["Python"]))
        outcome = partial_match_outcome((result,))
        assert outcome.status == STATUS_PARTIAL_MATCH
        assert outcome.results == (result,)


class TestMatchedSkills:
    def test_matched_skills_marked(self):
        outcome = build_recommendation(builtin_corpus(), CANONICAL_QUERY)
        top = outcome.results[0]
        assert isinstance(top.matched_skills, tuple)
        query_skills = ("python", "sql", "machine learning")
        for skill in top.matched_skills:
            assert skill in query_skills
        assert "python" in top.matched_skills

    def test_matched_skills_case_insensitive(self):
        outcome = build_recommendation(builtin_corpus(), "python, sql, machine learning")
        top = outcome.results[0]
        assert "python" in top.matched_skills


class TestResultModel:
    def test_result_defaults(self):
        result = RecommendationResult(
            title="Backend Developer", skills=SkillSet.from_list(["Python"])
        )
        assert result.rank == 0
        assert result.similarity == 0.0
        assert result.matched_skills == ()

    def test_outcome_defaults(self):
        outcome = RecommendationOutcome(results=())
        assert outcome.status == STATUS_OK
        assert not outcome.has_results

    def test_similarity_percent_helper(self):
        assert similarity_percent(0.873) == 87
        assert similarity_percent(0.5) == 50

    def test_matched_skills_text_helper(self):
        assert matched_skills_text(("python", "sql")) == "python, sql"
        assert matched_skills_text(()) == ""


class TestRegressionW3M1W3M2:
    def test_recommendation_result_re_exported(self):
        assert corpus_module.RecommendationResult is RecommendationResult

    def test_builtin_corpus_unchanged(self):
        assert len(builtin_corpus()) >= 20

    def test_skillset_input_accepted(self):
        skills = SkillSet.from_list(["Python", "SQL", "Machine Learning"])
        outcome = build_recommendation(builtin_corpus(), skills)
        assert outcome.status == STATUS_OK


class TestNoModuleScopeFitting:
    def test_import_does_not_load_sklearn(self):
        script = (
            "import sys\n"
            "import decodebot.recommender.ranker\n"
            "import decodebot.recommender.fallbacks\n"
            "import decodebot.recommender.result\n"
            "import decodebot.recommender\n"
            "if 'sklearn' in sys.modules:\n"
            "    print('SKLEARN-PRESENT')\n"
            "    sys.exit(1)\n"
            "if 'numpy' in sys.modules:\n"
            "    print('NUMPY-PRESENT')\n"
            "    sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
