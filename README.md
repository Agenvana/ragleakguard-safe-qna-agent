# RAGLeakGuard Safe Q&A Agent — the RAG agent that checks what it remembers

<p>
  <a href="https://github.com/Agenvana/ragleakguard-safe-qna-agent/actions/workflows/tests.yml"><img src="https://github.com/Agenvana/ragleakguard-safe-qna-agent/actions/workflows/tests.yml/badge.svg" alt="tests" height="20"></a>
  <a href="https://github.com/Agenvana/ragleakguard-safe-qna-agent/releases"><img src="https://img.shields.io/github/v/release/Agenvana/ragleakguard-safe-qna-agent" alt="release" height="20"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="license" height="20"></a>
  <a href="https://github.com/Agenvana/RAGLeakGuard"><img src="https://img.shields.io/badge/powered%20by-RAGLeakGuard-0F172A" alt="powered by RAGLeakGuard" height="20"></a>
</p>

**A question-answering AI with a twist: it checks what it's about to
remember.** Give it your documents and it answers questions from them, like
any knowledge-base assistant, except **every document must pass a
sensitive-data scan before it can enter the knowledge base**, and you can ask
it to audit its own memory anytime. Powered by
**[RAGLeakGuard](https://github.com/Agenvana/RAGLeakGuard)**, the open-source
scanner for AI pipelines and vector stores.

> Build a customer-facing FAQ / knowledge agent in minutes without turning it
> into a PII leak. The scan gate is enforced in code, not in a prompt.

> ⭐ The engine behind this agent lives at
> **[github.com/Agenvana/RAGLeakGuard](https://github.com/Agenvana/RAGLeakGuard)**.
> Stars, issues and locale-pack requests all land there.
> Looking for the standalone auditor that scans files and existing vector
> stores? That's the sister repo:
> **[ragleakguard-agent](https://github.com/Agenvana/ragleakguard-agent)**.

## How it works

Under the hood it's a standard retrieval setup (an OpenAI vector store with
file search), the same mechanism most knowledge agents use. The difference
is the front door:

- `SafeIngestDocument(path, force?)` — scans first, ingests only if clean.
  Findings refuse ingestion unless the user explicitly accepts the risk.
- `ScanDocument(path)` — verdict without ingesting: `SAFE_TO_INGEST` or
  `REVIEW_REQUIRED`.
- `ScanKnowledgeBase()` — audit what the vector store already remembers
  (parsed chunks), on demand.

**Deliberately missing:** a bulk knowledge-file upload field in the onboarding
form. Platform file-drops that bypass the scan would defeat the point; every
document goes through `SafeIngestDocument`. (Internally the agent folder is
named `safe_rag_agent`; RAG is the mechanism, safe Q&A is the product.)

## The metadata-only principle

Scan results contain counts, finding types, severities, risk levels, file and
chunk ids, span lengths, confidence scores and fully-masked samples (zero
original characters). Raw detected values and document text are never
returned; a chat transcript is itself a data store. Enforced by
[`tests/test_metadata_only.py`](tests/test_metadata_only.py), mirroring
`test_state_and_payload_never_contain_raw_values` in the RAGLeakGuard repo.

Detection engine: Microsoft Presidio + RAGLeakGuard's custom recognisers and
post-processing. Global + US entities by default; `locale='au'` adds
Australian identifiers (TFN, ABN, ACN, Medicare, AU phones) with checksum
validation.

## Quick start (local, for developers)

Requires **Python 3.12** (agency-swarm needs ≥3.12; ragleakguard's detection
extra needs <3.13 for prebuilt wheels).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.template .env   # add your OPENAI_API_KEY

python agency.py        # terminal demo
python -m pytest tests/ -q
```

## Deploy on Agencii

1. Sign up at [agencii.ai](https://agencii.ai/signup?referral=a0d8a28b-56c3-47a4-9ebf-7faa8c2b0caf)
   (referral link) and install the
   [Agencii GitHub App](https://github.com/apps/agencii) with access to this repo.
2. Add `OPENAI_API_KEY` in the Agencii dashboard environment settings.
3. Push to `main`. The agency deploys as `safe-qna-agent` from `main.py`.

With your own OpenAI API key configured, Agencii does not deduct platform
credits for AI tokens. Running cost is your OpenAI token spend plus FileSearch
($2.50 per 1k calls) and file-search storage ($0.10/GB/day after 1 GB free).

**Knowledge persistence across redeploys:** the first `SafeIngestDocument`
call creates the vector store and reports its id. To keep the same knowledge
base across container redeploys, set that id as `RLG_VECTOR_STORE_ID` in the
platform environment settings; otherwise a fresh deploy starts a new store
(the old one still exists in your OpenAI account). File search over the store
attaches at boot, so retrieval begins on the first restart after the store
exists.

## Need more than a scan?

This agent diagnoses at the document level. For a formal, human-led
assessment of your AI data security (scoping, data-flow mapping, remediation
program, compliance mapping), start here:
**[the intake form](https://tally.so/r/obaG5V)**. The same goes for managed
deployment in your own cloud. Deploying for your own clients? Point the
contact at your own security team instead, or switch it off.

## Credits

Built by [Agenvana](https://github.com/Agenvana) on
**[RAGLeakGuard](https://github.com/Agenvana/RAGLeakGuard)** and
[Agency Swarm](https://github.com/VRSEN/agency-swarm) /
the [agency-starter-template](https://github.com/agency-ai-solutions/agency-starter-template).

License: [Apache-2.0](LICENSE). Detection is best-effort; absence of
findings is not proof of safety.
