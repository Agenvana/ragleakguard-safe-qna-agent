"""Shared fixtures.

PLANTED holds the secret values seeded into fixture documents and store
chunks; no tool output may ever contain any of them. The fake detector
returns them as raw finding text exactly like the real detector would, so the
reduction layer is exercised against worst-case input without needing the
heavyweight NLP stack.
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from rlg_common import summary  # noqa: E402

# Values planted in fixtures. None may ever appear in a tool output.
PLANTED = {
    "EMAIL_ADDRESS": "belle.secret.leak@example.com",
    "PHONE_NUMBER": "+1 415 555 0142",
    "PERSON": "Janet Leakwood",
    "AU_TFN": "123 456 782",
}
# Ordinary document prose must not leak either (outputs carry no document text).
DOC_SENTENCE = "strictly-internal patient consultation notes body text"


def fake_detect(text, locale=None):
    """Deterministic detector: finds each planted secret present in the text
    and returns it as raw finding text, mirroring the real detector's shape."""
    findings = []
    for ftype, secret in PLANTED.items():
        start = text.find(secret)
        while start != -1:
            findings.append(
                {"type": ftype, "start": start, "end": start + len(secret), "score": 0.85, "text": secret}
            )
            start = text.find(secret, start + 1)
    return findings


def assert_metadata_only(payload: str):
    """The rule itself: no planted secret and no document prose in a payload."""
    for secret in PLANTED.values():
        assert secret not in payload, f"raw value leaked into tool output: {secret[:4]}…"
    assert DOC_SENTENCE not in payload, "document text leaked into tool output"


@pytest.fixture
def use_fake_detect(monkeypatch):
    monkeypatch.setattr(summary, "_detect_impl", fake_detect)
    return fake_detect


@pytest.fixture
def risky_doc(tmp_path):
    p = tmp_path / "patient_note.txt"
    p.write_text(
        f"{DOC_SENTENCE}\nPatient {PLANTED['PERSON']} can be reached at "
        f"{PLANTED['EMAIL_ADDRESS']} or {PLANTED['PHONE_NUMBER']}. TFN {PLANTED['AU_TFN']}.",
        encoding="utf-8",
    )
    return str(p)


@pytest.fixture
def clean_doc(tmp_path):
    p = tmp_path / "policy.md"
    p.write_text("Returns are accepted within 30 days with a valid receipt.", encoding="utf-8")
    return str(p)


@pytest.fixture
def fake_store_chunks():
    return [
        {"id": "notes.txt#chunk0", "text": f"{DOC_SENTENCE} {PLANTED['EMAIL_ADDRESS']}", "collection": "vs_test123"},
        {"id": "notes.txt#chunk1", "text": f"call {PLANTED['PHONE_NUMBER']} re {PLANTED['PERSON']}", "collection": "vs_test123"},
        {"id": "faq.md#chunk0", "text": "shipping takes 3-5 business days", "collection": "vs_test123"},
    ]
