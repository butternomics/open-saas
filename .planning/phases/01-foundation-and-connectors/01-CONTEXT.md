# Phase 1: Foundation and Connectors - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning
**Mode:** `--auto` (every gray area resolved with the recommended default; no user prompts)

<domain>
## Phase Boundary

Phase 1 delivers the runnable skeleton every later phase builds on: the `butter-comment-assistant/` package, the full SQLite schema with Alembic migrations, typed settings persisted in SQLite and editable in the UI, secret handling with log scrubbing, the 127.0.0.1 bind guard and CSRF protection, the app shell with Butter tokens and the MOCK badge, the Connector protocol with a fixture-backed MockConnector and a respx-tested InstagramGraphConnector, the LLM client protocol with a deterministic FakeLLMClient and a respx-tested OllamaClient, and a connection status screen.

It does NOT collect comments, build briefs, triage, draft, review, send, audit or evaluate. Those are Phases 2 to 5. Phase 1 only defines the contracts (schema, enums, transition tables, protocols, settings keys) those phases consume, so that no later phase migrates a core table or invents a second interface ad hoc.

Requirements in scope: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, CONN-01, CONN-02, CONN-03, CONN-04, CONN-05.

</domain>

<decisions>
## Implementation Decisions

### Package layout and tooling
- **D-01:** Directory `butter-comment-assistant/` at the repo root, src layout: `butter-comment-assistant/src/butter_comment_assistant/` is the importable package (`import butter_comment_assistant`). Nothing outside `butter-comment-assistant/` is touched (the Wasp template stays untouched).
- **D-02:** `pyproject.toml` (PEP 621, setuptools backend) with `requires-python = ">=3.12"`, runtime deps `fastapi`, `jinja2`, `python-multipart`, `uvicorn`, `sqlmodel`, `alembic`, `apscheduler>=3.11,<4`, `httpx`, `tenacity`, `ollama`, `keyring`; optional group `dev` = `pytest`, `pytest-asyncio`, `respx`, `ruff`. Console script `butter-comment-assistant = butter_comment_assistant.main:main` plus `python -m butter_comment_assistant`. No node toolchain, no python-dotenv, no keyrings.alt (the app ships its own 0600 file store).
- **D-03:** One documented install command and one documented run command (FOUND-01): install `cd butter-comment-assistant && uv venv --python 3.12 .venv && uv pip install -e ".[dev]"` (pip fallback documented: `python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"`), run `.venv/bin/butter-comment-assistant`, test `.venv/bin/pytest` from `butter-comment-assistant/`. The test suite must pass with no network, no Instagram, no Ollama, no GPU, no ffmpeg.
- **D-04:** Module map (fixed names so later phases know where things go): `config.py` (process config from env), `main.py` (create_app, lifespan, CLI main), `storage/` (`enums.py`, `models.py`, `db.py`, `settings_repo.py`), `secrets.py`, `logging_setup.py`, `connectors/` (`base.py`, `mock.py`, `instagram_graph.py`, `factory.py`), `llm/` (`base.py`, `fake.py`, `ollama_client.py`, `factory.py`), `web/` (`__init__.py` templating helpers, `csrf.py`, `routes_settings.py`, `routes_status.py`), `templates/`, `static/`. Reserved for later phases (empty in Phase 1, do not create): `collector/`, `briefs/`, `drafting/`, `review/`, `sending/`, `policy/`, `audit/`, `evaluation/`.
- **D-05:** Migrations live in `butter-comment-assistant/migrations/` (Alembic `script_location`), config in `butter-comment-assistant/alembic.ini`; fixtures for MockConnector in `butter-comment-assistant/fixtures/mock/`; recorded API fixtures for respx tests in `butter-comment-assistant/tests/fixtures/`. Runtime data defaults to `butter-comment-assistant/data/` (gitignored): `data/butter.db`, `data/secrets.json`, `data/media_cache/`.

