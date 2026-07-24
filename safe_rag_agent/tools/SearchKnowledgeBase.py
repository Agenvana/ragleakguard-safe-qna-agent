import json
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

from rlg_common import openai_store

load_dotenv()

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SearchKnowledgeBase(BaseTool):
    """
    Retrieve relevant passages from the knowledge base to ground an answer.
    Works immediately after ingestion (the store is resolved at call time, no
    restart needed). Only documents that passed the ingestion scan, or were
    explicitly accepted through it, exist in the store. When quoting retrieved
    content, never repeat sensitive identifier values; summarize around them.
    """

    query: str = Field(..., description="What to search the knowledge base for.")
    vector_store_id: Optional[str] = Field(
        None, description="Store to search; omit to use the agent's own knowledge base."
    )

    def run(self):
        vs_id = openai_store.resolve_vector_store_id(_AGENT_DIR, explicit=self.vector_store_id)
        if not vs_id:
            return json.dumps({
                "event": "saferag.error",
                "error": "no knowledge base yet; ingest a document first",
            })
        try:
            results = openai_store.search_vector_store(vs_id, self.query)
        except Exception as e:  # API/auth errors carry no document content
            return json.dumps({"event": "saferag.error", "error": f"{type(e).__name__}: {e}"})
        return json.dumps(
            {"event": "saferag.search", "vector_store_id": vs_id, "results": results},
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    print(SearchKnowledgeBase(query="refund policy").run())
