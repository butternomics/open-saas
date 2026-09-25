# Requirements: Butter.ATL Comment Assistant

**Defined:** 2026-09-25
**Core Value:** Butter joins more worthwhile conversations under its own posts, with replies that understand the post and sound like Butter, while Brandon spends less time and never loses control of what gets published.

All v1 requirements must be buildable and testable in a container with no Instagram account, no Ollama and no GPU, using the visibly labeled MockConnector and FakeLLMClient. Live verification steps are tracked in the "Needs a human" runbook (EVAL-08), not asserted by any requirement below.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation

- [ ] **FOUND-01**: User can install and start the app from `butter-comment-assistant/` with one documented command each (Python 3.12, FastAPI, htmx, SQLite), and the full test suite passes offline with no Instagram, Ollama, GPU or ffmpeg present
- [ ] **FOUND-02**: App persists posts, comments, drafts, outbound tasks, examples, knowledge, voice rules, settings and audit log in a single SQLite file with versioned migrations that run automatically on start
- [ ] **FOUND-03**: User can view and edit app settings (daily limit, per-post limit, interaction depth, poll intervals, oldest monitored date, API version, model names, global pause) in the UI without code changes
- [ ] **FOUND-04**: Credentials are stored in the OS credential store or a 0600 protected file, never appear in logs, prompts, browser responses or exported examples, and a test scans log output for token-shaped strings
- [ ] **FOUND-05**: Server binds to 127.0.0.1 by default and refuses to start on a non-loopback address unless an explicit documented override is set
- [ ] **FOUND-06**: Every state-changing request (approve, send, edit, skip, pause, settings) is protected by a CSRF token and rejected without it

### Connectors

- [ ] **CONN-01**: All platform I/O goes through a single Connector interface (fetch posts, fetch comments with cursor, fetch replies, post reply with idempotency key, check auth) and the whole app runs end to end on MockConnector
- [ ] **CONN-02**: MockConnector is labeled MOCK in a persistent, unmissable badge on every screen and can simulate pagination, near-limit usage headers, 429s, auth failure, timeouts and permanent errors from fixtures
- [ ] **CONN-03**: InstagramGraphConnector implements the Instagram API with Instagram Login (`instagram_business_basic`, `instagram_business_manage_comments`) with configurable API version, long-lived token refresh, usage-header parsing and distinct error classes, verified by respx contract tests against recorded fixtures; no delete endpoint exists
- [ ] **CONN-04**: All model calls go through an LLM client interface with a deterministic FakeLLMClient and an OllamaClient that uses schema-constrained structured output and image input, is local-only with cloud features disabled, and is verified by respx tests
- [ ] **CONN-05**: User can see a connection status screen showing connector type, auth state, granted scopes as documented, and the time of the last successful sync

### Collector

- [ ] **COLL-01**: User can choose which recent posts are monitored and set an explicit oldest monitored date; the collector never looks further back
- [ ] **COLL-02**: Collector follows pagination cursors, saves a per-post checkpoint, re-fetches with an overlap window, and upserts comments by platform ID so no comment is missed or duplicated across restarts
- [ ] **COLL-03**: Collector polls active posts more often and reduces frequency as activity slows, within configurable floor and ceiling intervals
- [ ] **COLL-04**: Collector backs off proactively on near-limit usage headers and on 429 responses without dropping the cycle
- [ ] **COLL-05**: Collector stores parent IDs and thread relationships so replies to Butter's replies are linked to their thread and never mistaken for fresh top-level comments
- [ ] **COLL-06**: Butter's own outbound comments are filtered at ingestion by account ID, never enter the drafting queue, and mark the parent comment as already handled
- [ ] **COLL-07**: When credentials expire or auth fails, collection pauses with a loud, distinct status (never "no new comments") and the UI shows the last successful sync time
- [ ] **COLL-08**: Collector records whether a thread received further audience activity after a Butter reply, so audience response can be measured separately from Butter's own replies
- [ ] **COLL-09**: After the app was stopped or the machine slept, the collector resumes from saved checkpoints and collects the backlog

### Post Briefs

