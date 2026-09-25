<!-- GSD:project-start source:PROJECT.md -->
## Project

**Butter.ATL Comment Assistant**

A small local Python application (FastAPI, htmx, SQLite) that watches comments on Butter.ATL's own Instagram posts, understands each post once, decides which conversations are worth joining, drafts replies that sound like Butter, and puts them in a one-screen approval inbox for Brandon. Approved text is published through a locked, idempotent sender with a full audit trail. It starts in review mode and can graduate specific, low-risk categories to scoped automation only after measured quality earns it.

It lives in `butter-comment-assistant/` inside the `butternomics/open-saas` repo as a standalone directory and does not touch the Wasp template.

**Core Value:** Butter joins more worthwhile conversations under its own posts, with replies that understand the post and sound like Butter, while Brandon spends less time and never loses control of what gets published.

### Constraints

- **Tech stack**: Python 3.12, FastAPI + Jinja2 + vendored htmx, SQLite via SQLModel with Alembic migrations, APScheduler 3.x, httpx, official ollama client. No node toolchain, no vector DB, no training.
- **Location**: standalone `butter-comment-assistant/` directory in the open-saas repo; must not modify the Wasp template.
- **Build environment**: no Instagram account, Meta app, Ollama or GPU in the container. Everything must be buildable and testable with MockConnector and FakeLLMClient; real connectors tested with respx fixtures. Live steps are documented, not asserted.
- **Cost**: no required paid services or subscriptions; local model via Ollama is the baseline, cloud is optional and later.
- **Security**: bind 127.0.0.1 by default and refuse non-loopback without explicit override; CSRF protection on state-changing requests; credentials in the OS credential store or a 0600 protected file, never in logs, prompts, browser responses or exported examples; Ollama cloud features disabled.
- **Trust**: approval by default; the model never authorizes publishing; only a separate sender function operating on a stored, human-approved text hash can call the reply endpoint; automation is off by default and gated by measured quality per category.
- **Platform**: Instagram API with Instagram Login (`instagram_business_basic`, `instagram_business_manage_comments`), API version configurable, polling not webhooks in v1, no delete endpoint.
- **Voice**: default voice rules seeded from the Butter standing rules; rules and examples editable without code changes.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 (target 3.13-compatible) | Runtime | 3.13 is current stable (3.13.15, Aug 2026) and 3.12 remains in full support until Oct 2028. Pin to 3.12 for this project: it has the widest prebuilt-wheel coverage today for compiled deps (pywhispercpp, numpy/opencv used by frame sampling), while 3.13 wheel coverage for smaller/niche packages is still catching up in places. Either works; 3.12 is the safer default for a greenfield app that must "just install from PyPI." Avoid 3.14 — too new for guaranteed wheel availability on all target OSes as of Sep 2026. HIGH confidence on version numbers (python.org), MEDIUM on the wheel-coverage judgment call. |
| FastAPI | 0.141.x | Local web app + JSON endpoints for htmx partials | Verified latest on PyPI (0.141.1). Chosen over Flask despite Flask being the more "traditional" htmx pairing, because this app is built around Pydantic v2 models everywhere already (structured LLM output validation, API payloads, DB row shapes) and around async I/O (httpx calls to Graph API, Ollama, and in-process polling loop). FastAPI shares its core validation layer (Pydantic v2) with the rest of the stack and has native async support for background polling without extra glue. Jinja2Templates + StaticFiles cover the server-rendered HTML/htmx needs FastAPI doesn't do natively out of the box, at negligible extra cost. HIGH confidence. |
| Jinja2 | 3.1.x | HTML templating for the review UI | Standard, stable, works identically under FastAPI or Flask. No reason to deviate. HIGH confidence. |
| htmx | 2.0.x (vendored JS, no npm) | Partial-page updates (approve/edit/regenerate/send without full reloads) | Fits "local browser UI" with zero build tooling. Serve the single htmx.min.js file as a static asset — no npm/node toolchain needed for a Python-only project. HIGH confidence. |
| SQLite (stdlib `sqlite3`) via SQLModel | SQLModel 0.0.x (pin exact after `pip install`), Pydantic 2.13.x, SQLAlchemy 2.x | Data access layer over SQLite | SQLModel combines SQLAlchemy Core/ORM with Pydantic v2 models, so the same class defines both the DB table and the API/validation schema — a good fit for a small app with tables (posts, comments, drafts, outbound_tasks, examples) that map closely to API payloads. Avoids hand-writing both a dataclass and a schema. MEDIUM confidence: SQLModel is officially "not yet 1.0" and moves slower than SQLAlchemy itself; acceptable for this scope since the schema is small and stable. |
| Alembic | 1.13.x+ | Schema migrations | Standard companion to SQLAlchemy/SQLModel. Even for a single-file SQLite app, use Alembic from day one — the brief's data model (posts/comments/drafts/outbound_tasks/examples) will evolve, and hand-rolled `ALTER TABLE` scripts are exactly the kind of thing that causes silent drift between dev and the one real deployment. HIGH confidence. |
| APScheduler | 3.11.x (NOT 4.0) | In-process scheduled polling (comment collection cadence, token refresh, daily recap) | Verified: APScheduler 4.0 is still alpha (4.0.0a6, unstable API, explicitly "do not use in production") as of Sep 2026; 3.11.3 is the current stable release. Use `AsyncIOScheduler` from the 3.x line, backed by FastAPI's own event loop (`app.lifespan` starts/stops it) or `BackgroundScheduler` with a thread if simpler jobs are preferred. This avoids a separate cron/systemd-timer dependency, matching "one Python application, no separate automation subscription." HIGH confidence. |
| httpx | 0.28.1 | HTTP client for Graph API, Ollama HTTP fallback, general outbound calls | Verified latest on PyPI. Async-first, works natively with FastAPI, and is the client `respx` is built to mock — keeping the whole HTTP surface on one client library simplifies both retry logic and test fakes. HIGH confidence. |
| tenacity | 9.x | Retry/backoff for httpx calls (Graph API rate limits, transient Ollama errors) | Standard, well-maintained retry library with decorators for exponential backoff + jitter; pairs cleanly with httpx exceptions and Graph API's rate-limit error codes. Simpler and more explicit than hand-rolling backoff loops. MEDIUM confidence (not independently re-verified this session, but stable/uncontroversial choice). |
| ollama (official Python client) | 0.6.2 | Talk to local Ollama daemon for text generation, structured JSON output, and vision | Verified latest on PyPI; depends on httpx and pydantic itself, so it composes with the rest of the stack. Since Ollama 0.3.0, passing a JSON Schema (or a Pydantic model's `.model_json_schema()`) via the `format` parameter constrains decoding at the model level — use this for the drafting call's structured output (decision, draft_text, category, reason, facts_used, missing_context, review_flags, post_brief_version, voice_version) instead of asking the model to "return JSON" in the prompt and hoping. HIGH confidence on the client/version; MEDIUM on structured-output reliability specifics (schema-constrained decoding is real per Ollama's own docs, but exact guarantees vary by base model — validate with the target model during Phase 1). |
| pydantic | 2.13.x | Validation for structured LLM output, API request/response shapes, config | Verified latest (2.13.5). This is the backbone that ties FastAPI, SQLModel, and the ollama client together — one validation library, one mental model. Use `model_json_schema()` to generate the schema handed to Ollama's `format` param, and re-validate the model's JSON response before it ever touches the DB (never trust model output as-is, per the brief's untrusted-content rule). HIGH confidence. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| keyring | 25.7.x | Store the Instagram long-lived token (and any other secret) in the OS credential store, not in config/DB | Verified current (25.7.0/25.7.1). Use on the developer/operator machine for local credential storage per the brief ("Credentials belong in protected config or the OS credential store"). Note: keyring's backend availability depends on the OS/desktop session (macOS Keychain, Windows Credential Locker, Linux Secret Service via `dbus-python`/gnome-keyring). On a headless Linux box with no secret service running, keyring falls back to a null backend or fails — plan a documented fallback (e.g. an encrypted file backend via `keyrings.alt`, or a file with `0600` perms under a gitignored `secrets/` dir) for that case, and surface it in the roadmap's "Needs a human" list for the real deployment machine. MEDIUM confidence on headless-Linux behavior (training-data-based, verify on the actual target machine). |
| respx | 0.23.x (0.22+ acceptable) | Mock httpx requests in tests (fake Graph API, fake Ollama HTTP) | Verified current on PyPI, requires httpx 0.25+. Use for every test that would otherwise hit a real network endpoint — this is the mechanism that lets the whole Instagram/Ollama integration be tested in a container with neither service available, per the build-environment constraint. HIGH confidence. |
| pytest | 8.x | Test runner | Standard. Pair with `pytest-asyncio` for the async FastAPI/httpx code paths. HIGH confidence. |
| pytest-asyncio | 0.24.x+ | Run async test functions (FastAPI endpoints, async httpx calls, scheduler jobs) | Needed because FastAPI + httpx + APScheduler's AsyncIOScheduler push most of the I/O layer to async def. MEDIUM confidence (uncontroversial, not independently version-checked this session). |
| pywhispercpp | latest (check `pip install pywhispercpp` at build time; CPU wheels on PyPI) | Python bindings to whisper.cpp for local audio transcription | Confirmed actively maintained (github.com/absadiki/pywhispercpp), installable via `pip install pywhispercpp` with prebuilt CPU wheels, or `pip install git+https://github.com/absadiki/pywhispercpp` to build from source for the target hardware's optimizations (Metal/CUDA/etc). Prefer this over shelling out to the whisper.cpp CLI binary directly — it gives a normal Python API and avoids parsing subprocess stdout. Per the brief, whisper.cpp is a fallback for when production transcripts aren't already supplied, so this only needs to run occasionally. MEDIUM confidence — bindings ecosystem is fragmented (also saw `whispercpp` Pybind11-based and a Cython `whispercpp.py`); pywhispercpp is the most actively maintained and documented option, but re-verify it builds cleanly on the actual target machine (Phase 1 hardware check) before committing further. |
| ffmpeg-python OR direct subprocess calls to the `ffmpeg` CLI | n/a (wraps system ffmpeg) | Frame sampling from video creatives at timestamps, and audio extraction for whisper.cpp | Recommend calling the `ffmpeg`/`ffprobe` CLI directly via `subprocess` rather than adding `ffmpeg-python` as a dependency — the actual need here (grab N frames at timestamps, extract an audio track) is a handful of fixed CLI invocations, and a thin wrapper avoids a dependency that itself just shells out to the same binary. System `ffmpeg` must be installed and on PATH on the deployment machine (not pip-installable) — flag this as a "Needs a human" / environment prerequisite, since it is not available in the build container either. MEDIUM confidence (reasonable engineering judgment, not a contested ecosystem question). |
| python-dotenv | 1.x | Load local, non-secret config (ports, poll intervals, feature flags) from a `.env` file in dev | Keep actual secrets (tokens) out of `.env`/git-tracked files entirely — use keyring for those. `.env` is for non-sensitive local config only. LOW-MEDIUM confidence on necessity; optional convenience, not a hard requirement. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| ruff | Lint + format (replaces flake8/black/isort) | Single fast tool, standard for new Python projects in 2026; configure via `pyproject.toml`. |
| uv OR plain pip + venv | Dependency management / virtualenv | `uv` is the faster, increasingly standard choice for 2026 Python projects and works fine offline once the lockfile/cache is populated; plain `pip install -r requirements.txt` in a venv is the zero-surprises fallback if `uv` isn't available in the build/deploy environment. Pick one, don't mix. |
| pytest-cov | Coverage reporting | Optional but useful given the brief's emphasis on testable fakes for the untestable-live parts (Instagram, Ollama, GPU). |
## Installation
# Core
# Supporting
# Dev dependencies
- `ffmpeg` / `ffprobe` on PATH — for video frame sampling and audio extraction.
- `Ollama` daemon running locally, with a text model and a vision-capable model pulled (e.g. a Qwen2.5-VL variant per hardware tier — see Alternatives) and Ollama's cloud features explicitly disabled per the brief.
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| FastAPI + Jinja2 + htmx | Flask + Jinja2 + htmx | If the team strongly prefers Flask's simplicity and isn't already committing to Pydantic v2 as the app's shared validation layer, or wants to avoid learning `async def` at all. Flask's request/response model maps very directly onto htmx's "return an HTML fragment" pattern and has a more mature template-rendering ecosystem. For this project, FastAPI wins because Pydantic v2 is load-bearing everywhere else (LLM structured output, DB schemas via SQLModel), so sharing that validation layer end-to-end reduces total surface area more than Flask's marginal simplicity saves. |
| SQLModel | Raw SQLAlchemy 2.x Core/ORM, or bare stdlib `sqlite3` | Raw SQLAlchemy if the team wants more control and doesn't mind defining DB models and Pydantic schemas separately (more code, less "magic," arguably more mature/stable than SQLModel's sub-1.0 status). Bare `sqlite3` only for a much smaller app than this one — the brief's 5+ interrelated tables with versioning and lock/status fields justify an ORM/migration layer. |
| Alembic | Hand-written migration scripts / `CREATE TABLE IF NOT EXISTS` idempotent bootstrap | Acceptable only for a true single-developer, throwaway prototype. Not recommended here since the brief describes an evolving schema (brief versions, voice versions, outbound task states) that will need real migrations. |
| APScheduler 3.11.x (AsyncIOScheduler) | Plain `asyncio` loop with `asyncio.sleep`-based polling | A hand-rolled asyncio loop is viable and has zero extra dependency — reasonable if the only job is "poll comments every N minutes." APScheduler earns its keep once there are multiple jobs with different cadences (post polling, token refresh, daily recap, adaptive back-off per post) since it gives job stores, misfire handling, and per-job scheduling without hand-writing a mini-scheduler. |
| pywhispercpp | Direct `subprocess` calls to the `whisper.cpp` `main`/`whisper-cli` binary | If prebuilt pywhispercpp wheels don't build/run on the actual target hardware (verify in Phase 1's hardware check), fall back to invoking the compiled `whisper.cpp` CLI directly via subprocess and parsing its output — more brittle, but has zero Python binding/build risk. |
| Qwen2.5-VL (7B for single-GPU tiers, 3B for constrained/CPU-only) via Ollama | LLaVA, Llama 3.2 Vision, MiniCPM-V, Moondream | Llama 3.2 Vision 11B if the team wants more community familiarity and doesn't mind a larger model; Moondream (1.8B) or Qwen2.5-VL 3B on genuinely constrained/CPU-only hardware. Do not target the newer Qwen 3.6 vision line yet — as of mid-2026, Ollama had not wired up its multimodal projector, so vision input reportedly fails on it. Final model choice is explicitly gated on the Phase 1 hardware check per the brief ("Model choice must follow a check of the actual computer") — treat this table as a starting shortlist, not a commitment. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|--------------|
| APScheduler 4.0.x (any alpha) | Explicitly marked by its own maintainers as unstable / not for production, still alpha (4.0.0a6) as of Sep 2026 | APScheduler 3.11.x |
| A vector DB / embeddings pipeline for example selection | The brief explicitly rules this out ("Tags and local text search for example selection (no vector DB, no training)") | Simple tag-based filtering + SQLite `LIKE`/FTS5 full-text search over the `examples` table |
| A separate always-on public webhook server for comment collection (Phase 1) | The brief calls for starting with scheduled polling while the app runs, not an always-public server; webhooks are explicitly "later" and Standard Access is not guaranteed to include them | APScheduler-driven polling against the Graph API, with checkpoints/pagination; revisit webhooks in a later phase once eligibility is confirmed |
| Legacy Instagram scopes (`instagram_manage_comments`, `business_manage_comments`, the old Facebook Login for Business flow) | Deprecated Jan 27, 2025; current Instagram API with Instagram Login uses the `instagram_business_*` scope family | `instagram_business_basic` + `instagram_business_manage_comments` via Instagram Login (Business Login), issuing Instagram User access tokens directly (not Page/Facebook Login tokens) |
| Cloud LLM APIs (OpenAI, Anthropic, etc.) as the baseline drafting model | Brief requires no required paid services and no per-request cloud bill as the baseline; explicitly "a cloud model is optional, not baseline" | Ollama with a locally downloaded text model; keep a cloud fallback as an explicitly optional, later-phase config only if local quality proves insufficient |
| `whisper` (original OpenAI Python package, PyTorch-based) as the default transcription path | Heavier dependency (PyTorch), slower on CPU-only or constrained hardware than the C++ whisper.cpp inference path; the brief specifically names whisper.cpp | pywhispercpp (or subprocess to the compiled whisper.cpp CLI) |
| SQLAlchemy's own `Session`/model classes duplicated by hand-written Pydantic schemas | Doubles schema maintenance for a small app | SQLModel, which unifies both, accepting its sub-1.0 API-stability tradeoff |
## Stack Patterns by Variant
- Use a small vision model (Qwen2.5-VL 3B or Moondream 1.8B) and a small-to-mid text model, and keep concurrent Ollama jobs to 1.
- Increase polling intervals and reduce per-post frame-sampling counts to control CPU/time cost.
- Because this can only be confirmed on the real machine, the roadmap should treat "measure actual hardware and pick models accordingly" as an explicit Phase 1 task, not an assumption baked into the code.
- `keyring`'s default backends (Secret Service via dbus, KWallet) typically require an active desktop session; on a headless box they may silently fail or fall back to an insecure/null backend.
- Verify this concretely on the target machine in Phase 1; if it fails, use `keyrings.alt`'s encrypted file backend, or a manually-managed `0600`-permission secrets file outside version control, and document the choice — never fall back silently to plaintext without a decision being made explicitly.
- Fall back to invoking the compiled `whisper.cpp` binary via `subprocess`, parsing its `--output-json` output instead of stdout text, to keep a stable Python-side interface.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| respx 0.23.x | httpx >= 0.25 | httpx 0.28.1 (recommended) comfortably satisfies this. |
| ollama (py) 0.6.2 | httpx, pydantic | The official Ollama Python client itself depends on httpx and pydantic, so pinning compatible versions of those two also keeps the Ollama client happy — no separate version matrix to track. |
| SQLModel | SQLAlchemy 2.x, Pydantic 2.x | Confirm the SQLModel version resolved by pip is built against Pydantic 2.13.x at install time (`pip show sqlmodel`) since SQLModel's own releases sometimes lag the newest Pydantic point releases by a few weeks. |
| FastAPI 0.141.x | Pydantic 2.x, Starlette (pinned transitively) | Let pip resolve Starlette's version; don't pin it separately unless a conflict appears. |
| Python 3.12 | pywhispercpp, all other listed deps | Chosen specifically to maximize prebuilt-wheel availability; if the target machine already has 3.13 with working wheels for pywhispercpp, 3.13 is also fine — the version choice here is a wheel-availability hedge, not a hard API requirement. |
## Instagram Graph API Specifics (for the account adapter)
- **API family / auth route:** "Instagram API with Instagram Login" (Business Login), which issues Instagram User access tokens directly against `graph.instagram.com`, distinct from the older Facebook Login for Business route through `graph.facebook.com`/Page tokens. Supports Instagram Business and Creator accounts. HIGH confidence (official Meta docs).
- **Current API version:** v25.0 (reported released Feb 2026 per third-party 2026 developer guides) — MEDIUM confidence, since this was not cross-checked directly against Meta's own versioning changelog page this session. Per the brief's own instruction, select the version at implementation time and keep it configurable rather than hardcoding it into the client — do not trust this document's version number as still-current by the time Phase 1 code is written; re-check `https://developers.facebook.com/docs/graph-api/changelog` then.
- **Required scopes:** `instagram_business_basic` (baseline account/data access) and `instagram_business_manage_comments` (read and reply to comments). A third scope, `instagram_business_content_publish`, is unrelated to comment replies (it's for publishing new media) and is NOT needed for this app's scope (public replies to existing comments only, no new post creation). `instagram_business_manage_messages` is for DMs, explicitly out of scope per the brief. HIGH confidence (Meta's own Business Login docs, fetched directly).
- **Legacy scopes deprecated:** `instagram_manage_comments`/`business_manage_comments` (old naming) were deprecated Jan 27, 2025 — do not use them or follow any tutorial still referencing them. HIGH confidence.
- **Key endpoints:**
- **Token lifecycle:** Long-lived Instagram User access tokens last roughly 60 days. They can be refreshed via `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=<token>` once the token is at least 24 hours old and not yet expired; a token that goes unrefreshed for 60+ days cannot be refreshed and requires a fresh login. Build the token-refresh APScheduler job to run well inside that window (e.g. every 3-5 days, refreshing regardless of exact expiry, well clear of both the 24-hour minimum and 60-day cliff) rather than cutting it close. HIGH confidence (Meta's own refresh_access_token reference).
- **Rate limits:** Not independently re-verified with exact numbers this session (MEDIUM-LOW confidence on precise figures) — Graph API rate limiting is generally calculated per app/user and varies by endpoint category; the brief already calls for "pagination, saved checkpoints, overlapping retrieval, and rate-limit backoff," which this stack supports via `tenacity` retry/backoff wrapping every `httpx` call to the Graph API. Treat exact rate-limit numbers as a Phase 1 verification item against the live app dashboard once real Meta app credentials exist, not something to hardcode from this document.
- **Mock/testable design:** Because no Meta app or Instagram account exists in the build container, structure the Instagram adapter as a small interface (e.g. `InstagramClient` protocol/ABC) with a real `httpx`-based implementation and a `MockInstagramClient` used in dev/tests, clearly labeled MOCK in the UI per the brief. Test the real client's request/response handling with `respx`-mocked fixtures recorded from Meta's documented example payloads, not live calls.
## Sources
- PyPI JSON API (`pypi.org/pypi/<pkg>/json`) — fetched directly for `pydantic` (2.13.5), `httpx` (0.28.1), `fastapi` (0.141.1), `ollama` (0.6.2). HIGH confidence, live data.
- `developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login` — fetched directly for Instagram Login scopes (`instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_content_publish`, `instagram_business_manage_messages`) and the Business Login auth model. HIGH confidence.
- Meta's IG Comment / Replies reference pages (`developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-comment/...`) via WebSearch summary — endpoint shapes for comments/replies. MEDIUM-HIGH confidence (official doc pages identified but not directly WebFetched for full text this session).
- Meta's `refresh_access_token` reference page via WebSearch summary — 60-day token lifecycle and refresh endpoint. MEDIUM-HIGH confidence (official doc identified, summary-level verification).
- `docs.ollama.com/capabilities/structured-outputs` and `ollama.com/blog/structured-outputs` via WebSearch summary — `format` param + JSON Schema / Pydantic constrained decoding, available since Ollama 0.3.0. MEDIUM confidence (not directly WebFetched, but consistent across multiple independent sources).
- `pypi.org/project/APScheduler` and related listings — confirmed 3.11.3 stable, 4.0 still alpha (4.0.0a6) as of Sep 2026. HIGH confidence.
- `pypi.org/project/respx` and `keyring` listings — confirmed respx ~0.23.x (httpx 0.25+ requirement) and keyring 25.7.x. HIGH-MEDIUM confidence (WebSearch summaries of PyPI listing pages, not raw JSON fetch).
- `github.com/absadiki/pywhispercpp` via WebSearch — actively maintained whisper.cpp Python bindings, prebuilt CPU wheels on PyPI. MEDIUM confidence.
- `python.org/downloads` release pages via WebSearch — Python 3.13.15 (Aug 2026) current in the 3.13 line, 3.13 EOL 2029, 3.14 now the latest feature line. HIGH confidence on the dates; MEDIUM (judgment call) on recommending 3.12 over 3.13/3.14 for this specific project's wheel-availability needs.
- Ollama vision model landscape (multiple 2026 blog/guide sources via WebSearch, cross-referenced) — Qwen2.5-VL family strength, hardware-tier shortlist, and the Qwen 3.6/Ollama projector gap. LOW-MEDIUM confidence — third-party blog consensus, not official Ollama model-support documentation; treat the model choice as provisional pending the brief's mandated Phase 1 hardware check.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
