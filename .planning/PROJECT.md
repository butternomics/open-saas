# Butter.ATL Comment Assistant

## What This Is

A small local Python application (FastAPI, htmx, SQLite) that watches comments on Butter.ATL's own Instagram posts, understands each post once, decides which conversations are worth joining, drafts replies that sound like Butter, and puts them in a one-screen approval inbox for Brandon. Approved text is published through a locked, idempotent sender with a full audit trail. It starts in review mode and can graduate specific, low-risk categories to scoped automation only after measured quality earns it.

It lives in `butter-comment-assistant/` inside the `butternomics/open-saas` repo as a standalone directory and does not touch the Wasp template.

## Core Value

Butter joins more worthwhile conversations under its own posts, with replies that understand the post and sound like Butter, while Brandon spends less time and never loses control of what gets published.

## Requirements

### Validated

(None yet, ship to validate)

### Active

- [ ] Collect and prioritize eligible unanswered comments from monitored Butter posts automatically (checkpoints, pagination, overlap, backoff, thread relations, own-comment filtering, credential-expiry pause).
- [ ] Build one editable, versioned post brief per post from caption, creative, transcript and confirmed facts; flag missing context; invalidate unsent drafts when the brief changes.
- [ ] Triage every eligible comment into draft / hold for review / skip / already handled, classified by purpose, not sentiment.
- [ ] Draft replies in the background using editable voice rules (seeded from the Butter standing rules), a curated example library, approved facts and thread context, with strictly validated structured output.
- [ ] Treat comments, transcripts and external content as untrusted data that can never change voice rules, access secrets, authorize sending or execute tools.
- [ ] Review in one screen: post, comment, thread and editable draft together; Approve and send, Edit, Regenerate, Skip, Hold, Pause post; queues Ready / Needs attention / Sent / Skipped; batch approve only after text is visible.
- [ ] Publish reliably: pre-send recheck, task lock, idempotency, persisted reply ID, reconciliation after uncertain timeouts, distinct auth / rate-limit / permanent error classes, daily and per-post limits, global pause, all enforced outside the model.
- [ ] Keep an append-only audit log and a local daily recap (sent, held, errors) so Brandon can always see what the app did.
- [ ] Provide an evaluation harness: human-labeled baseline (respond / skip / needs judgment), coverage, quality, trust, workload and audience-response measures.
- [ ] Support scoped category automation that is OFF by default and gated on a recorded quality bar; sensitive posts and comments always stay in human review.
- [ ] Run fully in a container with no Instagram account, Ollama or GPU using a visibly labeled MockConnector and a fake LLM; real InstagramGraphConnector and OllamaClient built against documented APIs and tested with recorded fixtures.
- [ ] Bind to 127.0.0.1, protect state-changing requests with CSRF tokens, and keep secrets out of logs, prompts, browser responses and exports.

### Out of Scope

- Scheduling posts or generating feed content, this is a reply tool, not a publishing tool.
- Cold outreach, automated DMs, comment-to-DM funnels, sales funnels, the brief forbids them and they carry different trust risks.
- Customer service platform or CRM-style commenter profiles, unrelated to the four value dimensions (coverage, quality, workload, control).
- Automatic deletion or hiding of audience comments, explicitly forbidden; the delete endpoint is not implemented at all.
- Answering every comment or maximizing reply count, leaving a comment alone is a valid editorial decision; the coverage metric counts worthwhile comments only.
- Sentiment-driven engagement or engagement bait, positive sentiment alone never makes a reply eligible.
- Vector database, embeddings or model fine-tuning for voice, tags plus local text search over a small curated example bank is the chosen approach.
- Multi-account or multi-platform unified inbox, Instagram only for v1; the connector interface stays extensible but no other adapters are built.
- Always-on public webhook server, polling while the app runs is the baseline; webhooks are a later option once eligibility is confirmed.
- Cloud LLM as baseline, optional fallback only if local models prove insufficient after cheaper mitigations.
- TikTok, a subsequent adapter requiring separate access confirmation.

## Context

