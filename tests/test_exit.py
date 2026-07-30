"""Tests for exit detection (FR-036–FR-045).

Covers TC-EXIT-001 through TC-EXIT-010.
"""

import pytest

from decodebot.rules import exit
from decodebot.utils.normalization import normalize


class TestExitDetection:
    """Tests for exit pattern matching."""

    @pytest.mark.parametrize("phrase", [
        "bye",
        "exit",
        "quit",
        "goodbye",
        "see you",
        "later",
        "stop",
        "end",
        "close",
    ])
    def test_tc_exit_basic_exits(self, phrase):
        """Basic exit phrases are recognized."""
        assert exit.matches(normalize(phrase)), f"'{phrase}' should be an exit"

    def test_tc_exit_single_char_q(self):
        """TC-EXIT-005: 'q' alone is an exit."""
        assert exit.matches("q")

    def test_tc_exit_quick_question_not_exit(self):
        """TC-U-008: 'quitter' is NOT an exit."""
        assert not exit.matches("quitter")

    def test_tc_exit_contextual(self):
        """TC-EXIT-009: 'gotta go, bye' is an exit."""
        assert exit.matches(normalize("gotta go, bye"))

    def test_tc_exit_case_insensitive(self):
        """TC-EXIT-010: 'QUIT' is an exit."""
        assert exit.matches(normalize("QUIT"))

    def test_tc_u_009_negation_exclusion(self):
        """TC-U-009: 'don't go' is NOT an exit."""
        assert not exit.matches("don't go")

    def test_negation_variants(self):
        """Various negation phrases are not treated as exit."""
        assert not exit.matches("never leaving")
        assert not exit.matches("dont go")

    def test_exit_response_pool_nonempty(self):
        """EXIT_RESPONSES is non-empty."""
        assert len(exit.EXIT_RESPONSES) >= 6

    def test_exit_response_variety(self):
        """At least 3 distinct farewell responses across many calls."""
        import random
        random.seed(42)
        responses = {exit.get_response() for _ in range(50)}
        assert len(responses) >= 3

    def test_exit_patterns_abundant(self):
        """At least 10 distinct exit patterns exist (FR-036)."""
        assert len(exit.EXIT_PATTERNS) >= 10
