# Walking Skeleton — Butter.ATL Comment Assistant

**Phase:** 1
**Generated:** 2026-09-25

## Capability Proven End-to-End

Brandon runs one command, opens `http://127.0.0.1:8765/`, is redirected to a status screen that shows a MOCK CONNECTOR badge, the mock account's auth state and documented scopes, and can change a setting on `/settings` that survives an app restart because it was written to `data/butter.db` by a migrated schema, while a request without a CSRF token is rejected.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI 0.141 + Jinja2 + vendored htmx 2.0.4, served by uvicorn on 127.0.0.1:8765 | Pydantic v2 everywhere; no node toolchain; local-only by construction (CONTEXT D-17, D-19) |
| Data layer | SQLite file `data/butter.db`, SQLModel tables, Alembic migrations run at startup and in every test | Same class defines table and schema; migrations from day one; tests never use `create_all` (D-06..D-11) |
| Auth | None (single local operator). Access control is the loopback bind guard plus CSRF double-submit cookie on every state-changing request | Threat model is "other devices on the network" and "malicious page in the same browser" (D-17, D-18) |
| Secrets | `SecretStore` protocol: OS keyring, else 0600 JSON file with a loud warning | Container has no keyring backend; deployment machine may (D-15) |
| Deployment target | Documented local run: `uv venv --python 3.12 .venv && uv pip install -e ".[dev]"` then `.venv/bin/butter-comment-assistant`; tests `.venv/bin/pytest` | No hosted environment; the app is a local tool (D-03) |
| Directory layout | `butter-comment-assistant/` with src layout `src/butter_comment_assistant/{storage,connectors,llm,web,templates,static}` and `migrations/`, `fixtures/`, `tests/` | Fixed module map so later phases know where things go (D-04, D-05) |
| External seams | `Connector` Protocol (MockConnector, InstagramGraphConnector) and `LLMClient` Protocol (FakeLLMClient, OllamaClient), both built by factories from process config | The whole app runs with no network; real implementations are respx-tested (D-22..D-28) |
| State machines | String enums plus transition dicts in `storage/enums.py`; `assert_transition` raises on illegal moves | Duplicate-send, stale-approval and expired-token checks become mechanical tests in Phases 3-4 (D-09, D-10) |

## Stack Touched in Phase 1

- [x] Project scaffold (pyproject, src layout, ruff, pytest with asyncio auto mode)
- [x] Routing: `GET /` redirect, `GET/POST /settings`, `GET /status`, `POST /status/check`, `/static`
- [x] Database: migrations create all ten tables; settings rows are read and written; an audit_log row is written on settings change
- [x] UI: settings form wired to the API with CSRF header via htmx; MOCK and AUTOMATION OFF badges on every page
- [x] Local full-stack run command documented in README; full suite offline

## Out of Scope (Deferred to Later Slices)

- Any scheduler job, polling, checkpoints (Phase 2)
- Briefs, media analysis, transcripts (Phase 2)
- Triage, prompts, voice rules, examples, knowledge (Phase 3)
- Inbox, approval hashes, sender, limits, audit UI, recap (Phases 3-4)
- Evaluation, acceptance suite, automation gating, runbook (Phase 5)
- Login, multi-user, remote access, webhooks, TikTok, cloud LLM (v2 or never)

## Subsequent Slice Plan

- Phase 2: monitored posts are collected from the connector into `posts`/`comments` on a schedule and each post gets a versioned brief.
- Phase 3: eligible comments get validated drafts that appear in a one-screen inbox with all six actions.
- Phase 4: approved text is published exactly once through the hash-gated sender with limits, audit log and recap.
- Phase 5: labels, reports, acceptance suite, gated automation and the "Needs a human" runbook.
