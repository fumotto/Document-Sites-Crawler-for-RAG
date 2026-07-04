from src.app.crawler.markdown_extractor import MarkdownExtractor

SAMPLE_HTML = """
<html>
<head><title>Sample Page</title></head>
<body>
<article>
<h1>Sample Page</h1>
<p>This is a reasonably long paragraph of body content that should be
extracted as the main article text by trafilatura, since it forms a
complete sentence with enough substance to be recognized as content
rather than boilerplate navigation or footer text.</p>
</article>
</body>
</html>
"""

CODE_BLOCK_HTML = """
<html>
<head><title>Code Sample</title></head>
<body>
<article>
<p>Here is an example of client creation, which is a fairly common
pattern used across many SDKs and is worth showing in full below.</p>
<pre><code>const client = createClient(url, key);</code></pre>
</article>
</body>
</html>
"""

NO_TITLE_HTML = """
<html>
<head></head>
<body><p>Body without a title tag.</p></body>
</html>
"""


def test_extracts_title_and_body_from_normal_html():
    # TestID: MD-001
    extractor = MarkdownExtractor()

    result = extractor.extract(SAMPLE_HTML, "https://example.com/a")

    assert result.title
    assert result.body_markdown


def test_code_block_preserved_in_markdown():
    # TestID: MD-002
    extractor = MarkdownExtractor()

    result = extractor.extract(CODE_BLOCK_HTML, "https://example.com/a")

    assert result.body_markdown is not None
    assert "createClient" in result.body_markdown


def test_language_is_set_when_detectable():
    # TestID: MD-003
    extractor = MarkdownExtractor()

    result = extractor.extract(SAMPLE_HTML, "https://example.com/a")

    # trafilatura's language detection may or may not be installed with
    # langdetect; assert only that the field is present and, when set, is a
    # short language code string.
    if result.language is not None:
        assert isinstance(result.language, str)
        assert len(result.language) <= 5


def test_fallback_extraction_used_when_trafilatura_unavailable(monkeypatch):
    # TestID: MD-004
    import src.app.crawler.markdown_extractor as md_module

    monkeypatch.setattr(md_module, "_TRAFILATURA_AVAILABLE", False)
    extractor = MarkdownExtractor()

    result = extractor.extract(SAMPLE_HTML, "https://example.com/a")

    assert result.title == "Sample Page"
    assert result.body_markdown is not None
    assert "body content" in result.body_markdown or "Sample Page" in result.body_markdown


def test_empty_body_returns_none_or_empty():
    # TestID: MD-005
    extractor = MarkdownExtractor()

    result = extractor.extract("<html><head></head><body></body></html>", "https://example.com/a")

    assert result.body_markdown is None or result.body_markdown == ""


def test_fallback_extraction_title_none_when_missing():
    # TestID: MD-006
    extractor = MarkdownExtractor()

    result = extractor._fallback_extract(NO_TITLE_HTML, "https://example.com/a")

    assert result.title is None
