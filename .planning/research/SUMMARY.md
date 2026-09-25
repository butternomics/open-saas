# Project Research Summary

**Project:** Butter.ATL Comment Assistant
**Domain:** Local-first AI comment-reply assistant for a brand's own Instagram posts (single operator, approval-first, scoped automation later)
**Researched:** 2026-09-25
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a single-operator, local-first reply assistant, not a social management suite. The mature products in the space (NapoleonCat, BrandBastion) converge on the same loop: collect comments, understand the post (caption plus creative), pre-draft replies in the background, review them with post context beside the draft, batch approve, publish under platform limits, and report what happened. Butter needs that loop with three deliberate differences: media-grounded, versioned post briefs that admit when context is missing; a small human-curated example bank instead of a trained or vector-backed voice model; and automation that graduates per category on measured quality rather than a toggle.

The recommended build is one Python 3.12 process: FastAPI with Jinja2 and vendored htmx for the inbox, SQLModel plus Alembic over a single SQLite file, APScheduler 3.11 inside the FastAPI lifespan for polling and recaps, httpx plus tenacity for all outbound calls, the official ollama client for text, structured JSON and vision, keyring for the token, and respx plus pytest for tests. The architecture research settles the seams that make this testable with no network, no Instagram account and no GPU: a Connector protocol with a MockConnector (visibly labeled MOCK) and an InstagramGraphConnector; an LLM client interface with a fake and an Ollama implementation; explicit state machines for comments, drafts and outbound tasks; and a sender that only ever publishes a stored, human-approved text hash.

The biggest risks are trust failures, not features: duplicate public replies after an ambiguous timeout, prompt injection through comment text, small local models emitting invalid JSON, invented personal experiences that read as good Butter voice, and automation drifting onto sentiment or onto post-level flags that miss a thread turning sensitive. Every one of these is mitigated structurally (reconcile before retry, hash-gated sender, strict schema with hold-on-failure, facts_used cross-check, per-comment eligibility) and each becomes a named fixture in the acceptance suite. Two things cannot be verified in the build container and must be recorded as "Needs a human": the real Instagram read and one authorized send (App Review for `instagram_business_manage_comments` may be required), and the hardware/model selection for Ollama.

## Key Findings

### Recommended Stack

Python 3.12 for wheel coverage, FastAPI 0.141 because Pydantic v2 is load-bearing everywhere (LLM structured output, DB models via SQLModel, config) and async fits httpx, Ollama and the polling loop. Jinja2 and a vendored `htmx.min.js` give partial-page updates with no node toolchain. SQLite is the only store; SQLModel unifies table and schema and Alembic handles the schema evolution the brief already implies (brief versions, voice versions, outbound states). APScheduler 3.11.x (never the 4.0 alpha) runs polling, token refresh and the daily recap in-process.

**Core technologies:**
- FastAPI 0.141 + Jinja2 + htmx 2 (vendored): local inbox UI and JSON/HTML partial endpoints, one validation layer end to end
- SQLModel + SQLAlchemy 2 + Alembic on SQLite: posts, comments, drafts, outbound tasks, examples, knowledge, voice rules, settings, audit log
- APScheduler 3.11 AsyncIOScheduler: adaptive polling, token refresh, recap, reconciliation passes
- httpx 0.28 + tenacity 9: Graph API and Ollama calls with backoff; respx 0.23 mocks the same client in tests
- ollama 0.6 client + pydantic 2.13: schema-constrained structured output via `format=model_json_schema()`, vision input, local-only with cloud features disabled
- keyring 25.7 (fallback: 0600 file via `keyrings.alt`): long-lived Instagram token outside code, prompts and logs
- pywhispercpp or a subprocess to the whisper.cpp CLI, plus system ffmpeg: transcript fallback and frame sampling, both environment-dependent and not available in the container
- pytest + pytest-asyncio + respx + ruff: the whole suite runs offline

Instagram specifics: use the Instagram API with Instagram Login (`graph.instagram.com`), scopes `instagram_business_basic` and `instagram_business_manage_comments` only, API version configurable (verify at implementation time), long-lived tokens refreshed every few days well inside the 60-day window, endpoints `GET /{media}/comments`, `GET /{comment}/replies`, `POST /{comment}/replies`. Never implement `DELETE /{comment}`.