- [ ] **BRIEF-01**: App builds one brief per post from caption and date, image or carousel content including readable text, sampled timestamped video frames, a transcript (supplied transcript preferred, whisper.cpp fallback behind an interface when available), apparent topic, tone, joke, question or announcement, confirmed facts, source references and missing context
- [ ] **BRIEF-02**: User can view and edit a post brief in the UI; each edit increments the brief version
- [ ] **BRIEF-03**: Brief stores confirmed facts separately from inferred intent, and the drafter can only assert claims from confirmed facts
- [ ] **BRIEF-04**: When media is unavailable or unprocessed, the brief shows context status incomplete or caption-only, every draft under that post is forced to review, and no draft is ever described as having understood the video
- [ ] **BRIEF-05**: A post's media is processed once and the brief reused for every comment; re-analysis happens only when the caption, source facts or brief changes
- [ ] **BRIEF-06**: A brief version bump invalidates every unsent draft under that post and surfaces them for regeneration
- [ ] **BRIEF-07**: Brief carries a sensitivity flag for do-not-cover topics (murder, violent crime, shootings, stabbings, random tragedy) that forces every comment on that post into human review

### Triage and Drafting

- [ ] **DRAFT-01**: Every eligible comment receives exactly one of four outcomes: draft, hold for review, skip, already handled, classified by purpose, never by sentiment
- [ ] **DRAFT-02**: Cheap deterministic filters (own reply, already answered, empty or emoji-only, paused post, limits exhausted, older than oldest monitored date) run before any model call
- [ ] **DRAFT-03**: Drafts are generated in the background before review, and the drafting request receives the current voice rules, post brief, pertinent thread, a few tag-matched curated examples, approved facts when needed, and recent replies under that post to discourage repetition
- [ ] **DRAFT-04**: Model output is validated against a strict schema (decision, draft_text, category, reason, facts_used, missing_context, review_flags, post_brief_version, voice_version) before saving; invalid output routes the comment to Needs attention with a "model output invalid" flag and the scrubbed raw output is logged
- [ ] **DRAFT-05**: No model-reported field (decision, confidence) can authorize publishing; only app-level gates outside the model do
- [ ] **DRAFT-06**: Comment, thread, transcript and external text are passed as delimited data, the drafter has no tool or function access, and an instruction-injection fixture proves a comment cannot change voice rules, read secrets or trigger a send
- [ ] **DRAFT-07**: A per-comment sensitivity check holds for review any comment involving do-not-cover topics, allegations, tragedies, sponsor issues, disputes, ambiguous jokes or missing facts, even under an otherwise eligible post
- [ ] **DRAFT-08**: A facts cross-check flags any draft containing specifics (attendance, relationships, experiences, endorsements, dates, names, numbers) not traceable to facts_used, the brief or the thread
- [ ] **DRAFT-09**: A repetition check flags any draft that repeats a joke or phrasing already used by Butter under the same post

### Voice, Examples and Knowledge

- [ ] **VOICE-01**: Voice rules are editable in the UI, versioned, and seeded from the Butter standing rules (no emojis, no em dashes, no "let me know" closers, no filler or robot language, no lazy contrast phrasing, no forced slang, no mandatory question, no invented experiences, hashtag and Capture the Flag ATL wording rules, 404 Day kept separate from partnership talk)
- [ ] **VOICE-02**: User can add, tag, edit and retire examples; approved examples are kept distinct from unreviewed outputs, and selection uses tags plus local text search only (no vector DB, no training)
- [ ] **VOICE-03**: User can promote an edited or approved reply into the example library with tags in one action from the inbox
- [ ] **VOICE-04**: User can manage knowledge entries (fact text, category, source, validity dates, reviewer); expired facts are excluded from prompts
- [ ] **VOICE-05**: User can store negative examples labeled as bad output (engagement bait, forced question, invented anecdote) that are used contrastively in drafting

### Review Inbox

