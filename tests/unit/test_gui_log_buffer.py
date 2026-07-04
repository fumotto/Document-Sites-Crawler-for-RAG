import logging

from src.app.gui.log_buffer import InMemoryLogHandler


def test_emit_accumulates_and_get_lines_since_returns_all():
    # TestID: LB-001
    handler = InMemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_lb_001")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("first")
    logger.info("second")

    entries = handler.get_lines_since(-1)

    assert [e.text for e in entries] == ["first", "second"]


def test_get_lines_since_returns_only_new_entries():
    # TestID: LB-002
    handler = InMemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_lb_002")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("first")
    logger.info("second")
    first_batch = handler.get_lines_since(-1)
    last_index = first_batch[-1].index

    logger.info("third")
    second_batch = handler.get_lines_since(last_index)

    assert [e.text for e in second_batch] == ["third"]


def test_ring_buffer_discards_oldest_entries_beyond_max_lines():
    # TestID: LB-003
    handler = InMemoryLogHandler(max_lines=3)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_lb_003")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for i in range(5):
        logger.info(f"line{i}")

    entries = handler.get_lines_since(-1)

    assert len(entries) == 3
    assert [e.text for e in entries] == ["line2", "line3", "line4"]


def test_clear_resets_buffer_and_index():
    # TestID: LB-004
    handler = InMemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_lb_004")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("before clear")
    handler.clear()

    assert handler.get_lines_since(-1) == []

    logger.info("after clear")
    entries = handler.get_lines_since(-1)
    assert entries[0].index == 0
    assert entries[0].text == "after clear"


def test_format_exception_falls_back_to_get_message():
    # TestID: LB-005
    handler = InMemoryLogHandler()

    class BrokenFormatter(logging.Formatter):
        def format(self, record):
            raise RuntimeError("formatter broken")

    handler.setFormatter(BrokenFormatter())
    logger = logging.getLogger("test_lb_005")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("fallback message")

    entries = handler.get_lines_since(-1)
    assert entries[0].text == "fallback message"
