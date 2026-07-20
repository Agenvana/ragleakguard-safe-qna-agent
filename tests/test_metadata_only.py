"""The metadata-only principle as executable law, for every agent tool.

Mirrors test_state_and_payload_never_contain_raw_values in the RAGLeakGuard
repo (tests/test_monitor.py): plant known secrets, run the real tool code end
to end, then assert the serialized output contains finding TYPES but none of
the planted values and no document text. Any change to a tool's output shape
must keep every test in this file passing.
"""
import json

import pytest

from conftest import PLANTED, assert_metadata_only

from rlg_common import openai_store, summary
from safe_rag_agent.tools.ScanDocument import ScanDocument
from safe_rag_agent.tools.SafeIngestDocument import SafeIngestDocument
from safe_rag_agent.tools.ScanKnowledgeBase import ScanKnowledgeBase


def test_scan_document_output_never_contains_raw_values(use_fake_detect, risky_doc):
    out = ScanDocument(path=risky_doc).run()
    assert_metadata_only(out)
    parsed = json.loads(out)
    assert parsed["verdict"] == "REVIEW_REQUIRED"
    assert parsed["types"]["EMAIL_ADDRESS"] == 1


def test_safe_ingest_refusal_never_contains_raw_values_and_never_uploads(
    use_fake_detect, monkeypatch, risky_doc
):
    def must_not_upload(*a, **k):
        raise AssertionError("upload attempted for a document that failed its scan")

    monkeypatch.setattr(openai_store, "get_or_create_vector_store", must_not_upload)
    monkeypatch.setattr(openai_store, "upload_file_to_vector_store", must_not_upload)
    out = SafeIngestDocument(path=risky_doc).run()
    assert_metadata_only(out)
    parsed = json.loads(out)
    assert parsed["status"] == "REFUSED"
    assert "AU_TFN" in parsed["types"]


def test_scan_knowledge_base_output_never_contains_raw_values(
    use_fake_detect, monkeypatch, fake_store_chunks
):
    monkeypatch.setattr(openai_store, "resolve_vector_store_id", lambda d, explicit=None: "vs_test123")
    monkeypatch.setattr(openai_store, "iter_vector_store_chunks", lambda vs_id: iter(fake_store_chunks))
    out = ScanKnowledgeBase().run()
    assert_metadata_only(out)
    assert "PERSON" in out
    parsed = json.loads(out)
    assert parsed["totals"]["records"] == 3
    assert parsed["totals"]["records_with_findings"] == 2
    assert "shipping takes" not in out  # clean chunk text must not leak either


def test_masked_samples_contain_zero_original_characters(use_fake_detect):
    rec = summary.scan_text(f"reach {PLANTED['PERSON']} at {PLANTED['EMAIL_ADDRESS']}")
    for sample in rec["samples"]:
        assert set(sample["masked"]) <= {summary.MASK_CHAR}
        assert sample["length"] > 0


def _real_detector_ready():
    try:
        from ragleakguard.detect import detect
        return bool(detect("Contact sam.reader@example.com today"))
    except Exception:
        return False


@pytest.mark.skipif(not _real_detector_ready(), reason="presidio/spaCy model not installed")
def test_real_detector_end_to_end_never_leaks_raw_values(tmp_path):
    """Belt and braces: the same guarantee with the REAL detection stack."""
    secret_email = "sam.reader@example.com"
    secret_phone = "+1 415 555 0142"
    p = tmp_path / "leads.txt"
    p.write_text(f"Lead: Sam Reader, {secret_email}, {secret_phone}, meeting 2026-07-21.", encoding="utf-8")

    out = ScanDocument(path=str(p)).run()
    assert secret_email not in out
    assert secret_phone not in out
    assert "EMAIL_ADDRESS" in out
    parsed = json.loads(out)
    assert parsed["verdict"] == "REVIEW_REQUIRED"
    assert parsed["findings"] >= 2