- [ ] **REVIEW-01**: User reviews on one screen showing the post (creative, caption, brief, context status), the comment, the thread, the editable draft, facts_used, missing_context and review flags together
- [ ] **REVIEW-02**: User can Approve and send, Edit, Regenerate, Skip, Hold, and Pause post from that screen
- [ ] **REVIEW-03**: Drafts are organized in Ready, Needs attention, Sent and Skipped queues, and system problems (connection failure, uncertain send, invalid model output, auth expiry) are visibly distinct from content holds
- [ ] **REVIEW-04**: User can batch approve selected items, and an item can only be selected after its draft text has been expanded and visible
- [ ] **REVIEW-05**: Approval stores the exact approved text, its hash, reviewer, timestamp, brief version and voice version; any edit, regeneration or brief/voice version change invalidates the approval and returns the item to review
- [ ] **REVIEW-06**: UI uses Butter tokens (yellow #EFB82E as the only yellow, Inter body, Space Mono utility, system display font fallback), contains no emojis or em dashes in copy, and shows the MOCK badge whenever MockConnector is active

### Sending

- [ ] **SEND-01**: Only one sender function can publish; it accepts a draft ID and approved text hash, refuses if the draft is not approved, invalidated, or the hash does not match, and never reads unapproved draft text
- [ ] **SEND-02**: Immediately before sending, the sender rechecks that the comment still exists, is still eligible, its post is not paused, and it has not already been answered by Butter in-app or on Instagram
- [ ] **SEND-03**: Each outbound task is locked with an owner before sending, stale locks are reclaimable after a timeout, and the idempotency key derived from draft ID plus hash prevents a duplicate send across retries and restarts
- [ ] **SEND-04**: On success the returned reply ID is persisted with the task and the item moves to Sent
- [ ] **SEND-05**: After a timeout or ambiguous response the task is marked uncertain, the thread is reconciled before any retry, and an unresolved reconciliation holds the item for review
- [ ] **SEND-06**: Auth failures, rate limits and permanent errors are distinct states with distinct handling: auth pauses sending and flags credentials, rate limit requeues with backoff, permanent error holds for review
- [ ] **SEND-07**: Daily send limit, per-post limit, interaction depth limit and global pause are enforced by app code outside the model, checked at triage and again at send, and global pause stops all drafting and sending instantly

### Audit and Recap

- [ ] **AUDIT-01**: User can view and filter an append-only activity log of every state transition (draft created, edited, approved, invalidated, sent, held, skipped, error) with actor, timestamps, from and to state, and the original versus approved text
- [ ] **AUDIT-02**: User can view a local daily recap of sent, held, skipped, errors and audience follow-ups, in which auth failures are never presented as a quiet day and sent counts always appear beside quality context

### Evaluation

- [ ] **EVAL-01**: User can build a baseline sample (about 100 comments across about 10 varied posts) from collected data and label each comment respond, skip or needs judgment in the UI or by CSV import
- [ ] **EVAL-02**: User can view a coverage report comparing system decisions with the labels, listing missed opportunities and inappropriate selections
- [ ] **EVAL-03**: User can view a quality report with the proportion of drafts sent without substantive edits, parse-failure rate, reviewer-tagged factual and context errors, invented-experience rate, repetition rate, forced-question rate and voice mismatches
- [ ] **EVAL-04**: User can view a trust report with unapproved sends (must be zero), duplicate replies, out-of-scope holds and error counts
- [ ] **EVAL-05**: User can export review-action timestamps and per-item handling time to support the workload comparison
- [ ] **EVAL-06**: User can view audience response (conversations continued after a Butter reply) reported separately from Butter's own reply count
- [ ] **EVAL-07**: An automated acceptance suite covers duplicate delivery, a reply made directly in Instagram, a deleted comment, an expired token, a paused post, an uncertain send timeout and an instruction-injection comment, and proves unapproved text cannot publish
- [ ] **EVAL-08**: A "Needs a human" runbook documents every live verification step that cannot run in the build container: Meta app and scope setup, one real authorized read, one authorized test send, hardware and model selection for Ollama, ffmpeg/whisper.cpp/keyring checks, and the 100-comment evaluation with Brandon's labels

### Scoped Automation

- [ ] **AUTO-01**: Automation is OFF by default; enabling it requires explicit per-category and post-eligibility settings and is visible on every screen
- [ ] **AUTO-02**: Only two candidate categories exist: uncomplicated acknowledgments, and questions answered explicitly by a current approved fact; sentiment is never an eligibility input
- [ ] **AUTO-03**: Eligibility is evaluated per comment using post flags and comment content, never post level alone; do-not-cover posts, ambiguous jokes, allegations, tragedies, sponsor issues, disputes and missing facts always stay in review
- [ ] **AUTO-04**: A category can only be enabled when the evaluation report records that its quality bar was met, a configurable interaction limit applies, and global pause disables automation instantly
- [ ] **AUTO-05**: Auto-sent items are marked distinctly in the Sent queue, the activity log and the daily recap

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Platform Extensions

- **PLAT-01**: TikTok connector behind the same Connector interface, after TikTok access is separately confirmed
- **PLAT-02**: Webhook-based comment ingestion as an optimization once eligibility is confirmed, never removing the polling fallback

### Model Options

- **MODEL-01**: Optional cloud LLM fallback behind the LLM client interface, only after smaller model, shorter context and fewer concurrent jobs have been tried
- **MODEL-02**: Broader automation categories after specific situations demonstrate quality

### Convenience

- **CONV-01**: Configurable recap delivery (local notification) beyond the in-app recap page
- **CONV-02**: Bulk example import from historical Butter replies with reviewer approval

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Scheduling posts or generating feed content | Reply tool, not a publishing tool (brief boundary) |
| Cold outreach, automated DMs, comment-to-DM, sales funnels | Brief boundary; different trust risk profile |
| Customer service platform or CRM commenter profiles | Unrelated to coverage, quality, workload or control |
| Automatic deletion or hiding of audience comments | Brief forbids it; delete endpoint is not implemented at all |
| Answering every comment or maximizing reply count | Leaving a comment alone is a valid editorial decision |
| Sentiment-driven eligibility or engagement bait | Positive sentiment alone never makes a reply eligible |
| Vector DB, embeddings or model fine-tuning | Brief requires tags plus local text search only |
| Multi-account or multi-platform unified inbox | Instagram only for v1; interface stays extensible |
| Always-on public webhook server in v1 | Polling baseline; 127.0.0.1-only design |
| Cloud LLM as baseline | No required paid services |
| Inventing personal experiences or relationships for Brandon | Voice rule and facts cross-check enforce this |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Pending |
| FOUND-05 | Phase 1 | Pending |
| FOUND-06 | Phase 1 | Pending |
| CONN-01 | Phase 1 | Pending |
| CONN-02 | Phase 1 | Pending |
| CONN-03 | Phase 1 | Pending |
| CONN-04 | Phase 1 | Pending |
| CONN-05 | Phase 1 | Pending |
| COLL-01 | Phase 2 | Pending |
| COLL-02 | Phase 2 | Pending |
| COLL-03 | Phase 2 | Pending |
| COLL-04 | Phase 2 | Pending |
| COLL-05 | Phase 2 | Pending |
| COLL-06 | Phase 2 | Pending |
| COLL-07 | Phase 2 | Pending |
| COLL-08 | Phase 2 | Pending |
| COLL-09 | Phase 2 | Pending |
| BRIEF-01 | Phase 2 | Pending |
| BRIEF-02 | Phase 2 | Pending |
| BRIEF-03 | Phase 2 | Pending |
| BRIEF-04 | Phase 2 | Pending |
| BRIEF-05 | Phase 2 | Pending |
| BRIEF-06 | Phase 2 | Pending |
| BRIEF-07 | Phase 2 | Pending |
| DRAFT-01 | Phase 3 | Pending |
| DRAFT-02 | Phase 3 | Pending |
| DRAFT-03 | Phase 3 | Pending |
| DRAFT-04 | Phase 3 | Pending |
| DRAFT-05 | Phase 3 | Pending |
| DRAFT-06 | Phase 3 | Pending |
| DRAFT-07 | Phase 3 | Pending |
| DRAFT-08 | Phase 3 | Pending |
| DRAFT-09 | Phase 3 | Pending |
| VOICE-01 | Phase 3 | Pending |
| VOICE-02 | Phase 3 | Pending |
| VOICE-03 | Phase 3 | Pending |
| VOICE-04 | Phase 3 | Pending |
| VOICE-05 | Phase 3 | Pending |
| REVIEW-01 | Phase 3 | Pending |
| REVIEW-02 | Phase 3 | Pending |
| REVIEW-03 | Phase 3 | Pending |
| REVIEW-04 | Phase 3 | Pending |
| REVIEW-05 | Phase 3 | Pending |
| REVIEW-06 | Phase 3 | Pending |
| SEND-01 | Phase 4 | Pending |
| SEND-02 | Phase 4 | Pending |
| SEND-03 | Phase 4 | Pending |
| SEND-04 | Phase 4 | Pending |
| SEND-05 | Phase 4 | Pending |
| SEND-06 | Phase 4 | Pending |
| SEND-07 | Phase 4 | Pending |
| AUDIT-01 | Phase 4 | Pending |
| AUDIT-02 | Phase 4 | Pending |
| EVAL-01 | Phase 5 | Pending |
| EVAL-02 | Phase 5 | Pending |
| EVAL-03 | Phase 5 | Pending |
| EVAL-04 | Phase 5 | Pending |
| EVAL-05 | Phase 5 | Pending |
| EVAL-06 | Phase 5 | Pending |
| EVAL-07 | Phase 5 | Pending |
| EVAL-08 | Phase 5 | Pending |
| AUTO-01 | Phase 5 | Pending |
| AUTO-02 | Phase 5 | Pending |
| AUTO-03 | Phase 5 | Pending |
| AUTO-04 | Phase 5 | Pending |
| AUTO-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 69 total
- Mapped to phases: 69
- Unmapped: 0

---
*Requirements defined: 2026-09-25*
*Last updated: 2026-09-25 after roadmap creation*