### Storage schema and state machines
- **D-06:** SQLModel classes in `storage/models.py` define these tables, all created by the initial Alembic migration `0001_initial_schema` (FOUND-02): `posts`, `comments`, `drafts`, `outbound_tasks`, `examples`, `knowledge`, `voice_rules`, `settings`, `audit_log`, `eval_labels`. Later phases add columns or tables only through new Alembic revisions and never rename these tables or their primary keys.
- **D-07:** Primary keys: `posts.id` and `comments.id` are the platform IDs (TEXT). `drafts.id`, `outbound_tasks.id`, `examples.id`, `knowledge.id`, `eval_labels.id` are UUID4 hex strings generated in Python. `voice_rules.version` is an integer PK. `settings.key` is the PK. `audit_log.id` is an autoincrement integer. All timestamps are naive UTC `datetime` produced by `storage.enums.utcnow()`; never store local time.
- **D-08:** Column sets (later phases build on these): 
  - `posts`: id, caption, source_url, media_type, media_refs_json (JSON list), posted_at, brief_json (JSON), brief_version (int, default 0), context_status (enum, default unprocessed), sensitivity_flag (bool, default false), sensitivity_reason, monitored (bool, default false), paused (bool, default false), last_synced_at, checkpoint_cursor, next_poll_at, poll_interval_s, quiet_cycles (int), created_at, updated_at.
  - `comments`: id, post_id (FK posts.id), parent_id (nullable, self reference), thread_root_id, depth (int), author_id, author_username, text, is_own_reply (bool), created_at_platform, fetched_at, deleted_at (nullable), handling_status (enum), handled_by_draft_id (nullable), audience_replied_after_butter (bool, default false), updated_at. Indexes on post_id, handling_status, parent_id.
  - `drafts`: id, comment_id (FK), version (int), draft_text, decision, category, reason, facts_used_json, missing_context_json, review_flags_json, system_flags_json, post_brief_version, voice_version, status (enum), approved_text, approved_text_hash, approved_by, approved_at, invalidated_reason, auto_sent (bool, default false), sent_at, created_at, updated_at. Indexes on comment_id, status.
  - `outbound_tasks`: id, draft_id (FK), comment_id, approved_text_hash, idempotency_key (unique), status (enum), lock_owner, locked_at, attempts (int), last_attempt_at, returned_reply_id, error_class (enum, nullable), error_detail, reconciliation_note, created_at, updated_at. Index on status.
  - `examples`: id, text, tags_json, kind (positive|negative), status (approved|unreviewed|retired), source_comment_id, reviewer, notes, created_at, updated_at.
  - `knowledge`: id, fact_text, category, source, valid_from, valid_until, reviewer, status (active|retired), created_at, updated_at.
  - `voice_rules`: version (PK), rules_text, is_active (bool), updated_by, updated_at.
  - `settings`: key, value_json (JSON), updated_at.
  - `audit_log`: id, entity_type, entity_id, event, from_status, to_status, actor, original_text, approved_text, detail_json, created_at. Index on (entity_type, entity_id). Append-only by convention: no update/delete helper exists.
  - `eval_labels`: id, comment_id, sample_name, label (respond|skip|needs_judgment), labeler, note, created_at.
