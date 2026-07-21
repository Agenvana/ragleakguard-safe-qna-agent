import os

from agency_swarm import Agent

from rlg_common.config import get_config
from rlg_common.openai_store import resolve_vector_store_id

_cfg = get_config()
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


def _file_search_tools():
    """Attach FileSearch explicitly by store id (cache/env/explicit).

    Deliberately NOT the files_folder `*_vs_<id>` convention: agency-swarm
    syncs that folder's contents to the store at boot and deletes store files
    with no local mirror, which would silently purge documents ingested via
    SafeIngestDocument. Explicit attachment has no sync side effects.
    """
    vs_id = resolve_vector_store_id(_AGENT_DIR)
    if not vs_id:
        return []  # retrieval attaches on the first boot after a store exists
    try:
        from agency_swarm import FileSearchTool
    except ImportError:
        from agents import FileSearchTool
    return [FileSearchTool(vector_store_ids=[vs_id])]


safe_rag_agent = Agent(
    name=_cfg.get("agent_name") or "Safe Q&A Agent",
    description=(
        "A RAG agent that checks what it is about to remember: every document "
        "is scanned for sensitive data before ingestion, and the knowledge "
        "base can be audited on demand."
    ),
    instructions="./instructions.md",
    tools=_file_search_tools(),
    tools_folder="./tools",
    model=_cfg["model"],
)
