"""Findings-metadata reduction layer.

Every tool in this repo routes scan results through this module before
returning anything. The contract (the metadata-only principle from
RAGLeakGuard): tool outputs may contain counts, finding types, severities,
risk levels, record ids, file names, span lengths and confidence scores.
They may NEVER contain the detected values themselves, and NEVER document
text. A chat transcript is itself a data store; copying raw findings into it
would turn the auditor into a leak.

Enforced by tests/test_metadata_only.py, which mirrors
test_state_and_payload_never_contain_raw_values in the RAGLeakGuard repo.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from ragleakguard.report import SEVERITY, build_report

MASK_CHAR = "•"  # bullet: masked samples contain zero original characters
MAX_SAMPLES_PER_RECORD = 3
MAX_FLAGGED_RECORDS = 25

# Test seam: the suite monkeypatches this with a deterministic fake detector.
_detect_impl = None


def _detect(text: str, locale: Optional[str] = None) -> List[Dict[str, Any]]:
    global _detect_impl
    if _detect_impl is None:
        from ragleakguard.detect import detect as real_detect
        _detect_impl = real_detect
    return _detect_impl(text, locale=locale)


def summarize_findings(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reduce one record's raw findings to metadata.

    Reads only the type, score and the LENGTH of each matched span. The raw
    matched text is measured and discarded, never copied.
    """
    types: Dict[str, int] = {}
    for f in findings:
        types[f["type"]] = types.get(f["type"], 0) + 1
    samples = [
        {
            "type": f["type"],
            "masked": MASK_CHAR * min(len(f.get("text") or ""), 12),
            "length": len(f.get("text") or ""),
            "confidence": f.get("score"),
            "severity": SEVERITY.get(f["type"], "REVIEW"),
        }
        for f in findings[:MAX_SAMPLES_PER_RECORD]
    ]
    return {"findings": len(findings), "types": types, "samples": samples}


def scan_text(text: str, locale: Optional[str] = None) -> Dict[str, Any]:
    """Scan one text and return its metadata summary (the text is dropped)."""
    return summarize_findings(_detect(text, locale=locale))


def scan_items(items: Iterable[Dict[str, Any]], locale: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Scan connector-shaped items ({"id", "text", "collection"}).

    Returns record-key -> metadata summary, mirroring ragleakguard.monitor's
    snapshot shape. Document text is scanned and dropped.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for it in items:
        collection = it.get("collection") or ""
        key = f"{collection}:{it['id']}" if collection else str(it["id"])
        out[key] = scan_text(it.get("text") or "", locale=locale)
    return out


def _risk_level(by_type: Dict[str, int], n_flagged: int, n_records: int) -> str:
    # Mirrors ragleakguard.report's risk model (private there, restated here;
    # keep in lockstep when bumping the pinned ragleakguard version).
    has_high = any(SEVERITY.get(t) == "HIGH" for t in by_type)
    frac = (n_flagged / n_records) if n_records else 0.0
    if has_high and frac >= 0.25:
        return "HIGH"
    if has_high or frac >= 0.50:
        return "ELEVATED"
    return "MODERATE" if by_type else "LOW"


def build_result(
    source: str,
    path: str,
    records: Dict[str, Dict[str, Any]],
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate per-record summaries into the canonical tool result."""
    by_type: Dict[str, int] = {}
    for rec in records.values():
        for t, c in rec["types"].items():
            by_type[t] = by_type.get(t, 0) + c
    flagged = {k: r for k, r in records.items() if r["findings"] > 0}
    top = sorted(flagged.items(), key=lambda kv: (-kv[1]["findings"], kv[0]))[:MAX_FLAGGED_RECORDS]
    return {
        "event": "ragleakguard.agent.scan",
        "source": source,
        "path": path,
        "locale": locale,
        "totals": {
            "records": len(records),
            "records_with_findings": len(flagged),
            "findings": sum(by_type.values()),
        },
        "risk_level": _risk_level(by_type, len(flagged), len(records)),
        "by_type": {
            t: {"count": c, "severity": SEVERITY.get(t, "REVIEW")}
            for t, c in sorted(by_type.items(), key=lambda kv: (-kv[1], kv[0]))
        },
        "flagged_records": [
            {"record": k, "findings": r["findings"], "types": r["types"], "samples": r["samples"]}
            for k, r in top
        ],
        "flagged_records_truncated": len(flagged) > MAX_FLAGGED_RECORDS,
        "report_markdown": build_report(by_type, len(records), len(flagged), source=source, path=path),
    }


def to_json(result: Dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)
