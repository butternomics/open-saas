# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-25)

**Core value:** Butter joins more worthwhile conversations under its own posts, with replies that understand the post and sound like Butter, while Brandon spends less time and never loses control of what gets published.
**Current focus:** Phase 1: Foundation and Connectors

## Current Position

Phase: 1 of 5 (Foundation and Connectors)
Plan: 0 of 3 in current phase
Status: Ready to plan
Last activity: 2026-09-25 — Project initialized (PROJECT.md, research, REQUIREMENTS.md, ROADMAP.md)

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: - min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Standalone `butter-comment-assistant/` in the open-saas repo; Python 3.12, FastAPI + Jinja2 + vendored htmx, SQLModel + Alembic on SQLite, APScheduler 3.11, httpx + tenacity, official ollama client, keyring, pytest + respx.
- [Init]: Connector interface with MockConnector (labeled MOCK) and InstagramGraphConnector; LLM client interface with FakeLLMClient and OllamaClient. The whole suite runs offline; real integrations are respx-tested against recorded fixtures.
- [Init]: Publishing gated by a stored human-approved text hash; explicit state machines for comments, drafts and outbound tasks; limits enforced outside the model at triage and send.
- [Init]: Automation OFF by default, two categories only, per-comment eligibility, gated on the evaluation report's quality bar.
- [Init]: Live verification lives in the "Needs a human" runbook (Phase 5), never in phase success criteria. Project mode: mvp for all phases.

### Pending Todos

None yet.

### Blockers/Concerns

- No Instagram account, Meta app, Ollama, GPU or ffmpeg in the build container. All phases must be verifiable with MockConnector and FakeLLMClient. Runbook items: Meta app and scopes (App Review may be required for `instagram_business_manage_comments`), real read, one authorized send, hardware and model selection, ffmpeg/whisper.cpp/keyring checks, the 100-comment evaluation.
- Graph API version and rate-limit specifics must be re-verified at implementation time; keep the version configurable and backoff header-driven.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-09-25
Stopped at: Roadmap created; Phase 1 ready to plan
Resume file: None
