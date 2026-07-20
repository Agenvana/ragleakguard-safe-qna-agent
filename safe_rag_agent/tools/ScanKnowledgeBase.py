import json
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

from rlg_common import config as rlg_config
from rlg_common import openai_store, summary

load_dotenv()

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ScanKnowledgeBase(BaseTool):
    """
    Audit the knowledge base on demand: scan every parsed chunk the vector store
    remembers and report exposed sensitive data as findings-METADATA only
    (counts, types, severities, risk level, chunk ids, masked samples) plus a
    Markdown risk report. Read-only; raw values are never returned.
    """

    vector_store_id: Optional[str] = Field(
        None, description="Vector store id to audit; omit to use the agent's own knowledge base."
    )
    locale: Optional[str] = Field(
        None,
        description="Optional country pack, e.g. 'au' for Australian identifiers. "
        "Defaults to the onboarding configuration.",
    )

    def run(self):
        vs_id = openai_store.resolve_vector_store_id(_AGENT_DIR, explicit=self.vector_store_id)
        if not vs_id:
            return json.dumps({
                "event": "saferag.error",
                "error": "no knowledge base found yet; ingest a document first or pass vector_store_id",
            })
        locale = self.locale or rlg_config.get_default_locale()
        try:
            items = openai_store.iter_vector_store_chunks(vs_id)
            records = summary.scan_items(items, locale=locale)
        except Exception as e:  # API/auth errors carry no document content
            return json.dumps({"event": "saferag.error", "error": f"{type(e).__name__}: {e}"})
        result = summary.build_result("openai_vector_store", vs_id, records, locale=locale)
        return summary.to_json(result)


if __name__ == "__main__":
    print(ScanKnowledgeBase().run())
