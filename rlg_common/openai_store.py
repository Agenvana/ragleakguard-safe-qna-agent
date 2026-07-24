"""OpenAI vector-store access: resolve ids, read parsed chunks, upload files.

Reading uses the vector-store file-content endpoint, so a knowledge-base scan
audits exactly what the store remembers (the parsed chunk text), not the
original upload. All functions here are seams the test suite monkeypatches;
none of them ever place chunk text into a return value that leaves a tool.
"""
import os
import re
from typing import Any, Dict, Iterator, Optional, Tuple

_VS_SUFFIX = re.compile(r"_vs_([A-Za-z0-9_\-]+)$")
_CACHE_FILENAME = ".vector_store_id"
DEFAULT_STORE_NAME = "safe-rag-knowledge"


def _client():
    from openai import OpenAI
    return OpenAI()


def resolve_vector_store_id(agent_dir: str, explicit: Optional[str] = None) -> Optional[str]:
    """Resolution order: explicit arg > RLG_VECTOR_STORE_ID env > the agent's
    files folder renamed by agency-swarm to `files_vs_<id>` > local cache file
    written by a previous SafeIngestDocument run."""
    if explicit:
        return explicit
    env = os.environ.get("RLG_VECTOR_STORE_ID")
    if env:
        return env
    if os.path.isdir(agent_dir):
        for name in sorted(os.listdir(agent_dir)):
            m = _VS_SUFFIX.search(name)
            if m and os.path.isdir(os.path.join(agent_dir, name)):
                return m.group(1)
        cache = os.path.join(agent_dir, _CACHE_FILENAME)
        if os.path.isfile(cache):
            with open(cache, "r", encoding="utf-8") as fh:
                cached = fh.read().strip()
            if cached:
                return cached
    return None


def get_or_create_vector_store(agent_dir: str, explicit: Optional[str] = None) -> Tuple[str, bool]:
    """Resolve the agent's vector store, creating one if none exists yet.

    Returns (vector_store_id, created). A created id is cached next to the
    agent so later tool calls and scans find it again.
    """
    vs_id = resolve_vector_store_id(agent_dir, explicit=explicit)
    if vs_id:
        return vs_id, False
    store = _client().vector_stores.create(name=DEFAULT_STORE_NAME)
    try:
        with open(os.path.join(agent_dir, _CACHE_FILENAME), "w", encoding="utf-8") as fh:
            fh.write(store.id)
    except OSError:
        pass  # read-only filesystem: the id is still returned and usable
    return store.id, True


def iter_vector_store_chunks(vector_store_id: str) -> Iterator[Dict[str, Any]]:
    """Yield {"id", "text", "collection"} for every parsed content chunk."""
    client = _client()
    for f in client.vector_stores.files.list(vector_store_id=vector_store_id):
        label = getattr(f, "filename", None) or f.id
        content = client.vector_stores.files.content(f.id, vector_store_id=vector_store_id)
        for i, part in enumerate(content):
            text = getattr(part, "text", "") or ""
            if text:
                yield {"id": f"{label}#chunk{i}", "text": text, "collection": vector_store_id}


def search_vector_store(vector_store_id: str, query: str, max_results: int = 5) -> list:
    """Semantic search over the store's parsed chunks. Returns retrieved
    passages (this is the Q&A retrieval path, not a scan: only documents that
    passed, or were explicitly accepted through, the ingestion gate live in
    the store). Resolves at call time, so it works in the same session as the
    first ingestion, before FileSearch attaches at next boot."""
    client = _client()
    page = client.vector_stores.search(
        vector_store_id=vector_store_id, query=query, max_num_results=max_results
    )
    out = []
    for r in getattr(page, "data", []) or []:
        text = " ".join(
            getattr(part, "text", "") or "" for part in (getattr(r, "content", []) or [])
        ).strip()
        out.append({
            "file": getattr(r, "filename", None) or getattr(r, "file_id", "unknown"),
            "score": getattr(r, "score", None),
            "text": text,
        })
    return out


def upload_file_to_vector_store(vector_store_id: str, path: str) -> str:
    """Upload a local file and attach it to the vector store. Returns file id."""
    client = _client()
    with open(path, "rb") as fh:
        vs_file = client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store_id, file=fh
        )
    return vs_file.id