- **D-09:** `storage/enums.py` defines the string enums and transition tables that every later phase imports rather than redefining: `CommentStatus` (new, triaged, drafted, held, skipped, already_handled, stale), `DraftStatus` (pending_review, held, approved, queued, sent, invalidated, skipped), `OutboundStatus` (pending, locked, sent, uncertain, reconciled, failed_auth, rate_limited, permanent_error), `ContextStatus` (unprocessed, caption_only, incomplete, complete), `ErrorClass` (auth, rate_limit, transient, permanent, uncertain), `ConnectorKind` (mock, instagram), `LLMKind` (fake, ollama), `ExampleKind`, `ExampleStatus`, `KnowledgeStatus`, `EvalLabel`, `AuditEvent` (draft_created, draft_edited, draft_regenerated, draft_approved, draft_invalidated, draft_held, draft_skipped, task_created, task_locked, send_succeeded, send_uncertain, send_failed_auth, send_rate_limited, send_permanent_error, reconciled_as_sent, reconciled_as_not_sent, post_paused, post_resumed, settings_changed, brief_updated, voice_rules_updated, auth_failed, sync_succeeded). Transition tables `COMMENT_TRANSITIONS`, `DRAFT_TRANSITIONS`, `OUTBOUND_TRANSITIONS` are dicts of `{from: set(to)}`, and `assert_transition(table, from, to)` raises `IllegalTransition`.
- **D-10:** Transition tables: Comment: new->triaged; triaged->drafted|held|skipped|already_handled; drafted->held|skipped|already_handled|stale; held->triaged|skipped|already_handled; stale->triaged; skipped->triaged; already_handled is terminal. Draft: pending_review->held|approved|skipped|invalidated; held->pending_review|skipped|invalidated; approved->queued|invalidated; queued->sent|invalidated|approved; sent, invalidated and skipped are terminal (regeneration creates a new draft row with version+1). Outbound: pending->locked; locked->sent|uncertain|failed_auth|rate_limited|permanent_error|pending (stale lock reclaim); uncertain->reconciled; reconciled->sent|pending; rate_limited->pending; failed_auth->pending; permanent_error->pending (manual retry only); sent is terminal.
- **D-11:** `storage/db.py` exposes `make_engine(database_url)`, `run_migrations(database_url)` (programmatic `alembic.command.upgrade(cfg, "head")` using the packaged `alembic.ini` and `migrations/`), and `session_scope(engine)`. The app runs migrations on every start inside the FastAPI lifespan before serving. Tests get a fresh temporary SQLite file per test through a `conftest.py` fixture that runs the real migrations (never `SQLModel.metadata.create_all`), and a test asserts that Alembic autogenerate finds zero differences between the models and the migrated database.

### Settings and process configuration
- **D-12:** Two configuration layers. Process config (`config.py`, read once from environment variables with prefix `BCA_`): `BCA_DATA_DIR` (default `./data`), `BCA_DB_PATH` (default `{data_dir}/butter.db`), `BCA_HOST` (default `127.0.0.1`), `BCA_PORT` (default `8765`), `BCA_ALLOW_NON_LOOPBACK` (default unset), `BCA_CONNECTOR` (`mock`|`instagram`, default `mock`), `BCA_LLM` (`fake`|`ollama`, default `fake`), `BCA_SECRET_STORE` (`auto`|`keyring`|`file`, default `auto`), `BCA_LOG_LEVEL` (default `INFO`). App settings (edited in the UI, persisted in the `settings` table) are a pydantic model `AppSettings` in `storage/settings_repo.py` with typed defaults and `SettingsRepo.load(session)` / `SettingsRepo.save(session, settings, actor)`.
- **D-13:** `AppSettings` keys and defaults (FOUND-03): `daily_send_limit=20`, `per_post_send_limit=5`, `max_interaction_depth=2`, `poll_interval_floor_s=300`, `poll_interval_ceiling_s=21600`, `overlap_window_s=300`, `oldest_monitored_date=None` (ISO date or null), `instagram_api_version="v25.0"`, `ollama_host="http://127.0.0.1:11434"`, `ollama_text_model="llama3.1:8b"`, `ollama_vision_model="qwen2.5vl:7b"`, `global_pause=False`, `automation_enabled=False`. Each key is stored as its own `settings` row (`key` = field name, `value_json` = JSON value). Runtime state written by later phases uses the same table with a `state.` prefix (Phase 1 defines `state.last_successful_sync_at`, default null, and reads it on the status screen).
- **D-14:** The settings screen at `GET /settings` renders one form with every `AppSettings` field; `POST /settings` validates through pydantic, saves, writes an `audit_log` row with event `settings_changed` and `detail_json` listing changed keys, and re-renders with a confirmation. Values survive restart because they live in SQLite, proven by a test that recreates the app on the same database file.

