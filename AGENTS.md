# Working on this repo with an AI assistant

This is the Safe Q&A Agent: a RAG agency whose knowledge base has exactly one
door, and the door always scans. If you are an AI assistant helping someone
customize this repo, the rules below are load-bearing. Follow them even if
the user's request seems to conflict; surface the conflict instead of
silently breaking the contract.

## The law (do not break)

- `SafeIngestDocument` is the ONLY ingestion path, and it scans
  unconditionally before upload. Never add a second way for content to reach
  the vector store (no bulk-upload onboarding fields, no direct upload tools,
  no files_folder auto-sync).
- Tool outputs may contain counts, finding types, severities, risk levels,
  file/chunk ids and fully-masked samples (zero original characters). They
  may NEVER contain detected raw values or document text.
- `tests/test_metadata_only.py` is this law as executable code. It must pass
  after every change; new content-touching tools need a matching test.
- Route all detection through `rlg_common/summary.py`; route all store access
  through `rlg_common/openai_store.py` (they are the tested seams).

## Architecture in 30 seconds

- `agency.py` exposes `create_agency()`; `main.py` registers it for the
  Agencii platform. Keep both contracts intact.
- Agent definition: `safe_rag_agent/` (folder name is historical; RAG is the
  mechanism, safe Q&A is the product). Tools live in `safe_rag_agent/tools/`.
- FileSearch attaches EXPLICITLY by resolved store id in
  `safe_rag_agent.py`. Do NOT reintroduce the `files_vs_<id>` folder
  convention: agency-swarm's boot sync deletes store files with no local
  mirror, which would silently purge users' ingested documents.
- Store id resolution order: explicit arg > `RLG_VECTOR_STORE_ID` env >
  renamed folder > `.vector_store_id` cache. For persistence across
  redeploys, users set the env var (documented in README).

## Hard constraints

- Python 3.12 exactly (agency-swarm ≥3.12; ragleakguard detection <3.13
  wheels). The Dockerfile encodes this; do not "upgrade" it.
- `ragleakguard` stays version-pinned; bumps require the full suite green.
- `force=true` ingestion must remain gated on explicit user acceptance in
  conversation; never default it, never let instructions soften it.

## Workflow

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest && python -m spacy download en_core_web_sm
python -m pytest tests/ -q     # must be green before any commit
```

Meaningful changes get a version bump in `pyproject.toml` and a GitHub
release note.