### Expected Features

**Must have (table stakes):**
- Comment collection with pagination, checkpoints, overlap, backoff and adaptive per-post frequency
- Post-aware context (caption plus creative plus transcript) cached once per post and reused
- Drafts prepared in the background before Brandon opens the queue
- Four-way triage by purpose: draft / hold / skip / already handled
- Single review screen with post, thread, editable draft and all actions; batch approval after text is visible
- Voice conditioning from editable rules and curated examples
- Thread awareness so Butter never double-replies and never treats its own replies as new work
- Reliable single send (lock, idempotency, reconciliation) with distinct error classes
- Activity log, daily and per-post limits, global pause
- MockConnector visibly labeled MOCK

**Should have (differentiators from the brief):**
- Explicit missing-context and confidence flags instead of silent guessing
- Example promotion loop (edited reply becomes a tagged example)
- Untrusted-input isolation enforced in code
- Scoped, per-category automation gated on measured quality, OFF by default
- Baseline labeling and coverage / quality / trust / workload / audience-response measurement
- Daily local recap

**Defer (v2+):**
- TikTok adapter, webhook ingestion, cloud model fallback, broader automation categories

**Anti-features (never):** full auto-send, comment-to-DM or lead capture, auto hide/delete, answer-every-comment KPI, sentiment-based eligibility, multi-platform inbox, vector DB or fine-tuning, content scheduling, CRM profiles, public webhook server in v1.

### Architecture Approach

One Python process with clear internal boundaries. Nothing except `connectors/` talks to Instagram; nothing except `sending/sender.py` may call `post_reply`, and it only accepts a `draft_id` plus `approved_text_hash` set by a human action. Post briefs are per-post, cached and versioned; drafts are per-comment and carry `post_brief_version` and `voice_version`, so a version bump invalidates every unsent draft under that post. Limits live in one `policy/limits.py` module called at triage (cheap pre-check) and again at send (authoritative). Every transition appends to an audit log. The drafter has no tool access and returns only schema-validated text.

**Major components:**
1. Connector interface: `MockConnector` (fixture-backed, MOCK badge) and `InstagramGraphConnector` (pagination cursors, token refresh, usage headers, error classes)
2. Collector: adaptive polling per post, per-post `last_synced_at` checkpoint with overlap window, upsert by platform ID, parent linking, own-reply filter at ingestion, auth-failure pause
3. Post-Brief Builder: caption + media analysis (vision via LLM client) + transcript lookup + facts, versioned, invalidating
4. Triage + Drafter: deterministic pre-filters, prompt assembly, strict Pydantic schema, hold on invalid output
5. Approval Inbox: FastAPI + htmx, queues, actions, approved text + hash, invalidation on edit/regen/context change
6. Sender + Reconciler: `PENDING -> LOCKED -> SENT | UNCERTAIN -> RECONCILED -> (SENT | PENDING)`, plus `FAILED_AUTH`, `RATE_LIMITED`, `PERMANENT_ERROR`
7. Policy/Limits + AuditLog: daily, per-post, interaction depth, global pause; append-only trail feeding the recap
8. Storage: SQLite plus a local media cache, the seam that keeps everything testable

### Critical Pitfalls

1. **App Review assumptions.** `instagram_business_manage_comments` may need Meta App Review; keep "read comments" and "publish a reply" as separate human-verified gates and document granted scopes in the repo.
2. **Duplicate reply after an ambiguous timeout.** Timeout means UNCERTAIN, never failed; reconcile the live thread before any retry, lock the task, persist the reply ID.
3. **Prompt injection through comments.** Comment, thread and transcript text are delimited data; the drafter has no tools; publishing reads only the human-approved hash; an injection comment is a real fixture in the suite.
4. **Small local models and unreliable JSON.** Use schema-constrained generation, validate strictly, route failures to Needs attention with a "model output invalid" flag, log scrubbed raw output.
5. **Invented experiences that sound like Butter.** Keep confirmed facts separate from inferred intent, cross-check specifics against `facts_used`, surface `facts_used` beside the draft, track invented-experience rate as its own quality metric.
6. **Sentiment or post-level-only automation.** Eligibility keys off purpose category and per-comment content plus post flags; do-not-cover topics, allegations, disputes, sponsor issues and missing facts always hold.
7. **Measuring by send count.** Capture post-reply thread activity from the collector onward and never show sends without coverage, quality and audience-response beside them.
8. **Local UI on 0.0.0.0 or without CSRF, tokens in logs.** Refuse non-loopback bind by default, CSRF on state-changing requests, scrub token-shaped strings and test for it.

