import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datetime import datetime, timezone

from src.app.builder.duplicate_resolver import DuplicateResolver
from src.app.models.page_metadata_record import PageMetadataRecord

def _meta(url, sha256, retrieved_at):
    return PageMetadataRecord(
        title="T", url=url, language="en", word_count=10, char_count=50,
        token_count=12, content_sha256=sha256, retrieved_at=retrieved_at, content_type="text/html",
    )


# TestID: DR-001
# TestID: DUP-001
def test_newest_retrieved_at_wins():
    resolver = DuplicateResolver()
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    new = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("hashA", _meta("https://example.com/a", "sha-dup", old)),
        ("hashB", _meta("https://example.com/b", "sha-dup", new)),
        ("hashC", _meta("https://example.com/c", "sha-unique", new)),
    ]
    result = resolver.resolve(items)
    canonical_urls = {r.url for _h, r in result.canonical}
    assert canonical_urls == {"https://example.com/b", "https://example.com/c"}
    assert len(result.excluded) == 1
    assert result.excluded[0][1].url == "https://example.com/a"
