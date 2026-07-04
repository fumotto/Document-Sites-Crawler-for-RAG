import src.app.crawler.statistics_calculator as stats_module
from src.app.crawler.statistics_calculator import StatisticsCalculator


def test_word_and_char_count_computed_correctly():
    # TestID: STAT-001
    calculator = StatisticsCalculator()

    result = calculator.calculate("hello world foo")

    assert result.word_count == 3
    assert result.char_count == len("hello world foo")


def test_token_count_uses_tiktoken_when_available(monkeypatch):
    # TestID: STAT-002
    encode_calls = []

    class FakeEncoding:
        def encode(self, text):
            encode_calls.append(text)
            return list(range(len(text.split())))  # 1 fake token per word

    monkeypatch.setattr(stats_module, "_TIKTOKEN_AVAILABLE", True)
    monkeypatch.setattr(stats_module, "_ENCODING", FakeEncoding())

    calculator = StatisticsCalculator()
    result = calculator.calculate("one two three four five")

    assert result.token_count == 5
    # Confirms the tiktoken branch (not the char//4 fallback) actually ran.
    assert encode_calls == ["one two three four five"]


def test_token_count_falls_back_to_char_based_estimate_when_tiktoken_unavailable(monkeypatch):
    # TestID: STAT-003
    monkeypatch.setattr(stats_module, "_TIKTOKEN_AVAILABLE", False)
    monkeypatch.setattr(stats_module, "_ENCODING", None)

    calculator = StatisticsCalculator()
    text = "x" * 40
    result = calculator.calculate(text)

    assert result.token_count == max(1, len(text) // 4)


def test_empty_string_fallback_token_count_is_exactly_one(monkeypatch):
    # TestID: STAT-004
    monkeypatch.setattr(stats_module, "_TIKTOKEN_AVAILABLE", False)
    monkeypatch.setattr(stats_module, "_ENCODING", None)

    calculator = StatisticsCalculator()
    result = calculator.calculate("")

    assert result.word_count == 0
    assert result.char_count == 0
    assert result.token_count == 1  # max(1, 0 // 4) == 1


def test_empty_string_tiktoken_branch_not_forced_to_one(monkeypatch):
    # TestID: STAT-005
    class FakeEncoding:
        def encode(self, text):
            return []  # empty string encodes to zero tokens

    monkeypatch.setattr(stats_module, "_TIKTOKEN_AVAILABLE", True)
    monkeypatch.setattr(stats_module, "_ENCODING", FakeEncoding())

    calculator = StatisticsCalculator()
    result = calculator.calculate("")

    # Unlike the fallback path (which forces a minimum of 1), the tiktoken
    # branch returns whatever encode() reports, which can legitimately be 0.
    assert result.token_count == 0


def test_encode_exception_falls_back_to_estimation(monkeypatch):
    # TestID: STAT-006
    class BrokenEncoding:
        def encode(self, text):
            raise RuntimeError("encode failed")

    monkeypatch.setattr(stats_module, "_TIKTOKEN_AVAILABLE", True)
    monkeypatch.setattr(stats_module, "_ENCODING", BrokenEncoding())

    calculator = StatisticsCalculator()
    text = "some text here"
    result = calculator.calculate(text)

    assert result.token_count == max(1, len(text) // 4)