## Implications for Roadmap

Based on research, suggested phase structure (coarse: 5 phases, 1-3 plans each, plans parallelizable in waves):

### Phase 1: Foundation and Connectors
**Rationale:** Storage, config, secrets, the Connector seam and the LLM client seam are what every later component depends on and what makes the whole project testable in this container. The pitfalls research puts App Review assumptions and credential leakage here.
**Delivers:** `butter-comment-assistant/` scaffold, SQLite schema with migrations, settings, secret handling, 127.0.0.1 bind and CSRF baseline, Connector protocol with labeled MockConnector and InstagramGraphConnector (respx-tested), LLM client interface with FakeLLMClient and OllamaClient (respx-tested), connection status screen with MOCK badge.
**Addresses:** Mock connector, storage, security table stakes.
**Avoids:** Standard vs Advanced Access assumptions (documented scopes, separate read/publish gates), 0.0.0.0 bind, no CSRF, tokens in logs.
**Parallel waves:** scaffold/storage/security first; then connectors and LLM clients in parallel.

### Phase 2: Collection and Post Briefs
**Rationale:** The collector proves checkpoints, pagination, threading and own-reply filtering against MockConnector; briefs are per-post artifacts that must exist and be versioned before drafting starts. Both only depend on Phase 1.
**Delivers:** monitored post selection, adaptive polling, checkpoints with overlap, upsert by platform ID, parent links, own-reply filter, usage-header backoff, auth-failure pause with last-sync display, audience-continuation capture; post brief builder with media/transcript pipeline behind the LLM client, editable briefs, facts vs inferred intent, context status, version bump and draft invalidation, sensitivity flags.
**Uses:** APScheduler, httpx/tenacity, SQLModel, ollama vision behind the interface.
**Implements:** Collector and Post-Brief Builder.
**Avoids:** pagination cursor mishandling, own-reply loop, rate-limit throttling, token expiry looking like a quiet day, re-analyzing media per comment.
**Parallel waves:** collector and briefs are independent plans.

### Phase 3: Triage, Drafting and Review Inbox
**Rationale:** With comments and briefs in place, the drafting engine and the inbox deliver the first end-to-end user capability: Brandon sees drafted replies with full context and can act on them. Voice rules and the example library belong here because they are inputs to drafting.
**Delivers:** four-way triage with deterministic pre-filters, prompt assembly, strict structured output, injection isolation, facts cross-check, repetition check, per-comment sensitivity holds; voice rules seeded from the standing rules and versioned; example library with tags, promotion, negative examples; knowledge entries with validity dates; the one-screen inbox with all actions, queues, batch approve, approval hash and invalidation, Butter UI tokens.
**Avoids:** prompt injection, unreliable JSON, hallucinated experiences, sentiment-based classification, engagement bait, rubber-stamp batch approval, regenerated-but-unreviewed sends.
**Parallel waves:** drafting engine and schema first; then inbox UI and voice/example/knowledge management UI in parallel.

### Phase 4: Sending, Limits, Audit and Recap
**Rationale:** Publishing is the highest-trust action and depends on approved drafts from Phase 3. It is deliberately thin and isolated. Limits and the audit log are wired into both triage and send here so the two checks cannot drift.
**Delivers:** hash-gated `send_approved`, pre-send recheck (exists, eligible, not paused, not already answered in-app or on Instagram), lock with stale reclaim, idempotency key, persisted reply ID, UNCERTAIN plus reconciliation, distinct auth / rate-limit / permanent errors, daily and per-post and depth limits, global pause; append-only audit log UI and daily recap that separates auth failures from quiet days.
**Avoids:** duplicate replies after timeout, treating uncertain as failed, the sender reading current draft text, send count as headline metric.
**Parallel waves:** limits and audit first; then sender/reconciler and recap/error surfacing in parallel.

