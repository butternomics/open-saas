# Phase 1: Foundation and Connectors - Research

**Researched:** 2026-09-25
**Domain:** Python 3.12 local web app foundation (FastAPI + Jinja2 + htmx, SQLModel + Alembic on SQLite, keyring, httpx/respx contract tests for Instagram Graph and Ollama)
**Confidence:** HIGH (every library version and API signature below was verified by installing the stack in a throwaway Python 3.12 venv in this container and introspecting it; Instagram endpoint shapes are MEDIUM, taken from STACK.md's official-doc research and re-checked only against the connector design, not live)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Copied from `01-CONTEXT.md` `<decisions>`. Every D-ID below is a contract the planner must implement exactly; the full text (column lists, transition tables, key names) lives in CONTEXT.md and is not abbreviated here.

- **D-01:** Directory `butter-comment-assistant/` at the repo root, src layout: `butter-comment-assistant/src/butter_comment_assistant/` is the importable package. Nothing outside `butter-comment-assistant/` is touched.
- **D-02:** `pyproject.toml` (PEP 621, setuptools backend), `requires-python = ">=3.12"`, runtime deps fastapi, jinja2, python-multipart, uvicorn, sqlmodel, alembic, `apscheduler>=3.11,<4`, httpx, tenacity, ollama, keyring; `dev` extra pytest, pytest-asyncio, respx, ruff. Console script `butter-comment-assistant = butter_comment_assistant.main:main` plus `python -m butter_comment_assistant`. No node toolchain, no python-dotenv, no keyrings.alt.
- **D-03:** One install command (`uv venv --python 3.12 .venv && uv pip install -e ".[dev]"`, pip fallback documented), one run command (`.venv/bin/butter-comment-assistant`), test command `.venv/bin/pytest` from `butter-comment-assistant/`; suite passes with no network, Instagram, Ollama, GPU or ffmpeg.
- **D-04:** Fixed module map: `config.py`, `main.py`, `storage/{enums,models,db,settings_repo}.py`, `secrets.py`, `logging_setup.py`, `connectors/{base,mock,instagram_graph,factory}.py`, `llm/{base,fake,ollama_client,factory}.py`, `web/{__init__,csrf,routes_settings,routes_status}.py`, `templates/`, `static/`. Reserved (do not create in Phase 1): `collector/`, `briefs/`, `drafting/`, `review/`, `sending/`, `policy/`, `audit/`, `evaluation/`.
- **D-05:** `migrations/` + `alembic.ini` at `butter-comment-assistant/`; `fixtures/mock/` for MockConnector data; `tests/fixtures/` for respx recordings; runtime data in gitignored `data/`.
- **D-06:** Ten tables in the initial migration `0001_initial_schema`: posts, comments, drafts, outbound_tasks, examples, knowledge, voice_rules, settings, audit_log, eval_labels. Later phases only add via new revisions.
- **D-07:** PK conventions (platform IDs for posts/comments, UUID4 hex for drafts/outbound_tasks/examples/knowledge/eval_labels, integer version for voice_rules, key for settings, autoincrement for audit_log); naive UTC datetimes via `storage.enums.utcnow()`.
- **D-08:** Exact column sets for all ten tables (see CONTEXT.md D-08).
- **D-09:** `storage/enums.py` string enums (`CommentStatus`, `DraftStatus`, `OutboundStatus`, `ContextStatus`, `ErrorClass`, `ConnectorKind`, `LLMKind`, `ExampleKind`, `ExampleStatus`, `KnowledgeStatus`, `EvalLabel`, `AuditEvent`) plus `COMMENT_TRANSITIONS`, `DRAFT_TRANSITIONS`, `OUTBOUND_TRANSITIONS` and `assert_transition()` raising `IllegalTransition`.
- **D-10:** Exact transition tables (see CONTEXT.md D-10).
- **D-11:** `storage/db.py` with `make_engine`, `run_migrations` (programmatic `alembic.command.upgrade(cfg, "head")`), `session_scope`; migrations run in lifespan on every start; tests use real migrations on temp SQLite files and assert autogenerate finds zero diffs.
- **D-12:** Process config from `BCA_*` env vars in `config.py`; app settings as `AppSettings` pydantic model persisted per key in `settings` via `SettingsRepo.load/save`.
- **D-13:** `AppSettings` keys and defaults (daily_send_limit=20, per_post_send_limit=5, max_interaction_depth=2, poll_interval_floor_s=300, poll_interval_ceiling_s=21600, overlap_window_s=300, oldest_monitored_date=None, instagram_api_version="v25.0", ollama_host="http://127.0.0.1:11434", ollama_text_model="llama3.1:8b", ollama_vision_model="qwen2.5vl:7b", global_pause=False, automation_enabled=False); runtime state keys prefixed `state.` (`state.last_successful_sync_at`).
- **D-14:** `GET/POST /settings` form for every field, pydantic validation, `audit_log` row `settings_changed`, restart persistence test.
- **D-15:** `SecretStore` protocol; `KeyringSecretStore` (service `butter-comment-assistant`) and `FileSecretStore` (`{data_dir}/secrets.json`, mode 0600, refuse wider); `resolve_secret_store(config)` with loud WARNING on fallback; secret names `instagram_access_token`, `instagram_app_secret`.
- **D-16:** `logging_setup.RedactingFilter` on root and uvicorn loggers; redacts `access_token=`, `Authorization: Bearer`, `IGQ`/`IGAA`/`EAA` 40+ char tokens, any 60+ char `[A-Za-z0-9_-]` run; test proves no token reaches captured logs.
- **D-17:** `assert_loopback(host, allow_override)` in `main()` and in lifespan; `RefusedBindError` unless `BCA_ALLOW_NON_LOOPBACK=1`.
- **D-18:** CSRF middleware in `web/csrf.py`: cookie `bca_csrf` + header `X-CSRF-Token` or form `csrf_token`, `secrets.compare_digest`, 403 JSON `{"error": "csrf_token_missing_or_invalid"}`; `base.html` meta tag and `hx-headers`.
- **D-19:** `create_app(config=None)`, Jinja2Templates, `/static` mount, vendored htmx 2.0.4 at `static/htmx.min.js`, `base.html` header/nav/badge/footer, `GET /` redirects to `/status`.
- **D-20:** CSS variables in `static/app.css` (`--butter-yellow: #EFB82E` only yellow, Inter body, Space Mono utility, system display fallback), no emojis or em dashes, grep test.
- **D-21:** MOCK badge `data-testid="mock-badge"` with text `MOCK CONNECTOR` on every page under MockConnector; `AUTOMATION OFF` badge when automation disabled; test walks all GET routes.
- **D-22:** Connector DTOs (`PostDTO`, `CommentDTO`, `CommentPage`, `UsageInfo`, `ReplyResult`, `AuthStatus`) and error hierarchy (`ConnectorError` > `AuthError`, `RateLimitError`, `TransientError`, `PermanentError`, `UncertainSendError`).
- **D-23:** Async runtime-checkable `Connector` Protocol with `fetch_posts`, `fetch_comments`, `fetch_replies`, `post_reply`, `check_auth`, `refresh_credentials`, properties `kind`, `is_mock`, `display_name`; no delete/hide members and a source-scan test; `connectors/factory.py:build_connector` with lazy import.
- **D-24:** `MockConnector` from `fixtures/mock/dataset.json` (3 posts, 60+ comments over 3 pages of 25, own reply by account `17841400000000001`, injection comment, do-not-cover comment) driven by `MockScenario` behaviours (`ok`, `near_limit`, `rate_limit`, `auth_failure`, `timeout`, `permanent_error`), records `sent_replies`, `display_name = "MockConnector (MOCK)"`.
- **D-25:** `InstagramGraphConnector` on `https://graph.instagram.com/{api_version}` with the listed endpoints, cursor pagination, usage header parsing, error mapping (190/10/401/403 auth; 429/4/17/32/613 rate limit; 5xx GET transient with tenacity retry max 3; POST timeout uncertain, never retried), respx tests against `tests/fixtures/instagram/responses.json`.
- **D-26:** `LLMClient` Protocol: `generate_structured(request: LLMRequest, schema) -> LLMResult`, `health() -> LLMHealth`, `kind`; `LLMOutputInvalid`, `LLMUnavailable`; no tool parameters.
- **D-27:** Deterministic `FakeLLMClient` with a `responses` queue, `default_factory`, invalid-response scripting, `calls` recording.
- **D-28:** `OllamaClient` on `ollama.AsyncClient(host)`, `chat(..., format=schema.model_json_schema(), options=..., stream=False)`, loopback-only host, respx tests for success, invalid JSON, image bytes as base64, connection refused, `health()` via `/api/tags`.
- **D-29:** `GET /status` content list and CSRF-protected `POST /status/check`; distinct "AUTH PROBLEM" block.
- **D-30:** pytest `asyncio_mode = "auto"`, respx, TestClient, temp SQLite via migrations, FileSecretStore, Mock/Fake defaults in `conftest.py`, suite under 60 s offline, `ruff check src tests` clean at line length 100.

### Claude's Discretion
- Exact CSS beyond the tokens, status label wording, mock dataset text (no emojis, no em dashes, no invented facts about real people), `MockScenario` internals, autogenerated-then-checked vs hand-written initial revision, pydantic `BaseModel` vs non-table `SQLModel` for DTOs.

### Deferred Ideas (OUT OF SCOPE)
- Collector jobs and APScheduler wiring (Phase 2), post briefs and media (Phase 2), triage/drafting/voice/examples/knowledge (Phase 3), inbox/approval/sender/limits/audit UI/recap (Phases 3-4), evaluation/acceptance suite/automation/runbook (Phase 5), webhooks/TikTok/cloud LLM (v2).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | Install and start with one documented command each; full suite passes offline | Environment audit (uv + Python 3.12 present, PyPI reachable); pyproject pattern; pytest config; htmx vendoring verified downloadable |
| FOUND-02 | All tables in one SQLite file with versioned migrations that run on start | SQLModel + Alembic programmatic upgrade pattern; JSON column verified; zero-diff autogenerate test pattern |
| FOUND-03 | Settings editable in the UI without code changes, survive restart | `AppSettings` + `settings` key/value_json rows; Jinja form + CSRF; TestClient restart test |
| FOUND-04 | Credentials in OS store or 0600 file, never in logs/prompts/responses/exports, log scan test | keyring 25.7 backend behaviour (fail.Keyring in container), `os.open(..., 0o600)` file store, `logging.Filter` redaction pattern |
| FOUND-05 | Bind 127.0.0.1 by default, refuse non-loopback without override | `ipaddress.ip_address(...).is_loopback` guard before `uvicorn.run(host=...)` |
| FOUND-06 | CSRF token on every state-changing request | Starlette `BaseHTTPMiddleware` double-submit cookie pattern; htmx `hx-headers` |
| CONN-01 | Single Connector interface; whole app runs on MockConnector | `typing.Protocol` + `runtime_checkable`; factory with lazy import |
| CONN-02 | MOCK badge on every screen; mock simulates pagination, near-limit headers, 429, auth failure, timeouts, permanent errors | Fixture dataset + scenario queue design; template global from `app.state.connector.is_mock` |
| CONN-03 | InstagramGraphConnector (Instagram Login scopes, configurable version, token refresh, usage headers, error classes) respx-tested; no delete endpoint | httpx AsyncClient + respx verified; Graph endpoint shapes from STACK.md; tenacity retry pattern; source-scan test |
| CONN-04 | LLM client interface, FakeLLMClient, OllamaClient with schema-constrained output and image input, local-only, respx-tested | `ollama.AsyncClient.chat` signature verified (`format: dict`, `images` on message); respx can mock the `/api/chat` HTTP call the client makes |
| CONN-05 | Connection status screen: connector type, auth state, documented scopes, last successful sync | `/status` route reading connector `check_auth()`, `AppSettings`, `state.last_successful_sync_at` |
</phase_requirements>

## Summary

Phase 1 is a greenfield Python package with no existing code to conform to. Every library in the locked stack was installed into a scratch Python 3.12 venv inside this container and imported successfully, so the planner can treat the versions and signatures in this document as verified rather than remembered: fastapi 0.141.1 on starlette 1.7.0, sqlmodel 0.0.47 (which pins SQLAlchemy 2.0.54, not 2.1), alembic 1.20.0, apscheduler 3.11.3, httpx 0.28.1, respx 0.23.1, ollama 0.6.2, pydantic 2.13.5, keyring 25.7.0, pytest 9.1.1, pytest-asyncio 1.4.0, uvicorn 0.54.0, jinja2 3.1.6.

Three environmental facts shape the plans. First, the container's keyring backend is `keyring.backends.fail.Keyring`, so the 0600 file store is not an edge case but the path every test exercises, and `resolve_secret_store` must detect the fail backend explicitly (calling `keyring.get_password` on it raises `NoKeyringError`). Second, Starlette 1.7 marks `TestClient` on httpx 0.28 as deprecated in favour of `httpx2`; it still works, and the suite must simply tolerate the `StarletteDeprecationWarning` (do not add `httpx2`, it would break respx). Third, `uv` and `/usr/bin/python3.12` exist here, PyPI and jsdelivr are reachable through the proxy, so `uv venv --python 3.12` and the one-time htmx download are safe executor steps.

The riskiest part of the phase is not any library but the contracts: ten tables, three transition tables, two protocols and a settings model that four later phases import. The plans should therefore write contracts first (models, enums, `base.py` files), test them with deterministic implementations (MockConnector, FakeLLMClient) and only then wire real implementations behind respx. Migrations must be exercised by the tests, not bypassed with `create_all`, so that the zero-diff check catches a model edit that forgot its revision.

**Primary recommendation:** Build storage and enums first as one plan, fan out app shell, secrets, connector seam and LLM seam in parallel, then wire the Instagram connector and the status screen on top. Use real Alembic migrations in tests, respx for every HTTP call, and never let a test touch the network.

## Architectural Responsibility Map

Single-process application; "tiers" are internal layers of one Python process plus the browser.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Loopback bind guard | Process entry (`main.py`) | App lifespan | Must run before a socket opens; lifespan check covers hand-started ASGI servers |
| CSRF enforcement | API / Backend (Starlette middleware) | Browser (htmx `hx-headers`) | Server decides; browser only carries the token |
| Settings persistence and validation | Database / Storage (`settings` table) + Backend (pydantic) | Browser form | Values must survive restart; validation is server-side |
| Secret storage | OS credential store or 0600 file (Backend adapter) | none | Never the database, never templates or logs |
| Log redaction | Backend logging layer | none | Filter installed once on root logger |
| Connector I/O | Backend (`connectors/`) | External (Instagram Graph API) | Only place that knows platform specifics |
| LLM calls | Backend (`llm/`) | External (Ollama daemon on loopback) | Only place that talks to a model |
| MOCK badge and status rendering | Backend (Jinja templates) | Browser | Server-rendered from `app.state.connector` |
| Schema and migrations | Database / Storage | none | Alembic runs at startup from the app process |

## Standard Stack

### Core

| Library | Version (verified) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| fastapi | 0.141.1 | App factory, routing, Jinja2Templates, TestClient | Locked in PROJECT.md; Pydantic v2 native [VERIFIED: installed and imported] |
| starlette | 1.7.0 (transitive) | Middleware base, static files, templating | Pulled by fastapi; `Jinja2Templates.TemplateResponse(request, name, context)` signature confirmed [VERIFIED: introspected] |
| jinja2 | 3.1.6 | HTML templates | [VERIFIED: PyPI] |
| python-multipart | 0.0.32 | Form parsing for `POST /settings` | Required by FastAPI for form bodies [VERIFIED: PyPI] |
| uvicorn | 0.54.0 | ASGI server; `uvicorn.run(app, host=, port=)` defaults host to 127.0.0.1 | [VERIFIED: introspected signature] |
| sqlmodel | 0.0.47 | Table models + pydantic validation | Locked; pins SQLAlchemy 2.0.54 [VERIFIED: installed] |
| sqlalchemy | 2.0.54 (transitive) | Engine, JSON column type | Do not pin 2.1 (PyPI latest 2.1.0 is not what sqlmodel resolves) [VERIFIED: installed] |
| alembic | 1.20.0 | Migrations; `alembic.command.upgrade(config, "head")` | [VERIFIED: introspected] |
| apscheduler | 3.11.3 | Declared now, no jobs until Phase 2 | Locked 3.x, never 4.0 alpha [VERIFIED: installed] |
| httpx | 0.28.1 | Instagram client; respx target | [VERIFIED: installed] |
| tenacity | 9.1.4 | GET retry with jittered backoff | [VERIFIED: PyPI] |
| ollama | 0.6.2 | `AsyncClient.chat(model, messages, format=dict, options=, stream=False)`; message supports `images` | [VERIFIED: introspected signature] |
| pydantic | 2.13.5 | DTOs, AppSettings, LLM schemas | [VERIFIED: installed] |
| keyring | 25.7.0 | OS credential store; `keyring.get_keyring()` returns `keyring.backends.fail.Keyring` here | [VERIFIED: introspected] |

### Supporting (dev)

| Library | Version (verified) | Purpose | When to Use |
|---------|--------------------|---------|-------------|
| pytest | 9.1.1 | Runner | Always |
| pytest-asyncio | 1.4.0 | `asyncio_mode = "auto"` for async tests | Async connector and LLM tests |
| respx | 0.23.1 | Mock httpx routes; works with `AsyncClient` and with `ollama.AsyncClient` (which uses httpx) | Every test that would hit the network |
| ruff | 0.16.9 | Lint | `ruff check src tests` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| own `FileSecretStore` | keyrings.alt encrypted file | Extra dependency and passphrase; CONTEXT D-02/D-15 lock the own store |
| Starlette middleware CSRF | `starlette-csrf` package | Extra dependency for 40 lines; not in locked stack |
| `uvicorn` plain | `uvicorn[standard]` | uvloop/httptools not needed for a single-user local app |

**Installation (executor runs from `butter-comment-assistant/`):**
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
# pip fallback
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

## Package Legitimacy Audit

slopcheck 1.x ran in this container (`slopcheck install <all packages>`) and installed every package, which it only does for packages it rates clean; none were blocked as `[SLOP]` or `[SUS]`. Registry facts below come from the PyPI JSON API fetched this session.

| Package | Registry | First release | Source Repo | slopcheck | Disposition |
|---------|----------|---------------|-------------|-----------|-------------|
| fastapi | PyPI | 2018-12 | github.com/fastapi/fastapi | OK | Approved |
| sqlmodel | PyPI | 2021-08 | github.com/fastapi/sqlmodel | OK | Approved |
| alembic | PyPI | 2011-11 | github.com/sqlalchemy/alembic | OK | Approved |
| apscheduler | PyPI | 2009-08 | github.com/agronholm/apscheduler | OK | Approved (pin `>=3.11,<4`) |
| httpx | PyPI | 2019-07 | github.com/encode/httpx | OK | Approved |
| tenacity | PyPI | 2016-08 | github.com/jd/tenacity | OK | Approved |
| ollama | PyPI | 2024-01 | github.com/ollama/ollama-python | OK | Approved (official client) |
| pydantic | PyPI | 2017-05 | github.com/pydantic/pydantic | OK | Approved |
| keyring | PyPI | 2009-08 | github.com/jaraco/keyring | OK | Approved |
| jinja2 | PyPI | 2008-06 | github.com/pallets/jinja | OK | Approved |
| python-multipart | PyPI | 2013-03 | github.com/Kludex/python-multipart | OK | Approved |
| uvicorn | PyPI | 2017-06 | github.com/encode/uvicorn | OK | Approved |
| pytest | PyPI | 2010-11 | github.com/pytest-dev/pytest | OK | Approved |
| pytest-asyncio | PyPI | 2015-04 | github.com/pytest-dev/pytest-asyncio | OK | Approved |
| respx | PyPI | 2019-11 | github.com/lundberg/respx | OK | Approved |
| ruff | PyPI | 2022-08 | github.com/astral-sh/ruff | OK | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none. No `checkpoint:human-verify` install gates are required.

## Architecture Patterns

### System Architecture Diagram

```
 Browser (127.0.0.1 only)
   |  GET /status, GET/POST /settings (+ X-CSRF-Token from hx-headers / hidden field)
   v
 uvicorn (host asserted loopback by main() and lifespan)
   v
 FastAPI app  --CSRFMiddleware (403 on missing/mismatched token)--> routers (web/)
   |                                                                  |
   |  lifespan: run_migrations(db) -> load AppSettings -> build connector + llm client
   |                                                                  |
   v                                                                  v
 storage/ (SQLModel + Alembic on data/butter.db)         app.state.connector : Connector
                                                          |-- MockConnector <- fixtures/mock/dataset.json + MockScenario
                                                          |-- InstagramGraphConnector <- httpx -> graph.instagram.com (respx in tests)
                                                          app.state.llm : LLMClient
                                                          |-- FakeLLMClient (scripted queue)
                                                          |-- OllamaClient <- ollama.AsyncClient -> 127.0.0.1:11434 (respx in tests)
                                                          secrets: SecretStore (keyring | data/secrets.json 0600)
                                                          logging: RedactingFilter on root + uvicorn loggers
```

### Recommended Project Structure (matches CONTEXT D-01, D-04, D-05)

```
butter-comment-assistant/
├── pyproject.toml
├── alembic.ini
├── .gitignore
├── README.md                          # install, run, test, env vars (plan 01-07)
├── migrations/
│   ├── env.py                         # target_metadata = SQLModel.metadata
│   ├── script.py.mako
│   └── versions/0001_initial_schema.py
├── fixtures/mock/dataset.json         # MockConnector data
├── src/butter_comment_assistant/
│   ├── __init__.py  __main__.py  main.py  config.py  secrets.py  logging_setup.py
│   ├── storage/   enums.py  models.py  db.py  settings_repo.py
│   ├── connectors/ base.py  mock.py  instagram_graph.py  factory.py
│   ├── llm/        base.py  fake.py  ollama_client.py  factory.py
│   ├── web/        __init__.py  csrf.py  routes_settings.py  routes_status.py
│   ├── templates/  base.html  settings.html  status.html
│   └── static/     app.css  htmx.min.js
└── tests/
    ├── conftest.py
    ├── fixtures/instagram/responses.json
    └── test_*.py
```

### Pattern 1: SQLModel table with JSON list column (verified round trip)
**What:** JSON columns for tag lists and structured blobs; SQLite stores them as TEXT.
```python
# Source: verified in scratch venv this session (sqlmodel 0.0.47, sqlalchemy 2.0.54)
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field

class Example(SQLModel, table=True):
    __tablename__ = "examples"
    id: str = Field(primary_key=True)
    tags_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
```
Enums are stored as their string values: declare the field as the `str, Enum` subclass and SQLModel maps it to a VARCHAR; add `sa_column=Column(String(32))` if Alembic autogenerate produces an `Enum` type you do not want (SQLite has no native enum; a plain String column keeps migrations simple).

### Pattern 2: Alembic programmatic upgrade with packaged config
```python
# Source: alembic 1.20 API, verified signature command.upgrade(config, revision)
from pathlib import Path
from alembic import command
from alembic.config import Config

PKG_ROOT = Path(__file__).resolve().parents[3]  # butter-comment-assistant/

def run_migrations(database_url: str) -> None:
    cfg = Config(str(PKG_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PKG_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
```
`migrations/env.py` must `from butter_comment_assistant.storage import models  # noqa: F401` before setting `target_metadata = SQLModel.metadata`, and use `render_as_batch=True` in `context.configure` so future ALTERs work on SQLite. Zero-diff test: `from alembic.autogenerate import compare_metadata; from alembic.migration import MigrationContext; assert compare_metadata(MigrationContext.configure(conn), SQLModel.metadata) == []`.

### Pattern 3: Runtime-checkable async Protocol seam
```python
# Source: Python 3.12 typing docs (Protocol, runtime_checkable)
from typing import Protocol, runtime_checkable

@runtime_checkable
class Connector(Protocol):
    @property
    def kind(self) -> ConnectorKind: ...
    @property
    def is_mock(self) -> bool: ...
    async def fetch_comments(self, post_id: str, cursor: str | None = None) -> CommentPage: ...
```
`isinstance(MockConnector(...), Connector)` checks member presence only; tests should additionally assert the exact member set with `Connector.__protocol_attrs__` (3.12) or a hand-written list so a stray `delete_comment` fails the test.

### Pattern 4: respx contract test for an httpx AsyncClient (verified)
```python
# Source: verified in scratch venv (respx 0.23.1, httpx 0.28.1)
@respx.mock
async def test_usage_header_parsed():
    respx.get("https://graph.instagram.com/v25.0/123/comments").mock(
        return_value=httpx.Response(200, json=FIXTURES["comments_page1"],
                                    headers={"x-app-usage": '{"call_count": 90, "total_time": 10, "total_cputime": 5}'}))
    page = await connector.fetch_comments("123")
    assert page.usage.near_limit is True and page.next_cursor == "QVFI..."
```
`ollama.AsyncClient` is httpx underneath, so `respx.post("http://127.0.0.1:11434/api/chat")` mocks it; the response JSON shape is `{"model": ..., "message": {"role": "assistant", "content": "<json string>"}, "done": true}`.

### Pattern 5: Starlette double-submit CSRF middleware
```python
# Source: Starlette BaseHTTPMiddleware docs; pattern is standard
class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        cookie = request.cookies.get("bca_csrf")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            sent = request.headers.get("x-csrf-token") or await _form_token(request)
            if not (cookie and sent and secrets.compare_digest(cookie, sent)):
                return JSONResponse({"error": "csrf_token_missing_or_invalid"}, status_code=403)
        response = await call_next(request)
        if not cookie:
            response.set_cookie("bca_csrf", secrets.token_hex(32), httponly=True, samesite="strict", path="/")
        return response
```
Reading the form body in middleware consumes the stream; the simplest safe approach is to read `await request.form()` once and rely on Starlette caching `request._form` so the route can read it again (Starlette caches parsed forms on the Request object). Alternatively require the header only and have `settings.html` submit via htmx (`hx-post`) so the header is always present; keep the hidden field for no-JS fallback and document that the middleware checks header first, then form.

### Pattern 6: Loopback guard
```python
import ipaddress
def assert_loopback(host: str, allow_override: bool) -> None:
    if host == "localhost": return
    if ipaddress.ip_address(host).is_loopback: return
    if allow_override: log.warning("Binding to non-loopback host %s because BCA_ALLOW_NON_LOOPBACK=1", host); return
    raise RefusedBindError(host)
```

### Pattern 7: Redacting log filter
```python
TOKEN_RE = re.compile(r"(access_token=)[^&\s]+|(Bearer\s+)[A-Za-z0-9._-]+|\b(?:IGQ|IGAA|EAA)[A-Za-z0-9_-]{40,}|\b[A-Za-z0-9_-]{60,}\b")
class RedactingFilter(logging.Filter):
    def filter(self, record):
        record.msg = TOKEN_RE.sub(lambda m: (m.group(1) or m.group(2) or "") + "[REDACTED]", str(record.msg))
        if record.args: record.args = tuple(TOKEN_RE.sub("[REDACTED]", str(a)) for a in record.args)
        return True
```
Attach to `logging.getLogger()` and to `uvicorn`, `uvicorn.access`, `uvicorn.error`, `httpx`, `httpcore` loggers. httpx logs request URLs at DEBUG including query strings, which is why `access_token=` is scrubbed at the filter, not by hoping DEBUG is off.

### Pattern 8: Ollama structured output with image input
```python
# Source: ollama-python 0.6.2 AsyncClient.chat signature (verified); Ollama structured outputs docs
resp = await client.chat(
    model=model,
    messages=[{"role": "system", "content": req.system},
              {"role": "user", "content": req.user, "images": [base64.b64encode(b).decode() for b in req.images]}],
    format=schema.model_json_schema(),
    options={"temperature": req.temperature, "num_predict": req.max_tokens},
    stream=False)
parsed = schema.model_validate_json(resp.message.content)  # raises ValidationError -> LLMOutputInvalid
```
The Python client accepts raw bytes in `images` too, but sending base64 strings makes the respx assertion on the request body deterministic.

### Anti-Patterns to Avoid
- **`SQLModel.metadata.create_all` in tests or startup:** bypasses migrations; a model change without a revision goes unnoticed until the real deployment. Use `run_migrations` everywhere.
- **Storing the token on the connector instance and logging `self.__dict__`:** read from `SecretStore` per call; the `repr` of the connector must not include the token.
- **Retrying `POST /{comment}/replies` on timeout:** creates duplicate public replies; raise `UncertainSendError` and let Phase 4 reconcile.
- **Badge derived from an env var string in the template:** derive from `app.state.connector.is_mock` so a misconfigured factory cannot show REAL while the mock runs.
- **`httpx2`:** Starlette's deprecation note suggests it, but respx targets httpx 0.28; keep httpx.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema versioning | ad hoc `ALTER TABLE` scripts | Alembic revisions with `render_as_batch=True` | SQLite ALTER limitations; zero-diff test needs Alembic's compare |
| HTTP mocking | monkeypatched `httpx.AsyncClient` | respx | Route matching, request recording, works with ollama client |
| Retry/backoff | manual sleep loops | tenacity `retry_if_exception_type(TransientError)`, `wait_random_exponential`, `stop_after_attempt(3)` | Jitter and stop conditions are easy to get wrong |
| Constant-time compare | `==` on tokens | `secrets.compare_digest` | Timing side channel |
| Loopback detection | string compare on `127.` | `ipaddress.ip_address().is_loopback` | Handles `::1`, `127.0.0.2` |
| OS credential storage | custom keychain calls | keyring | Cross-platform backends |

**Key insight:** the phase is contract-heavy; every custom mechanism (state machine tables, secret store, CSRF) is small, but the libraries above remove the parts that are easy to get subtly wrong.

## Common Pitfalls

### Pitfall 1: keyring fail backend looks like "no password" instead of "no keyring"
**What goes wrong:** `keyring.get_password` on `fail.Keyring` raises `keyring.errors.NoKeyringError`; code that catches only `KeyringError` still works (NoKeyringError subclasses it) but code that expects `None` crashes at startup.
**How to avoid:** In `resolve_secret_store` check `type(keyring.get_keyring()).__module__.endswith("fail")` or attempt a `get_password("butter-comment-assistant", "probe")` inside `try/except KeyringError`, then fall back to `FileSecretStore` with a WARNING. Tests set `BCA_SECRET_STORE=file`.

### Pitfall 2: Reading the request body twice in CSRF middleware
**What goes wrong:** Middleware consumes the form stream; the route then gets an empty form.
**How to avoid:** Check header first; only call `await request.form()` when no header is present (Starlette caches the parsed form on the request so the route can call `request.form()` again). Test both header-only and form-only submissions.

### Pitfall 3: Alembic env.py not importing models
**What goes wrong:** `target_metadata` is empty, autogenerate produces a migration that drops every table, the zero-diff test fails.
**How to avoid:** `env.py` imports `butter_comment_assistant.storage.models` explicitly; the src layout requires the package to be installed (`-e .`) or `prepend_sys_path = src` in `alembic.ini`.

### Pitfall 4: Enum columns rendered as SQLAlchemy `Enum` with CHECK constraints
**What goes wrong:** Adding an enum member later requires a constraint migration on SQLite.
**How to avoid:** Store enums as `String(32)` columns (`sa_column=Column(String(32), nullable=False, index=True)`) and validate in Python through the `str, Enum` types.

### Pitfall 5: Windows-safe temp SQLite in tests
**What goes wrong:** SQLite file locked when engine not disposed.
**How to avoid:** Fixture yields the engine and calls `engine.dispose()` on teardown; use `sqlite:///{tmp_path}/butter.db` with `connect_args={"check_same_thread": False}` because TestClient runs the app in a thread.

### Pitfall 6: pytest-asyncio 1.x strict mode by default
**What goes wrong:** async tests are skipped or error without a marker.
**How to avoid:** `[tool.pytest.ini_options] asyncio_mode = "auto"` in pyproject.

### Pitfall 7: Vendored htmx missing in CI
**What goes wrong:** Templates reference `/static/htmx.min.js` but the file was never committed.
**How to avoid:** Download once with `curl -sSfL https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js -o src/butter_comment_assistant/static/htmx.min.js` (verified 200, ~50 KB) and commit it; a test asserts the file exists and starts with `var htmx=`.

## Code Examples

See Patterns 1 to 8 above; each was either executed in the scratch venv (Patterns 1, 4) or derived from an introspected signature (Patterns 2, 8) or from standard library / Starlette documentation (Patterns 3, 5, 6, 7).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `templates.TemplateResponse(name, {"request": request})` | `TemplateResponse(request, name, context)` | Starlette 0.29+ | Use the request-first form everywhere |
| `instagram_manage_comments` scope | `instagram_business_manage_comments` | Jan 2025 | Only the `instagram_business_*` family is documented in scopes |
| pytest-asyncio 0.2x `asyncio_mode=auto` config key | same key, 1.x defaults strict | 2025 | Set explicitly |
| Prompt "return JSON" | `format=<json schema>` | Ollama 0.3+ / client 0.4+ | Schema-constrained decoding |

**Deprecated/outdated:** APScheduler 4.0 alpha (do not use); Starlette `TestClient` on httpx is deprecated but functional (tolerate the warning; do not migrate this phase).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Instagram Graph comment endpoints return `paging.cursors.after` and `paging.next`, and usage headers are `x-app-usage` / `x-business-use-case-usage` JSON [ASSUMED from STACK.md/PITFALLS.md official-doc research, not fetched live] | Pattern 4, D-25 | Real connector would need a fixture update; design (cursor string opaque, headers parsed leniently) tolerates shape changes |
| A2 | Graph error codes 190/10 (auth) and 4/17/32/613 (rate limit) [ASSUMED: Meta docs from training and STACK.md] | D-25 | Misclassified error class; mapping is a single table in `instagram_graph.py`, and HTTP status is used as the primary signal |
| A3 | Ollama daemon cloud features are disabled at the daemon, not through the Python client [ASSUMED] | D-28 | Client-side loopback-only host check remains the enforceable control; runbook item for the daemon |
| A4 | Reading `request.form()` in middleware then again in the route works because Starlette caches `_form` [ASSUMED from Starlette source knowledge] | Pattern 5 | Fallback: header-only CSRF with htmx, documented; test will catch it immediately |

## Open Questions (RESOLVED)

1. **Hand-write or autogenerate `0001_initial_schema.py`?** RESOLVED: executor may run `alembic revision --autogenerate -m initial_schema` after models exist, then must review, rename to `0001_initial_schema.py` with `revision = "0001"`, and commit it; the zero-diff test is the acceptance check either way.
2. **Where does the MOCK badge get its truth before the connector plan lands?** RESOLVED: plan 01-02 renders the badge from `request.app.state.connector.is_mock` when a connector is attached and from `config.connector == "mock"` otherwise; plan 01-07 attaches the real instance. Both paths show the badge under mock.
3. **Does respx intercept the ollama client?** RESOLVED: yes, `ollama.AsyncClient` is an httpx AsyncClient wrapper; mock `POST {host}/api/chat` and `GET {host}/api/tags`.
4. **Python 3.11 system interpreter vs locked 3.12?** RESOLVED: `uv venv --python 3.12` uses the container's 3.12; `requires-python = ">=3.12"` stays as locked.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | package | yes | /usr/bin/python3.12, uv-managed | none needed |
| uv | install command | yes | /root/.local/bin/uv | `python3.12 -m venv` + pip |
| PyPI via proxy | install | yes | verified `uv pip install` of full stack | none needed |
| jsdelivr CDN | htmx vendoring (one-time) | yes | HTTP 200, 50917 bytes | unpkg also 200 |
| keyring OS backend | KeyringSecretStore | no (fail.Keyring) | keyring 25.7.0 | FileSecretStore 0600 (D-15) |
| Ollama daemon | OllamaClient live | no | none | respx fixtures; FakeLLMClient |
| Instagram account / Meta app | InstagramGraphConnector live | no | none | respx fixtures; MockConnector |
| ffmpeg | not needed in Phase 1 | no | none | not applicable |
| SQLite | storage | yes | 3.45.1 (stdlib sqlite3) | none needed |

**Missing dependencies with no fallback:** none for Phase 1.
**Missing dependencies with fallback:** keyring backend (file store), Ollama (fake + respx), Instagram (mock + respx).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (single local user) | Loopback bind is the access control; documented override only |
| V3 Session Management | partial | CSRF cookie `HttpOnly; SameSite=Strict`; no login session |
| V4 Access Control | yes | `assert_loopback`; CSRF on every state change |
| V5 Input Validation | yes | pydantic `AppSettings`, DTOs, LLM schema validation |
| V6 Cryptography | minimal | `secrets.token_hex`, `secrets.compare_digest`; no custom crypto |
| V8 Data Protection | yes | SecretStore (keyring / 0600 file), RedactingFilter, no secrets in templates or JSON |
| V14 Configuration | yes | env-only process config, defaults safe (127.0.0.1, mock, fake) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Localhost CSRF from a malicious page in the same browser | Spoofing/Tampering | Double-submit cookie + header, SameSite=Strict |
| App bound to 0.0.0.0 on shared wifi | Elevation of privilege | `assert_loopback` refusal with explicit override |
| Token leakage into logs / templates | Information disclosure | RedactingFilter; SecretStore never passed to templates; status shows presence only |
| Secrets file readable by other users | Information disclosure | `os.open(path, O_WRONLY|O_CREAT, 0o600)`, refuse to load if mode wider than 0600 |
| Prompt injection via comment text reaching tools | Tampering | LLM protocol has no tool parameters; images/strings only |
| Duplicate public reply after POST timeout | Repudiation/Tampering | `UncertainSendError`, never retry POST |
| Supply chain (pip) | Tampering | slopcheck audit above; all packages long-lived with source repos |
| Mock mistaken for real | Repudiation | `data-testid="mock-badge"` on every page, `display_name` includes MOCK |

## Project Constraints (from CLAUDE.md)

- Python 3.12, FastAPI + Jinja2 + vendored htmx, SQLite via SQLModel with Alembic, APScheduler 3.x, httpx, official ollama client; no node toolchain, no vector DB, no training.
- Standalone `butter-comment-assistant/` directory; the Wasp template must not be modified.
- No Instagram account, Meta app, Ollama or GPU in the container; everything testable with MockConnector and FakeLLMClient; real connectors respx-tested; live steps documented, not asserted.
- Bind 127.0.0.1 by default and refuse non-loopback without explicit override; CSRF on state-changing requests; credentials in the OS credential store or a 0600 file, never in logs, prompts, browser responses or exports; Ollama cloud features disabled.
- The model never authorizes publishing; only the sender (Phase 4) operating on a stored approved-text hash can call the reply endpoint; no delete endpoint at all.
- Instagram API with Instagram Login (`instagram_business_basic`, `instagram_business_manage_comments`), configurable API version, polling not webhooks.
- Butter canon for UI copy: no emojis, no em dashes, Butter yellow #EFB82E only, Inter body, Space Mono utility.

## Sources

### Primary (HIGH confidence)
- Scratch venv in this container (Python 3.12): `uv pip install` of the full stack, `inspect.signature` on `ollama.AsyncClient.chat`, `Jinja2Templates.TemplateResponse`, `alembic.command.upgrade`, `uvicorn.run`; executed TestClient, respx + AsyncClient, SQLModel JSON round trip.
- PyPI JSON API (`pypi.org/pypi/<pkg>/json`) for versions, first-release dates and source repos; `pip index versions` for latest versions.
- slopcheck run over all 16 packages.
- `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md` (project research, already sourced to Meta and Ollama docs).

### Secondary (MEDIUM confidence)
- Instagram Graph API endpoint and header shapes as described in STACK.md §"Instagram Graph API Specifics" and PITFALLS.md (official domains cited there; not re-fetched this session).

### Tertiary (LOW confidence)
- Graph API numeric error codes (A2).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (installed and imported)
- Architecture: HIGH (contracts locked in CONTEXT.md; patterns executed)
- Pitfalls: HIGH for local stack, MEDIUM for Instagram specifics
- Code examples: HIGH (executed or introspected) except Pattern 5 body-caching detail (A4)

**Research date:** 2026-09-25
**Valid until:** 2026-10-25 (stable libraries; re-check Instagram API version at Phase 2)

---

*Phase: 01-foundation-and-connectors*
*Research completed: 2026-09-25*
*Ready for planning: yes*
