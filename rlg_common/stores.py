"""Vector-store readers (read-only), kept as thin monkeypatchable seams."""
from typing import Any, Dict, Iterator, Optional


def iter_chroma_items(path: str, collection: Optional[str] = None) -> Iterator[Dict[str, Any]]:
    """Yield {"id", "text", "metadata", "collection"} from a local Chroma store."""
    from ragleakguard.connectors import read_chroma
    yield from read_chroma(path, collection=collection)
