import json
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

from rlg_common import config as rlg_config
from rlg_common import files as rlg_files
from rlg_common import openai_store, summary

load_dotenv()

_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SafeIngestDocument(BaseTool):
    """
    Add a document to the knowledge base ONLY after scanning it for sensitive
    data. If the scan finds anything, ingestion is REFUSED and the findings are
    reported as metadata (counts, types, masked samples) so the user can clean
    the document first. The user may explicitly accept the risk, in which case
    set force=true. Raw detected values are never returned.
    """

    path: str = Field(..., description="Path to the document to scan and ingest.")
    locale: Optional[str] = Field(
        None,
        description="Optional country pack, e.g. 'au' for Australian identifiers. "
        "Defaults to the onboarding configuration.",
    )
    force: bool = Field(
        False,
        description="Set true ONLY after the user explicitly accepts ingesting a "
        "document that scanned with findings.",
    )
    vector_store_id: Optional[str] = Field(
        None, description="Target vector store id; omit to use the agent's own knowledge base."
    )

    def run(self):
        if not os.path.isfile(self.path):
            return json.dumps({"event": "saferag.error", "error": f"file not found: {self.path}"})
        locale = self.locale or rlg_config.get_default_locale()
        rec = summary.scan_text(rlg_files.read_text(self.path), locale=locale)

        if rec["findings"] > 0 and not self.force:
            return json.dumps(
                {
                    "event": "saferag.ingest",
                    "status": "REFUSED",
                    "file": os.path.basename(self.path),
                    "reason": "document contains sensitive data; clean it or get explicit "
                    "user approval before ingesting (then re-run with force=true)",
                    "findings": rec["findings"],
                    "types": rec["types"],
                    "samples": rec["samples"],
                    "locale": locale,
                },
                indent=2,
                ensure_ascii=False,
            )

        try:
            vs_id, created = openai_store.get_or_create_vector_store(_AGENT_DIR, explicit=self.vector_store_id)
            file_id = openai_store.upload_file_to_vector_store(vs_id, self.path)
        except Exception as e:  # API/auth errors carry no document content
            return json.dumps({"event": "saferag.error", "error": f"{type(e).__name__}: {e}"})

        result = {
            "event": "saferag.ingest",
            "status": "INGESTED",
            "file": os.path.basename(self.path),
            "file_id": file_id,
            "vector_store_id": vs_id,
            "vector_store_created": created,
            "findings": rec["findings"],
            "types": rec["types"],
            "forced": bool(rec["findings"] and self.force),
            "locale": locale,
        }
        if created:
            result["note"] = (
                "a new knowledge-base vector store was created; file search over it "
                "attaches when the agency restarts"
            )
        return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("Refund policy: items may be returned within 30 days with receipt.")
        p = fh.name
    # Without an OPENAI_API_KEY this demonstrates the scan path only.
    print(SafeIngestDocument(path=p).run())
    os.unlink(p)