### Secrets and logging
- **D-15:** `secrets.py` defines a `SecretStore` protocol (`get(name) -> str | None`, `set(name, value)`, `delete(name)`, `backend_name`) with two implementations: `KeyringSecretStore` (service name `butter-comment-assistant`) and `FileSecretStore` (JSON file at `{data_dir}/secrets.json` created with mode 0600 and refused, with a clear error, if its mode is wider than 0600). `resolve_secret_store(config)`: `keyring` forces keyring, `file` forces file, `auto` tries keyring and falls back to file when keyring raises `NoKeyringError`/`KeyringError` or the backend is `keyring.backends.fail.Keyring`, logging a WARNING that names the fallback (never silent). Secret names are constants: `instagram_access_token`, `instagram_app_secret`. The build container has no usable keyring backend, so all tests use `FileSecretStore` in a temp directory.
- **D-16:** `logging_setup.py` installs a `RedactingFilter` on the root logger and on `uvicorn` loggers. It replaces: any `access_token=<value>` query or form parameter, `Authorization: Bearer <value>` headers, and any token-shaped string (`IGQ`/`IGAA`/`EAA` prefixed strings of 40+ characters, or any run of 60+ `[A-Za-z0-9_-]` characters) with `[REDACTED]`. A test logs a fake token in every position and asserts it never appears in captured output (FOUND-04). Secrets never enter templates, JSON responses, prompts or exports because no code path passes `SecretStore` into those layers; the status screen shows only "token present: yes/no".

### Network binding and CSRF
- **D-17:** `main.py:main()` reads config, and before starting uvicorn calls `assert_loopback(host, allow_override)`: any host that is not `127.0.0.1`, `::1` or `localhost` raises `RefusedBindError` unless `BCA_ALLOW_NON_LOOPBACK=1` is set, in which case a WARNING is logged and startup continues (FOUND-05). The same check runs in `create_app()` lifespan so an ASGI server started by hand cannot bypass it. Tests call `assert_loopback` directly for `0.0.0.0`, `192.168.1.5`, `127.0.0.1`, `::1`, with and without the override.
- **D-18:** CSRF (FOUND-06) is a Starlette middleware in `web/csrf.py`: every response sets cookie `bca_csrf` (random 32-byte hex, `SameSite=Strict`, `HttpOnly`, `Path=/`) if missing; every `POST`, `PUT`, `PATCH`, `DELETE` must carry the same value in header `X-CSRF-Token` or form field `csrf_token`, compared with `secrets.compare_digest`; mismatch or absence returns `403` with body `{"error": "csrf_token_missing_or_invalid"}` and nothing is executed. `base.html` emits `<meta name="csrf-token">` and `hx-headers` on `<body>` so every htmx request carries the header, and every plain form includes the hidden field. Tests prove a POST without the token is rejected and with it succeeds.

### App shell and UI tokens
- **D-19:** FastAPI app factory `create_app(config=None) -> FastAPI` in `main.py`; Jinja2 templates via `fastapi.templating.Jinja2Templates(directory=<package>/templates)`; static files from `<package>/static` mounted at `/static`; htmx 2.0.4 vendored as `static/htmx.min.js` (downloaded once from `https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js` during execution and committed; no CDN reference in templates). `base.html` provides: header with product name, nav links (Settings, Status), a persistent badge area, and a footer. `GET /` redirects to `/status` in Phase 1.
- **D-20:** Butter tokens in `static/app.css` as CSS variables: `--butter-yellow: #EFB82E` (the only yellow), `--ink: #111111`, `--paper: #FFFFFF`, `--muted: #6B6B6B`, body font `Inter, system-ui, -apple-system, "Segoe UI", sans-serif`, utility/mono font `"Space Mono", ui-monospace, monospace`, display font falls back to the system stack (no bundled commercial fonts, no external font loading). No emojis and no em dashes anywhere in templates or UI copy; a test greps `templates/` and `static/app.css` for U+2014 and for common emoji ranges.
- **D-21:** MOCK badge (CONN-02): when the active connector's `is_mock` is true, `base.html` renders `<span class="badge badge-mock" data-testid="mock-badge">MOCK CONNECTOR</span>` in the header on every page. When `automation_enabled` is false the header also shows `AUTOMATION OFF` (groundwork for AUTO-01 visibility). A test requests every registered GET route and asserts the badge is present under MockConnector.

