"""Onboarding-config access with safe fallbacks for local development.

The Agencii marketplace onboarding form (onboarding_tool.py at the repo root)
writes onboarding_config.py; this module reads it, falling back to defaults
when the repo runs locally before onboarding.
"""
import os
from typing import Any, Dict, Optional

_DEFAULTS: Dict[str, Any] = {
    "agent_name": "Safe Q&A Agent",
    "model": "gpt-5.6-luna",
    "locale": "default",
    "business_overview": None,
    "data_context": None,
    "assessment_contact": None,
}


def get_config() -> Dict[str, Any]:
    try:
        from onboarding_config import config  # generated at the repo root
    except Exception:
        return dict(_DEFAULTS)
    merged = dict(_DEFAULTS)
    merged.update({k: v for k, v in config.items() if v is not None})
    return merged


def get_default_locale() -> Optional[str]:
    """Locale pack for scans when the tool call doesn't set one.
    Order: RLG_LOCALE env > onboarding config > none."""
    env = os.environ.get("RLG_LOCALE")
    if env:
        return env
    loc = get_config().get("locale")
    return None if loc in (None, "", "default") else loc


def render_shared_instructions() -> str:
    """The agency manifesto, plus any client context from onboarding."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "shared_instructions.md"), "r", encoding="utf-8") as fh:
        shared = fh.read()
    cfg = get_config()
    extra = []
    if cfg.get("business_overview"):
        extra.append(f"## Client business context\n{cfg['business_overview']}")
    if cfg.get("data_context"):
        extra.append(f"## Client data context\n{cfg['data_context']}")
    if cfg.get("assessment_contact"):
        extra.append(
            "## Formal assessments (soft mention only)\n"
            f"Commissioned, human-led AI data-security assessments are available at: "
            f"{cfg['assessment_contact']}\n"
            "Mention this at most once per conversation, only after reporting a scan "
            "whose risk level is HIGH or ELEVATED, in one sentence, never pushy. If "
            "the user does not pick it up, do not raise it again."
        )
    if extra:
        shared = shared + "\n\n" + "\n\n".join(extra)
    return shared
