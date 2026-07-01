from dataclasses import dataclass

@dataclass(frozen=True)
class PageDTO:
    page_hash: str
    url: str
    content: str
    metadata: dict