- Butter.ATL is Atlanta's culture channel. Comment sections carry local references, jokes, questions and opinions. A generic brand reply misses the joke and weakens the voice people recognize.
- Brandon does not consistently have time to read context, decide what deserves a reply, write it and follow up. Volume, response rate and time cost have not been measured yet; the evaluation harness exists to establish that baseline.
- Reference products: NapoleonCat (click-to-generate, learns from past replies) and BrandBastion (pre-drafted queue, post-aware media analysis, batch approval, selective auto-send). Butter borrows the patterns (background drafts, post-aware context, batch approval) without replicating either product or paying for a subscription.
- Research (see `.planning/research/`) settled the stack (Python 3.12, FastAPI 0.141, Jinja2, vendored htmx 2, SQLModel + Alembic on SQLite, APScheduler 3.11, httpx + tenacity, official ollama client, keyring, respx + pytest for tests), the component boundaries (Connector interface, Collector, Post-Brief Builder, Triage + Drafter, Approval Inbox, Sender + Reconciler, Policy/Limits, AuditLog) and the top pitfalls (App Review assumptions, duplicate sends after timeouts, prompt injection, unreliable JSON from small local models, hallucinated experiences, sentiment-based automation, sensitive threads, engagement bait, measuring by send count).
- Build environment for this session: a container inside the `butternomics/open-saas` repo with no Instagram account, no Meta app, no Ollama and no GPU. Real integrations are implemented against documented APIs and exercised with recorded fixtures and fakes. Live verification steps go into a "Needs a human" list.
- Butter standing rules bind the shipped default voice rules and all Butter-facing copy: no emojis, no em dashes, no "let me know" closers, no filler or robot language, no lazy contrast phrasing, no forced slang, do-not-cover list (murder, violent crime, shootings, stabbings, random tragedy) always stays in human review, never #COCWeekend, Capture the Flag ATL says "the app" and "check-ins", keep 404 Day separate from brand partnership talk. UI tokens: Butter yellow #EFB82E, Inter body, Space Mono utility, system display font fallback.

## Constraints

- **Tech stack**: Python 3.12, FastAPI + Jinja2 + vendored htmx, SQLite via SQLModel with Alembic migrations, APScheduler 3.x, httpx, official ollama client. No node toolchain, no vector DB, no training.
- **Location**: standalone `butter-comment-assistant/` directory in the open-saas repo; must not modify the Wasp template.
- **Build environment**: no Instagram account, Meta app, Ollama or GPU in the container. Everything must be buildable and testable with MockConnector and FakeLLMClient; real connectors tested with respx fixtures. Live steps are documented, not asserted.
- **Cost**: no required paid services or subscriptions; local model via Ollama is the baseline, cloud is optional and later.
- **Security**: bind 127.0.0.1 by default and refuse non-loopback without explicit override; CSRF protection on state-changing requests; credentials in the OS credential store or a 0600 protected file, never in logs, prompts, browser responses or exported examples; Ollama cloud features disabled.
- **Trust**: approval by default; the model never authorizes publishing; only a separate sender function operating on a stored, human-approved text hash can call the reply endpoint; automation is off by default and gated by measured quality per category.
- **Platform**: Instagram API with Instagram Login (`instagram_business_basic`, `instagram_business_manage_comments`), API version configurable, polling not webhooks in v1, no delete endpoint.
- **Voice**: default voice rules seeded from the Butter standing rules; rules and examples editable without code changes.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI + Jinja2 + htmx over Flask | Pydantic v2 is load-bearing everywhere (structured LLM output, SQLModel, config); one validation layer end to end; native async for httpx, Ollama and polling | Pending |
| SQLModel + Alembic on SQLite | Same class defines table and schema; migrations from day one because briefs, voice versions and outbound states will evolve | Pending |
| APScheduler 3.11.x, not 4.0 alpha | 4.0 is explicitly unstable; 3.x AsyncIOScheduler runs inside the FastAPI lifespan with no external cron | Pending |
| Connector interface with MockConnector (labeled MOCK) and InstagramGraphConnector | Only way to make the whole app testable with no network; swapping Mock to Real must require no changes outside the connector module and config | Pending |
| LLM client interface with FakeLLMClient and OllamaClient | Drafting logic, schema validation and invalidation are tested deterministically; real model is swapped in behind the same interface after hardware verification | Pending |
| Publishing gated by stored approved-text hash | Enforces "the model drafts text; a separate application function controls publishing" in code, not prompt wording; defeats injection and stale approvals structurally | Pending |
| Explicit state machines for comments, drafts, outbound tasks | Makes duplicate-send, uncertain-timeout, expired-token and paused-post acceptance checks mechanically testable | Pending |
| Post brief cached and versioned per post; drafts carry brief and voice versions | Media processed once; any brief or voice change invalidates unsent drafts instead of silently sending stale context | Pending |
| Tags + local text search for examples, no vector DB | Brief requirement; small curated bank is cheaper and auditable | Pending |
| Polling baseline, webhooks deferred | Standard Access does not guarantee webhooks; polling avoids a public server and matches the 127.0.0.1 design | Pending |
| Automation OFF by default, per category, gated on eval quality bar, per-comment sensitivity check | Brief: autonomy expands on demonstrated quality in specific situations, never elapsed time or sentiment | Pending |
| Live verification recorded in a "Needs a human" runbook, not in phase success criteria | No account, Ollama or GPU in the build container; do-the-work doctrine says only human-only steps go on that list | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason
2. Requirements validated? Move to Validated with phase reference
3. New requirements emerged? Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check, still the right priority?
3. Audit Out of Scope, reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-25 after initialization*
