from datetime import datetime, timezone

from src.app.builder.chunk_builder import ChunkBuilder
from src.app.models.page_metadata_record import PageMetadataRecord


def _meta(url, word_count, sha256="sha", title=None):
    return PageMetadataRecord(
        title=title, url=url, language="en", word_count=word_count, char_count=word_count * 5,
        token_count=word_count, content_sha256=sha256,
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc), content_type="text/html",
    )


def test_pages_within_word_limit_combined_into_one_file():
    # TestID: CB-001
    builder = ChunkBuilder()
    pages = [("h1", _meta("https://e.com/a", 100)), ("h2", _meta("https://e.com/b", 100))]
    bodies = {"h1": "body a", "h2": "body b"}

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    assert len(result.files) == 1
    assert "body a" in result.files[0].content
    assert "body b" in result.files[0].content


def test_word_limit_exceeded_splits_into_new_file():
    # TestID: CB-002
    builder = ChunkBuilder()
    pages = [("h1", _meta("https://e.com/a", 600)), ("h2", _meta("https://e.com/b", 600))]
    bodies = {"h1": "body a", "h2": "body b"}

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    assert len(result.files) == 2


def test_single_page_never_spans_multiple_files():
    # TestID: CB-003
    builder = ChunkBuilder()
    pages = [
        ("h1", _meta("https://e.com/a", 600)),
        ("h2", _meta("https://e.com/b", 600)),
        ("h3", _meta("https://e.com/c", 600)),
    ]
    bodies = {"h1": "AAA", "h2": "BBB", "h3": "CCC"}

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    contents = [f.content for f in result.files]
    for body in ("AAA", "BBB", "CCC"):
        matches = [c for c in contents if body in c]
        assert len(matches) == 1


def test_single_page_exceeding_limit_gets_own_file_with_warning():
    # TestID: CB-004
    builder = ChunkBuilder()
    pages = [("h1", _meta("https://e.com/huge", 2000))]
    bodies = {"h1": "huge body"}

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    assert len(result.files) == 1
    assert result.files[0].content == "huge body"
    assert len(result.warnings) == 1
    assert "https://e.com/huge" in result.warnings[0]


def test_chunk_records_reference_correct_filenames():
    # TestID: CB-005
    builder = ChunkBuilder()
    pages = [("h1", _meta("https://e.com/a", 600)), ("h2", _meta("https://e.com/b", 600))]
    bodies = {"h1": "AAA", "h2": "BBB"}

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    filenames_produced = {f.filename for f in result.files}
    for record in result.chunk_records:
        assert record.file in filenames_produced


def test_empty_input_produces_no_files():
    # TestID: CB-006
    builder = ChunkBuilder()

    result = builder.build_chunks([], {}, word_limit=1000)

    assert result.files == []
    assert result.chunk_records == []


def test_missing_page_body_treated_as_empty_string():
    # TestID: CB-007
    builder = ChunkBuilder()
    pages = [("h1", _meta("https://e.com/a", 100))]
    bodies = {}  # h1 missing entirely

    result = builder.build_chunks(pages, bodies, word_limit=1000)

    assert len(result.files) == 1
    assert result.files[0].content == ""


def test_word_limit_boundary_exact_vs_exceeded():
    # TestID: CB-008
    builder = ChunkBuilder()

    # Exactly at the limit: current_word_count + page_word_count == word_limit
    # should NOT trigger a split (condition uses strict '>').
    pages_exact = [("h1", _meta("https://e.com/a", 500)), ("h2", _meta("https://e.com/b", 500))]
    bodies = {"h1": "AAA", "h2": "BBB"}
    result_exact = builder.build_chunks(pages_exact, bodies, word_limit=1000)
    assert len(result_exact.files) == 1

    # One word over the limit should trigger a split.
    pages_over = [("h1", _meta("https://e.com/a", 500)), ("h2", _meta("https://e.com/b", 501))]
    result_over = builder.build_chunks(pages_over, bodies, word_limit=1000)
    assert len(result_over.files) == 2
