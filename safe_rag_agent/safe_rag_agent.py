from agency_swarm import Agent

from rlg_common.config import get_config

_cfg = get_config()

safe_rag_agent = Agent(
    name=_cfg.get("agent_name") or "Safe Q&A Agent",
    description=(
        "A RAG agent that checks what it is about to remember: every document "
        "is scanned for sensitive data before ingestion, and the knowledge "
        "base can be audited on demand."
    ),
    instructions="./instructions.md",
    tools_folder="./tools",
    files_folder="./files",
    model=_cfg["model"],
)
