import json
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from dotenv import load_dotenv
from pydantic import Field

from rlg_common import config as rlg_config
from rlg_common import files as rlg_files
from rlg_common import summary

load_dotenv()


class ScanDocument(BaseTool):
    """
    Scan ONE document for sensitive data before deciding whether to ingest it
    into the knowledge base. Returns a verdict (SAFE_TO_INGEST or
    REVIEW_REQUIRED) plus findings-METADATA only: counts, types, severities and
    fully-masked samples. The detected values themselves are never returned.
    """

    path: str = Field(..., description="Path to the document to scan.")
    locale: Optional[str] = Field(
        None,
        description="Optional country pack, e.g. 'au' for Australian identifiers. "
        "Defaults to the onboarding configuration.",
    )

    def run(self):
        if not os.path.isfile(self.path):
            return json.dumps({"event": "saferag.error", "error": f"file not found: {self.path}"})
        locale = self.locale or rlg_config.get_default_locale()
        rec = summary.scan_text(rlg_files.read_text(self.path), locale=locale)
        verdict = "SAFE_TO_INGEST" if rec["findings"] == 0 else "REVIEW_REQUIRED"
        return json.dumps(
            {
                "event": "saferag.scan_document",
                "file": os.path.basename(self.path),
                "verdict": verdict,
                "findings": rec["findings"],
                "types": rec["types"],
                "samples": rec["samples"],
                "locale": locale,
            },
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("Patient Jane Doe, email jane.doe@example.com, phone +1 415 555 0100.")
        p = fh.name
    print(ScanDocument(path=p).run())
    os.unlink(p)
