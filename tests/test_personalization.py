import pytest

from decodebot.core.session import SessionState
from decodebot.rules.personalization import extract_name, sanitize_name, is_forget_request


class TestNameExtraction:
    def test_extract_my_name_is(self):
        assert extract_name("my name is Sara") == "Sara"

    def test_extract_i_am(self):
        assert extract_name("i am Ali") == "Ali"

    def test_extract_im(self):
        assert extract_name("i'm Bob") == "Bob"

    def test_extract_call_me(self):
        assert extract_name("call me Max") == "Max"

    def test_extract_set_name(self):
        assert extract_name("set name Priya") == "Priya"

    def test_no_match_returns_none(self):
        assert extract_name("hello there") is None

    def test_sanitize_removes_invalid_chars(self):
        assert sanitize_name("Alex99") == "Alex"

    def test_sanitize_multiple_words(self):
        assert sanitize_name("Anna Marie") == "Anna Marie"

    def test_sanitize_empty_returns_none(self):
        assert sanitize_name("") is None

    def test_sanitize_all_invalid_returns_none(self):
        assert sanitize_name("12345") is None

    def test_sanitize_truncates_long_names(self):
        long_name = "A" * 50
        result = sanitize_name(long_name)
        assert result is not None
        assert len(result) <= 30

    def test_forget_request_detected(self):
        assert is_forget_request("forget my name")
        assert is_forget_request("forget me")
        assert not is_forget_request("hello")


class TestPersonalizationIntegration:
    def test_name_stored_in_session(self):
        session = SessionState()
        name = extract_name("my name is Jo")
        assert name == "Jo"
        session.user_name = name
        assert session.user_name == "Jo"

    def test_reset_clears_name(self):
        session = SessionState()
        session.user_name = "Sam"
        session.reset()
        assert session.user_name is None