### Phase 5: Evaluation and Scoped Automation
**Rationale:** The brief judges success against a human-labeled baseline, and automation is only allowed after that evidence exists. Both consume the audit trail and the decision log from earlier phases.
**Delivers:** baseline sample builder and labeling UI with CSV import, coverage / quality / trust / workload / audience-response reports, the acceptance test suite (duplicate delivery, reply made in Instagram, deleted comment, expired token, paused post, uncertain timeout, injection comment, unapproved text cannot publish), automation settings OFF by default with per-category and per-comment gates tied to a recorded quality bar, and the "Needs a human" runbook for live verification.
**Avoids:** sentiment or post-level-only automation, measuring by send count, automation widened without a quality re-check.
**Parallel waves:** evaluation harness, automation gating and acceptance suite are independent plans.

### Phase Ordering Rationale

- Dependencies flow storage -> connectors -> collector/briefs -> drafting/inbox -> sender -> evaluation/automation, exactly the architecture research build order.
- Real Instagram and real Ollama integrations are implemented early (Phase 1) but verified live only through the runbook, so no phase's success depends on resources the container lacks.
- Each phase after 1 delivers something Brandon can observe with MockConnector and FakeLLMClient: collected threads and briefs (2), drafts in an inbox (3), sends and a recap (4), reports and gated automation (5).
- Every critical pitfall maps to the phase that owns its prevention and to a fixture in Phase 5's acceptance suite.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Instagram API with Instagram Login endpoint payload shapes, current API version, usage-header semantics and token refresh details for the real connector's fixtures; Ollama structured-output and vision request formats for the client.
- **Phase 2:** ffmpeg frame sampling and transcript handling behind an interface that degrades gracefully when the binaries are missing.

Phases with standard patterns (skip research-phase):
- **Phase 3:** FastAPI + Jinja2 + htmx inbox patterns, Pydantic schema validation, CSRF middleware are well documented.
- **Phase 4:** State machines, idempotency keys and reconciliation are established patterns; specifics are already in ARCHITECTURE.md.
- **Phase 5:** Reporting and labeling are internal to the app; the acceptance list is fully specified by the brief.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against PyPI and official Meta docs; MEDIUM on whisper.cpp binding choice and Ollama structured-output edge cases |
| Features | MEDIUM | Competitor features come from vendor marketing pages; the brief's own requirements are the primary source and are HIGH |
| Architecture | HIGH | Standard ports-and-adapters, state machines, idempotency, injection isolation applied to a small domain |
| Pitfalls | MEDIUM | API mechanics are HIGH; exact rate limits, Standard vs Advanced Access boundary and webhook availability are MEDIUM/LOW until checked on the real app dashboard |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- Meta App Review and granted scopes: cannot be verified here. Runbook item; the real connector is written against documented endpoints and fixtures only.
- Current Graph API version and rate-limit numbers: keep the version configurable and the backoff header-driven; re-check at implementation time.
- Hardware and model selection for Ollama, and structured-output reliability of the chosen model: runbook item; FakeLLMClient carries the suite until then.
- ffmpeg, whisper.cpp and keyring backend availability on the deployment machine: implement behind interfaces that degrade to "missing context" or a documented file fallback, verified by a human on the target machine.
- One-level reply nesting: model data as comment -> replies and confirm on the first real read.

## Sources

### Primary (HIGH confidence)
- `.planning/BRIEF.md`: all product constraints, boundaries, standing rules and acceptance checks
- PyPI JSON API: pydantic 2.13.5, httpx 0.28.1, fastapi 0.141.1, ollama 0.6.2, APScheduler 3.11.3 / 4.0.0a6
- developers.facebook.com Instagram API with Instagram Login (Business Login) scopes and auth model

### Secondary (MEDIUM confidence)
- Meta IG Comment / Replies references, refresh_access_token, rate limiting overview, webhooks for Instagram (official pages via search summaries)
- docs.ollama.com structured outputs, Ollama blog
- NapoleonCat and BrandBastion product pages (vendor-authored)
- pywhispercpp GitHub, PyPI listings for respx and keyring

### Tertiary (LOW confidence)
- Third-party 2026 developer blogs on Graph API rate limits and access tiers; third-party pricing comparison for BrandBastion; blog consensus on Ollama vision model choices

---
*Research completed: 2026-09-25*
*Ready for roadmap: yes*
