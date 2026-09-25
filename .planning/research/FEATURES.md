# Feature Research

**Domain:** AI comment-reply assistant for a brand's own Instagram posts (single-operator, local-first, approval-first)
**Researched:** 2026-09-25
**Confidence:** MEDIUM (reference-product features verified via current vendor marketing/help pages, MEDIUM confidence per source-hierarchy rules since these are vendor-authored, not independently audited; brief's own requirements are HIGH confidence as primary source)

Every feature below is tagged with which of the brief's four value dimensions it serves: **Coverage** (worthwhile comments answered), **Quality** (reply fits post/voice), **Workload** (Brandon's hands-on minutes), **Control** (Brandon's visibility/authority over what publishes). A feature with no clear tag is a candidate for deferral per the brief ("features without that connection should be deferred").

## Feature Landscape

### Table Stakes (Users Expect These)

Features users (Brandon, evaluating this against NapoleonCat/BrandBastion mental models) assume exist. Missing these makes the product feel incomplete or unsafe to use.

| Feature | Why Expected | Complexity | Notes | Value dims |
|---------|--------------|------------|-------|------------|
| Comment collection/sync from owned posts | Both references center on "see all comments in one place." Without it there's no product. | MEDIUM | Scheduled polling per brief (webhooks later); pagination, checkpoints, backoff. | Coverage |
| Post-aware context (caption + creative, not just comment text) | Both NapoleonCat and BrandBastion explicitly analyze the post (image/video/caption), not just the comment string — this is the difference between a generic reply and a correct one. | HIGH | Brief calls for one-time post brief: caption, image/carousel OCR, video frames, transcript, confirmed facts. Reuse cached brief across comments on that post. | Quality |
| Draft-before-review (pre-generated suggestions, not generate-on-click) | BrandBastion's differentiator over older tools ("workflows prepare drafts before you open the queue") is now the baseline expectation; brief explicitly requires "prepare drafts in the background." | MEDIUM | Draft generation runs async on a schedule, not on comment-click. | Workload |
| Human approval before send (approve/edit/regenerate/skip) | Both products support this; brief mandates it as default mode. Non-negotiable for trust-building. | MEDIUM | Actions: Approve+send, Edit, Regenerate, Skip, Hold, Pause post per brief. | Control |
| Single review screen with post + thread + draft together | NapoleonCat/BrandBastion both surface comment + context together; reviewing comments with no post context is unusable for a voice-sensitive brand. | MEDIUM | Brief specifies "post beside comment, thread and editable draft." | Workload, Quality |
| Voice/brand-tone conditioning from examples and rules | Core promise of both products — NapoleonCat "learns from how you reply," BrandBastion "follows your tone, phrasing" — and the brief's central differentiator concern (Butter's voice must not be generic). | MEDIUM-HIGH | Brief: store voice rules separately from example bank; tag + local text search for example retrieval, no vector DB. | Quality |
| Spam/irrelevant-comment filtering (skip, don't just draft everything) | Both competitors triage before drafting (spam/hate/negative-sentiment detection). Drafting on every comment wastes Brandon's review time and risks bad output. | MEDIUM | Brief's 4-way classification: draft / hold for review / skip / already handled. | Coverage, Workload |
| Thread/reply-context awareness (don't duplicate, don't miss existing reply) | Both products track thread state to avoid double-replying; brief requires checking "already handled" and pre-send reconciliation. | MEDIUM | Needs parent/child comment IDs, dedupe against Butter's own outbound comments. | Quality, Control |
| Activity log / audit trail of what was sent | Baseline trust requirement once a tool can publish text under the brand's name; both competitors report performance/actions. Brief requires "visible record." | LOW-MEDIUM | Exact approved text stored, tied to draft version and reply ID. | Control |
| Rate/volume limiting on outbound sends | Both products operate within platform rate constraints; brief specifies daily/per-post limits and global pause enforced outside the model. | LOW | Simple counters + kill switch. | Control |
| Reliable single-send guarantee (no duplicate publish) | Table stakes for any tool that writes to a live public surface; brief calls out locking, reconciliation, idempotency explicitly as an acceptance check. | MEDIUM-HIGH | Lock outbound task, persist reply ID, reconcile on timeout. | Control |

### Differentiators (Competitive Advantage / Fit for Brief)

Features that set this build apart from a generic clone of NapoleonCat/BrandBastion — valuable specifically because of the brief's constraints (single operator, no subscription cost, voice-sensitive niche brand, approval-first-then-scoped-autonomy).

| Feature | Value Proposition | Complexity | Notes | Value dims |
|---------|-------------------|------------|-------|------------|
| Media-grounded post brief (video frames + transcript + OCR) reused across a post's comment set | Neither reference product's media handling is well-documented publicly ("not established" for NapoleonCat); BrandBastion's is a paid black box. Doing this locally and cheaply, and treating it as a versioned artifact that invalidates drafts when it changes, is more rigorous than typical SaaS behavior and directly targets Butter's "did it understand the joke" quality bar. | HIGH | This is the single highest-quality-leverage feature in the brief; it is also the highest technical risk (local vision/audio models on unknown hardware). | Quality |
| Explicit "missing context" / confidence flagging instead of silent guessing | Competitors optimize for coverage/volume; the brief explicitly rejects a "caption-only draft described as having understood the video." This is a deliberate anti-competitor stance: slower, more honest triage over broad auto-drafting. | LOW-MEDIUM | Structured output field `missing_context`; UI must surface it, not bury it. | Quality, Control |
| Example-promotion loop (approved edits become new examples) | NapoleonCat retrieves historical examples automatically; the differentiator here is a manual curation step Brandon controls, keeping the example bank small, high-quality, and untrained (no model fine-tuning, no vector DB) — cheaper and more auditable than SaaS "AI learns from your replies" black boxes. | LOW-MEDIUM | Directly serves the "no training, no vector DB" cost/complexity constraint while still improving over time. | Quality, Workload |
| Untrusted-input isolation (comments/transcripts cannot alter voice rules, secrets, or trigger sends) | Neither competitor documents prompt-injection defenses publicly. Given a public comment section is adversarial input by design, treating all scraped text as data-only (never instructions) is a differentiator specific to a single local build done carefully rather than a SaaS feature checklox. | MEDIUM | Brief calls this out explicitly as an acceptance test ("instruction-injection comment"). | Control |
| Scoped, category-based automation graduation (not all-or-nothing auto-send) | BrandBastion offers "selective automation for exact phrase matches" as a paid add-on; the brief's design goes further by making per-category, per-post-eligibility automation the core trust-building mechanism from day one, with quality-gated graduation rather than a toggle. | MEDIUM-HIGH | Depends on Table Stakes approval flow + logged outcomes to have evidence to graduate categories. | Control, Workload |
| Zero recurring cost / local-only operation | Both reference products are paid SaaS (BrandBastion pricing starts high per public comparison sources). A local Ollama-based pipeline with no per-request billing is a structural differentiator for a solo operator, not a feature copy. | HIGH (infra risk, not product risk) | Contingent on hardware; brief treats this as unproven until validated. | Workload (cost is a workload/resource proxy per brief) |
| Baseline-labeling and coverage/quality/workload measurement harness | Neither competitor publishes a rigorous human-labeled baseline methodology; this is specific to how the brief wants success judged, not a market feature. Necessary for evaluation, not for the product experience itself, but essential for the project. | MEDIUM | See "Evaluation/baseline features" section below — required by downstream requirements process. | Coverage, Quality, Workload (as measurement, not runtime feature) |
| Daily local activity recap (sent/held/errors) | Small feature, high trust value for a single operator who isn't going to open the app constantly; recap gives passive control without babysitting. | LOW | Brief specifies this explicitly. | Control, Workload |

### Anti-Features (Commonly Requested, Often Problematic — Out of Scope Per Brief)

| Anti-Feature | Why It Looks Appealing (seen in references) | Why Problematic Here | Alternative |
|--------------|-------------------------------------------|----------------------|-------------|
| Full auto-send / "AI workflows can also auto-send" (BrandBastion) | Removes Brandon's review bottleneck entirely; competitor offers it as a selling point. | Brief explicitly: "does not yet trust unrestricted publishing," start in review mode always. Auto-send-everything also risks voice mismatch and the do-not-cover categories (tragedy, disputes) going out unreviewed. | Category-scoped automation only after demonstrated quality per category (Differentiator above). |
| Comment-to-DM automation / lead capture (NapoleonCat, BrandBastion) | Both competitors treat this as a monetization/lead-gen feature and market it heavily. | Brief boundary: "no automated DMs... no sales funnels." Explicitly out of scope for v1 and possibly ever. | Public replies only; DMs stay manual/human. |
| Auto-hide/auto-delete of audience comments (both competitors, core moderation feature) | Looks like "the same tech, just point it at deletion instead of reply" — appears cheap to add once you have sentiment/spam classification. | Brief explicitly forbids "automatic deletion of audience comments." Deleting real audience speech is a much higher-trust action than replying and not requested. | Flag/skip only; leave moderation/deletion to Instagram's native tools or Brandon manually. |
| Answer every comment / maximize response rate as a KPI | Coverage-maximizing instinct, and both competitors implicitly sell "handle comments at scale." | Brief explicitly: "objective is not to answer every comment... Leaving a comment alone is an acceptable editorial decision." Maximizing volume creates filler and engagement bait. | Coverage metric is worthwhile-comments-answered, not all-comments-answered; skip is a first-class outcome. |
| Sentiment-score-driven engagement bait (reply to boost engagement stats) | Vanity-metric appeal; easy to build once sentiment tagging exists. | Brief explicitly forbids "manufactured arguments and engagement bait" and states "positive sentiment alone never makes a reply eligible." | Classify by purpose (question/joke/ack), not sentiment. |
| Cross-platform unified inbox (Facebook, TikTok ads, multi-account) from day one | Both competitors sell multi-channel as core value ("Facebook, Instagram, TikTok ads in one dashboard"). | Brief scope: Instagram first, TikTok only as a later, separately-confirmed adapter; multi-account is not Butter's situation (single brand, single operator). Building generic multi-tenant/multi-platform abstractions now is premature complexity. | Instagram-only adapter; design the account-adapter interface to be extensible, but do not build other adapters yet. |
| Vector-DB/fine-tuned voice model | Appears to be "the modern way" to do retrieval-augmented voice matching; NapoleonCat's "learns from your replies" implies something like this. | Brief explicitly: "no vector DB, no training." Adds infra weight, cost, and opacity disproportionate to a small curated example set. | Tags + local text search over a small, human-curated example bank. |
| Scheduling/publishing new feed content, content calendar | Natural adjacent feature for a "social management" tool (this is NapoleonCat/BrandBastion's whole other product line). | Brief boundary: no scheduling posts, no feed content generation. This is a reply tool, not a publishing tool. | None — explicitly out of scope. |
| Customer-service ticketing / CRM-style commenter profiles (NapoleonCat "Social CRM") | Looks valuable for continuity and looks like "professionalizing" the tool. | Brief boundary: not a customer service platform. Adds scope (identity resolution, history UI, SLAs) unrelated to the four value dimensions. | Keep author ID/history only as much as needed for context and dedupe, not as a CRM feature. |
| Always-on public webhook server for real-time comment ingestion | Feels like the "proper" real-time architecture competitors use. | Brief explicitly starts with scheduled polling while the app is running, webhooks later; an always-public server contradicts the local/127.0.0.1-bound, no-added-cost design and adds security surface disproportionate to a single-operator tool. | Scheduled API pulls, frequency scaled to post activity; revisit webhooks only after Standard Access/webhook eligibility is confirmed. |

## Feature Dependencies

```
Account adapter (real IG read) [prerequisite, not itself a "feature"]
    └──requires──> Comment collection/sync
                       └──requires──> Post-aware context (post brief, cached/versioned)
                                          └──requires──> Draft-before-review generation
                                                             ├──requires──> Voice/brand-tone conditioning (examples + rules)
                                                             └──requires──> Thread/reply-context awareness (dedupe, "already handled")
                                                                                └──requires──> Single review screen
                                                                                                   └──requires──> Human approval before send
                                                                                                                      └──requires──> Reliable single-send guarantee (locking, reconciliation)
                                                                                                                                         └──requires──> Activity log / audit trail
                                                                                                                                         └──requires──> Rate/volume limiting

Example-promotion loop ──enhances──> Voice/brand-tone conditioning
Missing-context flagging ──enhances──> Post-aware context (surfaces its own gaps)
Baseline-labeling harness ──validates──> Coverage/Quality/Workload metrics (independent of runtime pipeline; needs only a comment/post sample + human labels, can start before drafting works)
Scoped automation graduation ──requires──> Human approval before send (needs an approval history to graduate from)
                              ──requires──> Activity log / audit trail (needs outcome evidence)
Untrusted-input isolation ──conflicts with──> any design where model output fields (e.g. "confidence") gate sending directly — brief requires a separate app-level gate always
Daily activity recap ──requires──> Activity log / audit trail
Auto-send-everything (anti-feature) ──conflicts──> Human approval before send (do not build both; the brief resolves this conflict in favor of approval-first with scoped, evidence-gated exceptions)
```

### Dependency Notes

- **Post-aware context requires Comment collection**, because a post brief is only worth building once you know which posts have live comment activity to prioritize; the brief also says "process a post's media once and reuse the brief" — so this artifact must exist and be versioned before drafting starts.
- **Draft-before-review requires Post-aware context + Voice conditioning**, since a draft with no post brief or no voice rules is exactly the generic-brand-voice failure mode the brief is built to avoid.
- **Thread-awareness requires collection with parent/child IDs** stored from the start; retrofitting dedupe after the fact against Instagram's own reply state is much harder.
- **Reliable single-send guarantee requires Human approval** to exist first (there's nothing to send reliably until there's an approved draft), but is itself a hard prerequisite for enabling any Scoped automation later — sending only becomes safe to run less-supervised once retries/locking/reconciliation are solid.
- **Scoped automation graduation requires an Activity log with outcome data** — the brief is explicit that autonomy expands "based on observed quality," so there is no path to automation without an audit trail to measure against.
- **Baseline-labeling harness is independent of the runtime pipeline** — it needs a sample of real posts/comments and Brandon's human judgments, not a working drafting system. It can and should start early (parallel to or even before collector/drafting work) because Coverage and Quality metrics are defined relative to it.
- **Untrusted-input isolation conflicts with any shortcut where a model-reported field authorizes sending** — this is a hard architectural rule from the brief ("Model self-reported confidence is not publishing permission"), not a soft preference; any feature design that lets model output directly gate sending must be rejected regardless of convenience.

## MVP Definition

### Launch With (v1)

Minimum to validate the concept per the brief's own build order (acceptance checks 1-4).

- [ ] Real Instagram read connection (account adapter, documented permissions) — nothing else works without it
- [ ] Persistent comment collector with checkpoints, thread IDs, dedupe of Butter's own comments
- [ ] Cached, versioned post brief (caption + creative interpretation + confirmed facts), reused per post
- [ ] Draft generation with editable voice rules + curated examples + thread context, structured output with confidence/flag fields
- [ ] 4-way classification (draft / hold / skip / already handled)
- [ ] Single review screen (post + thread + editable draft, approve/edit/regenerate/skip/hold/pause post)
- [ ] Reliable send path (pre-send recheck, lock, reply-ID persistence, reconciliation, distinct error classes)
- [ ] Activity log / audit trail of sent, edited, held items
- [ ] App-level daily/per-post limits and global pause
- [ ] Mock connector clearly labeled MOCK for local dev (build-environment constraint)

### Add After Validation (v1.x)

Trigger: the ~100-comment / 10-post evaluation (acceptance check 5) produces usable coverage/quality/workload numbers and the core loop is stable.

- [ ] Example-promotion loop (promote an edited reply into the curated example bank) — trigger: enough approved/edited drafts exist to be worth curating
- [ ] Daily activity recap — trigger: Brandon is checking the log manually often enough that a digest saves time
- [ ] Scoped, category-based automation (uncomplicated acknowledgments, explicitly-sourced Q&A) — trigger: logged quality in those categories meets an agreed bar
- [ ] Webhook-based monitoring — trigger: Standard Access/webhook eligibility confirmed AND polling proves too slow/costly for activity levels observed
- [ ] Configurable interaction limit tuning based on observed volume

### Future Consideration (v2+)

Defer until the Instagram approval-first loop has proven itself.

- [ ] TikTok adapter — brief: "subsequent adapter requiring separate confirmation," explicitly not v1
- [ ] Broader automation categories beyond the initial safe set — defer until specific situations (not just elapsed time) demonstrate quality
- [ ] Any cloud-model fallback for quality/speed — brief: "optional, not baseline," only if local models prove insufficient after cheaper mitigations (smaller model, shorter context, fewer concurrent jobs) are tried first

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Real IG read connection | HIGH | MEDIUM | P1 |
| Comment collector (checkpoints, threading) | HIGH | MEDIUM | P1 |
| Post-aware context (post brief, media) | HIGH | HIGH | P1 |
| Voice/brand-tone conditioning | HIGH | MEDIUM | P1 |
| Draft-before-review generation | HIGH | MEDIUM | P1 |
| 4-way classification (draft/hold/skip/handled) | HIGH | MEDIUM | P1 |
| Single review screen + approval actions | HIGH | MEDIUM | P1 |
| Reliable single-send guarantee | HIGH | HIGH | P1 |
| Activity log / audit trail | MEDIUM | LOW | P1 |
| Rate/volume limits + pause | MEDIUM | LOW | P1 |
| Baseline-labeling harness / eval metrics | HIGH | MEDIUM | P1 |
| Missing-context flagging | MEDIUM | LOW | P1 |
| Untrusted-input isolation | HIGH (risk mitigation) | MEDIUM | P1 |
| Example-promotion loop | MEDIUM | LOW | P2 |
| Daily activity recap | LOW-MEDIUM | LOW | P2 |
| Scoped category automation | HIGH (long-run workload) | HIGH | P2 |
| Webhook monitoring | LOW (polling suffices at Butter's scale) | MEDIUM | P3 |
| TikTok adapter | MEDIUM | HIGH | P3 |
| Cloud-model fallback | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch (acceptance checks 1-6)
- P2: Should have, add when v1 loop is validated
- P3: Nice to have, future consideration (v2+, separately confirmed)

## Competitor Feature Analysis

| Feature | NapoleonCat | BrandBastion Agent+ | Butter design |
|---------|--------------|--------------|--------------|
| Draft generation | Click-to-generate suggestion, learns from past replies + FAQs/help docs | Pre-drafted queue ready on open ("thousands of ... responses"), post-aware (caption, audio, video/image) | Background drafting on a schedule; post brief built once, reused across that post's comments |
| Context sources | Comment history, FAQs/help articles | Post analysis (caption/audio/video/image) + help center/site/product data | Cached post brief + thread + approved facts + curated Butter examples; explicit missing-context flag |
| Media handling | Not documented publicly | Image/video/audio interpretation as part of post analysis (paid, opaque) | Explicit local pipeline: OCR, frame sampling, transcript (existing transcripts preferred, whisper.cpp fallback); brief unavailable = forced review, never silently guessed |
| Approval | Edit → regenerate → send per comment | Batch approval (clear hundreds at once); selective auto-send for exact-phrase matches | Approval by default; explicit per-category settings for later scoped automation; approval invalidated by any edit/regeneration/context change |
| Voice/tone | Retrieves relevant historical examples at draft time (implicit "learning") | Configurable prompts/tone rules, escalation rules | Voice rules stored separately from facts; small curated, tag-searchable example bank; promotion workflow for good edited replies; explicitly no training, no vector DB |
| Moderation (hide/delete spam) | Full auto-hide/delete with sentiment+spam detection, 24/7 | Auto-removal of harmful comments, 20+ risk categories, 100+ languages | Out of scope — no auto-delete/hide of audience comments (brief boundary); flag/skip only |
| DM/lead capture | Comment-to-DM automation | Purchase-intent detection → move to DM with offers | Out of scope — no automated DMs (brief boundary) |
| Multi-channel | FB, Instagram, TikTok ads in one dashboard | Paid, organic, and private messages across channels | Instagram only for v1; TikTok deferred and separately confirmed |
| Cost model | Paid SaaS subscription (tiered) | Paid SaaS, public comparisons cite high entry pricing (~$800+/mo range per third-party comparison source, unverified) | Local-only, no required subscription; cloud model optional fallback, not baseline |
| Reporting | Volume, response time, moderator performance dashboards | Sentiment tracking at post/campaign/brand level, real-time risk alerts | Minimal: activity log + daily recap + the brief's specific coverage/quality/workload/trust metrics from human-labeled baseline (not vanity dashboards) |

## Evaluation / Baseline-Labeling Features (feeds success criteria directly)

These are required by the brief's "How we will judge success" section and are prerequisites for the downstream requirements/roadmap work, not optional extras:

- **Sample selection tooling**: pull ~100 real comments across ~10 varied Butter posts for the baseline sample. LOW complexity (reuses the collector), but needs to run before or alongside drafting features.
- **Human-labeling interface/record**: let Brandon mark each sampled comment as respond / skip / needs-judgment, forming the reference set. Can be a minimal form or even a spreadsheet-backed table for v1 — LOW complexity, but the *data model* for it (a label distinct from the system's own decision) must exist so system output can be diffed against it.
- **Coverage measurement**: worthwhile-comments-answered ÷ worthwhile-comments-in-sample, against the human labels, including false negatives (missed) and false positives (wrongly selected). Depends on the labeling record + the system's own decision log.
- **Workload measurement**: hands-on minutes comparison (manual vs. tool-assisted), including setup/maintenance time — this is closer to a timed-observation practice than a software feature, but the app should make timestamps of review actions available to support it.
- **Quality measurement**: proportion of drafts sent without substantive edits, plus tracked factual/context errors, repetition, and voice mismatches — depends on the Activity log capturing both the original draft and the final approved text (diffable).
- **Trust measurement**: unapproved sends (should be zero by construction), duplicate replies, visibility, and out-of-scope handling — depends on the Activity log and the reliable-send guarantee's error/reconciliation records.

These evaluation features are Coverage/Quality/Workload-tagged by definition (they measure those dimensions) and should be scoped into the same phase as the core P1 loop, not deferred, since the brief's acceptance check 5 requires them before any automation graduation (check 7).

## Sources

- Butter.ATL Comment Assistant Brief (`.planning/BRIEF.md`) — HIGH confidence, primary source for all constraints, boundaries, and value-dimension framing
- NapoleonCat, "Instagram Comment Moderation Tool" — https://napoleoncat.com/uses/instagram-comment-moderation-tool/ — MEDIUM confidence (vendor marketing page, fetched 2026-09-25)
- NapoleonCat, general product/marketing pages (auto-hide, auto-commenting AI, comment-to-DM) — https://napoleoncat.com/ — MEDIUM confidence, WebSearch summary
- BrandBastion, "Agent+" — https://www.brandbastion.com/agent — MEDIUM confidence (vendor marketing page, fetched 2026-09-25)
- BrandBastion, "Social Media Moderation" — https://www.brandbastion.com/social-media-moderation — MEDIUM confidence, WebSearch summary
- replient.ai, "BrandBastion alternative" comparison (pricing reference only, unverified) — LOW confidence, single third-party source, not independently confirmed
- All competitor features are MEDIUM confidence at best (vendor-authored marketing copy, not independently audited or tested); no claim from these sources is used as a hard requirement, only as market context for table-stakes/differentiator judgment calls, which remain governed by the brief's own stated priorities.

---
*Feature research for: AI comment-reply assistant (Butter.ATL)*
*Researched: 2026-09-25*