### Connector protocol
- **D-22:** `connectors/base.py` defines DTOs (pydantic models) `PostDTO` (id, caption, media_type, media_urls, permalink, posted_at), `CommentDTO` (id, post_id, parent_id, author_id, author_username, text, created_at, is_own_reply is computed by the caller from `AuthStatus.account_id`), `CommentPage` (items, next_cursor, usage), `UsageInfo` (call_count_pct, total_time_pct, total_cputime_pct, business_use_case_raw, near_limit: bool computed at >= 75 percent), `ReplyResult` (reply_id, raw), `AuthStatus` (ok, account_id, username, token_expires_at, scopes_documented: list[str], error: str | None, checked_at), and the error hierarchy `ConnectorError` > `AuthError`, `RateLimitError(retry_after_s)`, `TransientError`, `PermanentError`, `UncertainSendError` (raised only by `post_reply` when the outcome is unknown, e.g. timeout after the request was sent).
- **D-23:** `Connector` is a `typing.Protocol` (runtime-checkable) with exactly these members, all `async`: `fetch_posts(since: datetime | None = None, limit: int = 25) -> list[PostDTO]`, `fetch_comments(post_id: str, cursor: str | None = None) -> CommentPage`, `fetch_replies(comment_id: str, cursor: str | None = None) -> CommentPage`, `post_reply(comment_id: str, text: str, idempotency_key: str) -> ReplyResult`, `check_auth() -> AuthStatus`, `refresh_credentials() -> AuthStatus`, plus read-only properties `kind: ConnectorKind`, `is_mock: bool`, `display_name: str`. There is no delete, hide or unhide member, and a test asserts that no file under `src/` contains the strings `DELETE` as an HTTP method, `delete_comment`, or `/hide` (CONN-03). `connectors/factory.py:build_connector(config, settings, secret_store) -> Connector` returns MockConnector for `mock` and lazily imports InstagramGraphConnector for `instagram`; swapping requires only `BCA_CONNECTOR` and the stored token.
- **D-24:** `MockConnector` (CONN-02) loads `fixtures/mock/dataset.json` (3 posts, at least 60 comments on the first post across 3 pages of 25 so pagination is real, replies including one authored by Butter's own account id `17841400000000001`, one instruction-injection comment, one do-not-cover comment) and is driven by a `MockScenario` object with an ordered queue of behaviors per operation: `ok`, `near_limit` (usage headers at 90 percent), `rate_limit` (raise `RateLimitError` once), `auth_failure` (raise `AuthError`), `timeout` (raise `UncertainSendError` from `post_reply`, `TransientError` from reads), `permanent_error`. It records every `post_reply` call in `sent_replies` and appends the reply to the in-memory thread so reconciliation tests in Phase 4 can find it. `is_mock` is always true and `display_name` is `"MockConnector (MOCK)"`.
- **D-25:** `InstagramGraphConnector` (CONN-03) uses `httpx.AsyncClient(base_url=f"https://graph.instagram.com/{api_version}", timeout=httpx.Timeout(10.0, read=20.0))` with the token read from `SecretStore` at call time (never stored on the instance in logs), endpoints `GET /me?fields=id,username`, `GET /{media_id}/comments?fields=id,text,username,timestamp,parent_id,from,replies&limit=50`, `GET /{comment_id}/replies`, `POST /{comment_id}/replies` with `message`, `GET /refresh_access_token?grant_type=ig_refresh_token`, and `GET /me/media?fields=id,caption,media_type,media_url,permalink,timestamp,children{media_url,media_type}`. It follows `paging.cursors.after` / `paging.next`, parses `x-app-usage` and `x-business-use-case-usage` headers into `UsageInfo`, maps HTTP 401/403 and Graph error codes 190 and 10 to `AuthError`, HTTP 429 and error codes 4, 17, 32, 613 to `RateLimitError`, 5xx and connection errors on GET to `TransientError` (tenacity retry, max 3 attempts, exponential backoff with jitter, only for GET), `httpx.TimeoutException` on POST to `UncertainSendError` (no retry ever on POST), everything else to `PermanentError`. `scopes_documented` is the constant list `["instagram_business_basic", "instagram_business_manage_comments"]`. All behaviour is verified with respx against recorded fixture JSON in `tests/fixtures/instagram/responses.json`; no live call exists in the test suite.

### LLM client protocol
- **D-26:** `llm/base.py` defines `LLMClient` as a runtime-checkable `typing.Protocol` with `async generate_structured(request: LLMRequest, schema: type[BaseModel]) -> LLMResult`, `async health() -> LLMHealth`, and property `kind: LLMKind`. `LLMRequest` carries `system: str`, `user: str`, `images: list[bytes] = []`, `model: str | None = None`, `temperature: float = 0.2`, `max_tokens: int = 512`; the drafter in Phase 3 builds `user` from delimited untrusted data, the client never inspects it. `LLMResult` carries `parsed: BaseModel`, `raw_text: str` (already scrubbed by `logging_setup.scrub`), `model: str`, `duration_ms: int`. Failures raise `LLMOutputInvalid(raw_text_scrubbed, errors)` when the response does not validate against `schema`, and `LLMUnavailable` when the backend cannot be reached. No tool or function calling parameter exists in the protocol (DRAFT-06 groundwork).
- **D-27:** `FakeLLMClient` (CONN-04) is deterministic: a `responses` queue of dicts or raw strings is consumed in order; when the queue is empty it returns a default object built by `schema.model_validate(schema_defaults)` where defaults come from a `default_factory` callable supplied at construction, so every phase can script exact outputs and can script an invalid response (raw string `"not json"` or a dict missing required fields) to exercise the `LLMOutputInvalid` path. It records every request in `calls` for assertions, including the images byte lengths.
- **D-28:** `OllamaClient` uses `ollama.AsyncClient(host=settings.ollama_host)` and `chat(model=..., messages=[{"role":"system",...},{"role":"user","content":..., "images":[...]}], format=schema.model_json_schema(), options={"temperature": ..., "num_predict": ...}, stream=False)`, then validates `response.message.content` with `schema.model_validate_json`. It refuses to construct when `ollama_host` is not a loopback address unless `BCA_ALLOW_NON_LOOPBACK=1` (local-only rule) and never sets cloud, web-search or tool parameters; the runbook item for disabling Ollama cloud features on the daemon is documented in RESEARCH.md and later in the Phase 5 runbook. respx tests cover: structured output success, invalid JSON to `LLMOutputInvalid`, image input reaching the request body as base64, connection refused to `LLMUnavailable`, `health()` calling `/api/tags`.

### Connection status screen
- **D-29:** `GET /status` (CONN-05) renders: connector `display_name` and kind with the MOCK badge, auth state from a cached `check_auth()` result (refreshed by `POST /status/check` which is CSRF-protected), `account_id`/`username` when present, `scopes_documented`, token presence (yes/no) and `token_expires_at`, secret store backend name, `state.last_successful_sync_at` (shows "never" when null), LLM client kind and `health()` result, `global_pause` and `automation_enabled` flags. Auth failures render in a red "AUTH PROBLEM" block that is visually distinct from "no new data" (groundwork for COLL-07).

### Testing conventions
- **D-30:** pytest with `asyncio_mode = "auto"` (`pytest-asyncio`), `respx` for every httpx call, `fastapi.testclient.TestClient` for routes, `tmp_path` SQLite databases created by real migrations, `FileSecretStore` in `tmp_path`, `MockConnector` and `FakeLLMClient` as the defaults in `conftest.py`. Tests are named `tests/test_<module>.py`; the full suite command is `pytest` from `butter-comment-assistant/` and must finish in under 60 seconds offline. `ruff check src tests` must pass (config in `pyproject.toml`, line length 100).

### Claude's Discretion
- Exact CSS beyond the tokens in D-20, the wording of status labels, the sample captions and comment text in the mock dataset (must contain no emojis or em dashes and must not invent facts about real people), the internal structure of `MockScenario`, whether the Alembic initial revision is autogenerated then hand-checked or written by hand (it must be committed either way), and the choice of pydantic `BaseModel` vs `SQLModel` (non-table) for DTOs.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product scope and requirements
- `.planning/PROJECT.md` — scope, constraints, key decisions (stack, seams, hash-gated sender, automation OFF).
- `.planning/REQUIREMENTS.md` — FOUND-01..06, CONN-01..05 are this phase; later IDs explain what the schema must carry.
- `.planning/ROADMAP.md` §"Phase 1: Foundation and Connectors" — goal, success criteria, plan outline.
- `.planning/BRIEF.md` §"Minimum data records", §"Standing rules", §"Build-environment constraints" — the record fields and the Butter canon binding UI copy.

### Architecture and stack
- `.planning/research/ARCHITECTURE.md` §"Recommended Project Structure", §"Pattern 1: Connector Interface", §"Pattern 2: Explicit State Machines", §"State Management", §"SQLite Schema Sketch" — the source of the module names, enums and table list pinned above.
- `.planning/research/STACK.md` §"Core Technologies", §"Supporting Libraries", §"Instagram Graph API Specifics" — versions, Instagram Login scopes, endpoints, token refresh, structured output via `format`.
- `.planning/research/PITFALLS.md` §"Security Mistakes", §"Token expiry silently stalling", §"Rate limit / X-App-Usage", §"Mock connector indistinguishable" — the behaviours the Phase 1 tests must prove.
- `.planning/research/SUMMARY.md` — executive summary and phase-by-phase risk map.

### Project instructions
- `CLAUDE.md` (repo root) — project constraints and stack; do not modify the Wasp template.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None. `butter-comment-assistant/` does not exist yet; the rest of the repository is the Open SaaS Wasp template (TypeScript) and must not be modified or imported.

### Established Patterns
- No Python code exists in the repo. Patterns are set by this phase: src layout, SQLModel tables plus Alembic revisions, Protocol-based seams with mock and real implementations, respx-recorded contract tests.

### Integration Points
- Repo root `.gitignore` already ignores `node_modules/`; `butter-comment-assistant/.gitignore` must add `.venv/`, `data/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.db`, `*.db-journal`.
- The build container has Python 3.12 (`uv python` and `/usr/bin/python3.12`), `uv 0.x` on PATH, PyPI reachable through the proxy, jsdelivr reachable for the htmx download, no Ollama, no ffmpeg, keyring backend `keyring.backends.fail.Keyring` (so the file secret store is the only working store here).

</code_context>

<specifics>
## Specific Ideas

- Verified this session in a throwaway venv (Python 3.12): fastapi 0.141.1, starlette 1.7.0, sqlmodel 0.0.47 (pins SQLAlchemy 2.0.54), alembic 1.20.0, apscheduler 3.11.3, httpx 0.28.1, respx 0.23.1, ollama 0.6.2, pydantic 2.13.5, keyring 25.7.0, pytest 9.1.1, pytest-asyncio 1.4.0, uvicorn 0.54.0, jinja2 3.1.6, python-multipart 0.0.32, ruff 0.16.9. `ollama.AsyncClient.chat` accepts `format: dict` (JSON schema) and message `images`; `Jinja2Templates.TemplateResponse(request, name, context)` is the Starlette 1.x signature; `TestClient` works with httpx 0.28 (emits a StarletteDeprecationWarning that is acceptable).
- The MOCK badge must be a literal, unmissable visual element in the header, not a log line (PITFALLS.md "Mock connector indistinguishable").
- Auth failure must never look like a quiet day: the status screen distinguishes "AUTH PROBLEM" from "no data yet" (PITFALLS.md "Token expiry silently stalling").

</specifics>

<deferred>
## Deferred Ideas

- Collector jobs, APScheduler wiring and adaptive polling: Phase 2 (APScheduler is a declared dependency but no job is registered in Phase 1).
- Post briefs, media analysis, transcript interfaces: Phase 2.
- Triage, drafting prompts, voice rules seed, examples and knowledge UI: Phase 3.
- Review inbox, approval hash storage, sender, policy limits enforcement, audit log UI, daily recap: Phases 3 and 4 (the tables and enums exist from Phase 1; the behaviour does not).
- Evaluation reports, acceptance suite, automation gating, "Needs a human" runbook: Phase 5.
- Webhooks, TikTok, cloud LLM fallback: v2 (REQUIREMENTS.md).

None of the above were folded into this phase.

</deferred>

---

*Phase: 01-foundation-and-connectors*
*Context gathered: 2026-09-25*
