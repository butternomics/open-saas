# Roadmap: Butter.ATL Comment Assistant

## Overview

Five coarse phases take the project from an empty `butter-comment-assistant/` directory to a review-first comment assistant that can be evaluated against Brandon's labels and, only then, allowed to automate two narrow categories. Phase 1 lays the storage, security, connector and LLM seams that make everything testable with MockConnector and FakeLLMClient in a container with no Instagram, Ollama or GPU. Phase 2 collects threads and builds versioned post briefs. Phase 3 delivers the first end-to-end capability: drafts in a one-screen inbox with Butter's voice rules and examples. Phase 4 publishes reliably with limits, an audit log and a daily recap. Phase 5 adds the evaluation harness, the acceptance suite, gated automation and the "Needs a human" runbook for the live steps this environment cannot perform.

Every phase is complete when its success criteria hold with MockConnector and FakeLLMClient. Live verification (real account read, one authorized send, hardware and model selection, the 100-comment evaluation with Brandon's labels) lives in the runbook produced by Phase 5, not in any phase's success criteria.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation and Connectors** - Scaffold, storage, settings, secrets, security baseline, Connector and LLM client seams with labeled mocks and fixture-tested real implementations
- [ ] **Phase 2: Collection and Post Briefs** - Checkpointed adaptive collector with thread relations and own-comment filtering, plus versioned, invalidating post briefs
- [ ] **Phase 3: Triage, Drafting and Review Inbox** - Purpose-based triage, validated structured drafting with voice rules and examples, injection isolation, and the one-screen approval inbox
- [ ] **Phase 4: Sending, Limits, Audit and Recap** - Hash-gated idempotent sender with recheck, lock, reconciliation and error classes, app-level limits and global pause, audit log and daily recap
- [ ] **Phase 5: Evaluation and Scoped Automation** - Baseline labeling, coverage/quality/trust/workload/audience reports, acceptance suite, gated OFF-by-default automation, "Needs a human" runbook

## Phase Details

### Phase 1: Foundation and Connectors
**Goal**: Brandon can start the app locally, see a clearly labeled MOCK connection, and every later component has a tested seam for storage, secrets, Instagram and the local model
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, CONN-01, CONN-02, CONN-03, CONN-04, CONN-05
**Success Criteria** (what must be TRUE):
  1. User can install and start the app from `butter-comment-assistant/` with one command each, and `pytest` passes offline with no Instagram, Ollama, GPU or ffmpeg
  2. User sees a persistent MOCK badge on every screen when MockConnector is active, and a connection status screen with connector type, auth state, documented scopes and last successful sync
  3. User can edit limits, poll intervals, oldest monitored date, API version, model names and global pause in the settings screen, and the values survive restart in SQLite
  4. The server refuses to bind to a non-loopback address without an explicit override, rejects state-changing requests without a CSRF token, and a test proves no token-shaped string reaches logs
  5. InstagramGraphConnector and OllamaClient pass respx contract tests against recorded fixtures (pagination, usage headers, 429, auth failure, timeout, token refresh, structured output, image input) and no delete endpoint exists
**Plans**: 3 plans

Plans:
- [ ] 01-01: Scaffold, SQLite schema with Alembic migrations, settings and secret handling, 127.0.0.1 bind and CSRF baseline, app shell with Butter tokens (wave 1)
- [ ] 01-02: Connector protocol, fixture-backed MockConnector with MOCK badge, InstagramGraphConnector with respx contract tests, connection status screen (wave 2, parallel with 01-03)
- [ ] 01-03: LLM client interface, deterministic FakeLLMClient, OllamaClient with schema-constrained output and vision, respx tests (wave 2, parallel with 01-02)

**UI hint**: yes

### Phase 2: Collection and Post Briefs
**Goal**: Monitored posts have their comment threads collected reliably and each post has one editable, versioned brief that says what the post is about and what context is missing
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: COLL-01, COLL-02, COLL-03, COLL-04, COLL-05, COLL-06, COLL-07, COLL-08, COLL-09, BRIEF-01, BRIEF-02, BRIEF-03, BRIEF-04, BRIEF-05, BRIEF-06, BRIEF-07
**Success Criteria** (what must be TRUE):
  1. User can pick which recent posts are monitored and set an oldest monitored date, and the collector fills threads from mock fixtures with parent links, no duplicates and no misses across a restart, including a multi-page fixture
  2. Butter's own comments never appear as new work, the parent comment shows as already handled, and audience follow-ups after a Butter reply are recorded
  3. When the mock returns an auth failure, collection pauses with a loud distinct status showing the last successful sync; near-limit headers and 429s slow polling without dropping the cycle; active posts poll more often than quiet ones
  4. User can open a post and see its brief (topic, tone, confirmed facts separate from inferred intent, missing context, context status) and edit it, which bumps the version
  5. A caption-only or media-missing post shows an incomplete context status; changing the brief invalidates its unsent drafts; do-not-cover posts carry a sensitivity flag; media is analyzed once per post, not per comment
**Plans**: 2 plans

Plans:
- [ ] 02-01: Collector: monitored post selection, adaptive polling via APScheduler, checkpoints with overlap, upsert by platform ID, thread links, own-reply filter, backoff, auth pause, audience-continuation capture, resume from backlog (wave 1, parallel with 02-02)
- [ ] 02-02: Post briefs: builder pipeline behind the LLM client (caption, image/carousel text, frame sampling and transcript interfaces that degrade gracefully), facts vs inferred intent, context status, sensitivity flag, versioning and draft invalidation, brief editor UI (wave 1, parallel with 02-01)

**UI hint**: yes

### Phase 3: Triage, Drafting and Review Inbox
**Goal**: Brandon opens one screen and finds drafted replies that understand the post and sound like Butter, with everything he needs to approve, edit, regenerate, skip, hold or pause in seconds
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: DRAFT-01, DRAFT-02, DRAFT-03, DRAFT-04, DRAFT-05, DRAFT-06, DRAFT-07, DRAFT-08, DRAFT-09, VOICE-01, VOICE-02, VOICE-03, VOICE-04, VOICE-05, REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04, REVIEW-05, REVIEW-06
**Success Criteria** (what must be TRUE):
  1. Every eligible comment in the mock data lands in exactly one of draft, hold, skip or already handled, cheap filters run before any model call, and classification never reads sentiment
  2. User sees drafts already prepared in the inbox with post, comment, thread, editable draft, facts_used, missing_context and review flags on one screen, organized in Ready, Needs attention, Sent and Skipped queues with system problems visibly separate from content holds
  3. User can Approve and send, Edit, Regenerate, Skip, Hold and Pause post; batch approval only accepts items whose text was expanded; any edit, regeneration or brief/voice version change invalidates a prior approval and stores a new exact text and hash
  4. Malformed FakeLLMClient output routes to Needs attention with a "model output invalid" flag, an injection fixture comment cannot change rules, read secrets or trigger a send, drafts with untraceable specifics or repeated jokes are flagged, and do-not-cover or allegation comments hold even under a normal post
  5. User can edit versioned voice rules seeded from the Butter standing rules, manage tagged examples and negative examples, manage knowledge entries with validity dates, and promote an edited reply into the examples in one action
**Plans**: 3 plans

Plans:
- [ ] 03-01: Triage and drafting engine: deterministic pre-filters, prompt assembly with delimited untrusted data, strict output schema, hold-on-invalid, facts cross-check, repetition check, per-comment sensitivity, background drafting job, voice rules seed (wave 1)
- [ ] 03-02: Review inbox UI: one-screen review, all six actions, four queues, system-vs-content hold distinction, batch approve after visibility, approval text and hash, invalidation, Butter tokens (wave 2, parallel with 03-03)
- [ ] 03-03: Voice, examples and knowledge management UI: versioned voice rules editor, tagged example library with tag plus text search, negative examples, promotion from inbox, knowledge entries with validity dates (wave 2, parallel with 03-02)

**UI hint**: yes

### Phase 4: Sending, Limits, Audit and Recap
**Goal**: Approved text and only approved text reaches the platform exactly once, within app-level limits, and Brandon can always see what the app did and why
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: SEND-01, SEND-02, SEND-03, SEND-04, SEND-05, SEND-06, SEND-07, AUDIT-01, AUDIT-02
**Success Criteria** (what must be TRUE):
  1. Approving a draft creates an outbound task that the mock connector receives with the exact approved text; the sender refuses unapproved, invalidated or hash-mismatched drafts and never reads unapproved draft text
  2. Before sending, the sender rechecks existence, eligibility, post pause and prior Butter replies (in-app and on the mock platform); a comment deleted or answered in the mock is not sent and is surfaced
  3. A mock timeout marks the task uncertain, reconciliation finds or does not find the reply, and no duplicate is ever sent across retries or a simulated restart; auth failure, rate limit and permanent error each show distinct states and handling
  4. Daily, per-post and interaction depth limits and global pause block drafting and sending outside the model at both triage and send time, and global pause takes effect instantly on every screen
  5. User can filter an activity log of every transition with actor, timestamps and original versus approved text, and view a daily recap where auth failures are never presented as a quiet day and sent counts sit beside quality context
**Plans**: 3 plans

Plans:
- [ ] 04-01: Policy limits module (daily, per-post, depth, global pause) wired into triage, and append-only audit log writer with activity log UI (wave 1)
- [ ] 04-02: Sender state machine, hash-gated send_approved, pre-send recheck, lock and stale reclaim, idempotency key, reply ID persistence, uncertain plus reconciler, distinct error classes, scheduler jobs (wave 2, parallel with 04-03)
- [ ] 04-03: Daily recap page and system-error surfacing (auth expiry, uncertain sends, permanent errors) in the inbox, auto-send marker groundwork (wave 2, parallel with 04-02)

**UI hint**: yes

### Phase 5: Evaluation and Scoped Automation
**Goal**: Brandon can measure coverage, quality, trust, workload and audience response against his own labels, run the acceptance checks, and enable narrow automation only when the numbers justify it
**Mode**: mvp
**Depends on**: Phase 4
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08, AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05
**Success Criteria** (what must be TRUE):
  1. User can assemble a baseline sample from collected comments, label each respond, skip or needs judgment in the UI or by CSV import, and the labels are stored separately from system decisions
  2. User can view coverage, quality, trust, workload export and audience-response reports computed from the labels, drafts, audit log and thread activity, with sent counts never shown alone
  3. The acceptance suite passes for duplicate delivery, a reply made directly on the platform, a deleted comment, an expired token, a paused post, an uncertain send timeout and an instruction-injection comment, and proves unapproved text cannot publish
  4. Automation is OFF by default and visible on every screen; only uncomplicated acknowledgments and fact-backed answers can be enabled, per comment and never by sentiment or post level alone, only when the evaluation report records the category's quality bar, and global pause disables it instantly; auto-sent items are marked distinctly
  5. A "Needs a human" runbook lists every live step with what to do and what evidence to record: Meta app and scopes, real read, one authorized send, hardware and model selection, ffmpeg/whisper.cpp/keyring checks, the 100-comment evaluation
**Plans**: 3 plans

Plans:
- [ ] 05-01: Evaluation harness: sample builder, labeling UI and CSV import, coverage, quality, trust, workload export and audience-response reports (wave 1, parallel with 05-02 and 05-03)
- [ ] 05-02: Scoped automation: settings OFF by default, two categories, per-comment eligibility gate, quality-bar gate tied to evaluation report, interaction limit, auto-send markers (wave 1, parallel)
- [ ] 05-03: Acceptance suite fixtures and tests, "Needs a human" runbook, README with install, run and verification steps (wave 1, parallel)

**UI hint**: yes

## Needs a Human

Steps that cannot be performed in the build container. They are documented in the Phase 5 runbook and are not success criteria of any phase.

1. Create the Meta app, choose Instagram API with Instagram Login, confirm account type, and record which of `instagram_business_basic` and `instagram_business_manage_comments` are granted or need App Review.
2. Connect the Butter account, store the token in the credential store, and prove one authorized read of one owned post, its comments and one reply thread with the real connector.
3. Authorize and perform one test send of an approved reply, then confirm reconciliation records the returned reply ID.
4. Check the deployment machine (OS, CPU/GPU, memory), install Ollama with cloud features disabled, pick text and vision models that pass the structured-output tests on real Butter-length prompts, and install ffmpeg and, if needed, whisper.cpp.
5. Run the roughly 100-comment, 10-post evaluation with Brandon's labels and set numeric pilot targets from the baseline.
6. Decide, per category, whether the recorded quality bar justifies enabling scoped automation.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Connectors | 0/3 | Not started | - |
| 2. Collection and Post Briefs | 0/2 | Not started | - |
| 3. Triage, Drafting and Review Inbox | 0/3 | Not started | - |
| 4. Sending, Limits, Audit and Recap | 0/3 | Not started | - |
| 5. Evaluation and Scoped Automation | 0/3 | Not started | - |
