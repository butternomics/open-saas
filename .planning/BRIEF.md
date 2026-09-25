# Butter.ATL Comment Assistant: Product and Build Brief

Prepared September 25, 2026. Source idea document for GSD (`/gsd:new-project --auto @.planning/BRIEF.md`).

## The problem we are solving

Butter.ATL receives audience comments on its posts, but Brandon does not consistently have time to read the surrounding context, decide what deserves a response, write an appropriate reply, and follow the conversation. As a result, opportunities to acknowledge people, answer questions, join jokes and continue discussions go unanswered.

The bottleneck is the time and attention needed to participate after publishing. Brandon wants Butter to engage more consistently without hiring a social media manager or adding another paid social management subscription. He wants to review responses initially and move toward autonomous handling as the system earns his trust, while retaining visibility into what it says.

The volume of eligible comments, current response rate and time required have not yet been measured.

## Why this matters specifically for Butter.ATL

Butter is Atlanta's culture channel. Its comment sections are a place for local references, humor, opinions, questions and shared experiences. A useful reply needs to fit both what Butter posted and what the commenter actually means. An interchangeable brand response can miss the joke or weaken the voice people recognize.

The business intent is to turn existing audience participation into more two-way conversation and a stronger relationship with Butter. The hoped-for benefits are more people continuing conversations and returning to participate. Those are outcomes to test, not guaranteed increases in reach, followers, revenue or algorithmic distribution.

Avoiding added software costs is a constraint on the solution. The purpose is consistent, worthwhile audience engagement with less work for Brandon.

## Product objective

Help Butter.ATL participate in more worthwhile conversations under its own posts, with responses that understand the content and sound like Butter, while reducing the effort required from Brandon and preserving his control.

User job: When comments arrive on a Butter post, identify conversations worth joining, understand the post and thread, and prepare an appropriate response so Brandon can quickly approve it. Over time, handle demonstrated routine situations automatically and surface the exceptions that need his judgment.

## Requirements that keep the build focused

| User need | Required behavior | Evidence that it works |
| --- | --- | --- |
| Comments get missed because Brandon is busy. | Collect and prioritize eligible unanswered comments automatically. | More worthwhile comments receive a response during the monitored period. |
| A response must understand the actual post. | Use the creative, caption and thread; flag missing context. | Replies correctly address the joke, question or discussion. |
| Butter's voice matters. | Use approved Butter examples and editable voice rules. | Brandon would publish the replies with little or no rewriting. |
| The tool must reduce work. | Draft before review, show context together and remember decisions. | Less hands-on time than manually handling the same conversations, including setup and ongoing upkeep. |
| Brandon does not yet trust unrestricted publishing. | Start with approval and provide a visible record, pause control and scoped automation. | He can see what was sent and control what happens next. |
| Another hire or paid social tool is unwanted. | Keep the initial design within existing resources and avoid required additional subscriptions. | The workflow operates within that constraint without shifting the burden into constant maintenance. |

Instagram is the first platform. TikTok is a possible extension after the Instagram workflow proves useful and TikTok access is confirmed. Public replies on Butter's own posts are the initial scope.

A successful response may acknowledge a person, contribute to a joke, answer a supported question or invite a relevant continuation. It does not need to ask a question every time. Leaving a comment alone is an acceptable editorial decision.

## Boundaries

The first release does not include scheduling posts, generating feed content, cold outreach, automated DMs, sales funnels, a customer service platform, or automatic deletion of audience comments.

The objective is not to answer every comment or increase the displayed comment count with Butter's own messages. The system should avoid repetitive filler, manufactured arguments and engagement bait. It speaks as Butter.ATL and must not invent personal experiences or relationships for Brandon.

NapoleonCat and BrandBastion supply useful reference patterns. Replicating their entire products is not a project requirement. Each proposed feature must improve coverage of worthwhile conversations, reply quality, Brandon's workload or his control. Features without that connection should be deferred.

## How we will judge success

Establish a baseline using a sample of real posts and comments. Brandon should identify which comments merit a response, which should be skipped and which require his judgment. This provides a human reference for judging the system's selection decisions.

Measure these outcomes together:

- Coverage: worthwhile comments answered divided by worthwhile comments in the monitored sample. Include missed opportunities and inappropriate selections.
- Workload: hands-on minutes to handle the same eligible conversations manually versus with the tool. Include reviewing, editing, error correction and recurring maintenance.
- Quality: proportion of drafts publishable without substantive edits, plus factual mistakes, context errors, repetitive phrasing and voice mismatches.
- Audience response: whether people continue the conversation after Butter replies. Report audience contributions separately from Butter's replies and compare similar posts cautiously.
- Trust: unapproved sends, duplicate replies, visibility into activity, and how well the app holds situations outside its permitted scope.

Set numeric pilot targets after measuring the baseline. Technical success alone is insufficient. Broader autonomy depends on demonstrated quality within specific situations, not simply elapsed time.

## Proposed implementation

A small local application using official Instagram account access, a local AI model and an approval inbox is the current candidate. Local hosting and model choices serve the cost constraint; they are not the product objective. Validate that the actual hardware, reply quality and operating schedule can meet the requirements before treating this architecture as settled. Account permissions must be verified before promising live operation.

No Butter account was connected, no live comments were retrieved, and no replies were published for this analysis.

## Reference patterns from existing products

| Area | NapoleonCat | BrandBastion | Butter design |
| --- | --- | --- | --- |
| Draft generation | Click to generate a suggestion. | Workflows prepare drafts before the user opens the queue. | Prepare drafts in the background. |
| Context | Comment, post content, thread, relevant previous brand responses. | Post analysis plus selected factual sources and prompt instructions. | Combine a cached post brief, thread, approved facts, and curated Butter examples. |
| Media | Not established. | Image text extraction, audio transcription, visual description, inferred intent. | Process the actual creative as well as its caption. |
| Approval | Edit, regenerate, then send. | Batch review and sending; AI workflows can also auto-send. | Approval by default, with explicit settings for later automation. |
| Voice | Retrieves relevant historical examples at drafting time. | Configurable prompts and conditions. | Store voice rules separately from factual sources. |

## Candidate local architecture

| Component | Proposed implementation | Purpose |
| --- | --- | --- |
| Account adapter | Official Instagram API with authorized Butter account access | Read owned posts, comments and replies; publish approved public replies. |
| Worker and interface | One Python application with a local browser interface | Run collection, drafting, review and sending without a separate automation subscription. |
| Storage | SQLite database plus a local media/cache folder | Persist work, approvals, examples and sending results. |
| Reply generation | Ollama with a locally downloaded model | Generate replies without a per-request cloud bill. |
| Visual interpretation | A compatible local vision model through Ollama | Interpret images and sampled video frames. |
| Audio | Existing production transcripts first; whisper.cpp when necessary | Transcribe locally. |
| Monitoring | Scheduled API pulls while the app is running; webhooks later | Start without an always-public server. |

Ollama supports local-only operation and image inputs; its cloud functions should be disabled explicitly. Model choice must follow a check of the actual computer and performance on Butter material. Do not assume a browser user-agent string identifies suitable hardware.

Start with the interface bound to the local computer (127.0.0.1). Do not expose the model service or access tokens publicly.

## Processing workflow

### 1. Verify account access before building out the interface

Confirm account type and Meta app permissions (Instagram Login route supports professional accounts and comment management). First prove an authorized read of one owned post, its comments and an existing reply thread. Prepare one proposed response for review. Verify publishing only when the user has authorized that specific test. A mock connector must remain visibly identified as mock. Do not assume Standard Access guarantees webhooks. Select a supported API version at implementation time and keep it configurable.

### 2. Collect comments without wasting requests

Start with selected recent posts. Prioritize unanswered questions and comments where Butter would add value. Keep potentially valuable conversations visible even when they need human judgment. Poll active posts more often and reduce frequency as activity slows. Use pagination, saved checkpoints, overlapping retrieval, and rate-limit backoff. Keep an explicit oldest monitored date.

Use platform comment IDs as unique keys. Store parent IDs and thread relationships. Ignore Butter's own outbound comments as new work. Pause collection clearly when credentials expire. Display the time of the last successful sync.

### 3. Understand each post once

Create an editable post brief from: caption and date; image/carousel content incl. readable text; timestamped video frames; spoken transcript (preferably supplied); apparent topic, tone, joke, question or announcement; confirmed facts, source references and missing context.

If media is unavailable, show that context is incomplete and require review. A caption-only draft must not be described as having understood the video. Store inferred intent separately from verified facts. Re-analyze when caption, source facts or brief changes, and invalidate affected unsent drafts. Process a post's media once and reuse the brief.

### 4. Decide whether to engage and draft

Four outcomes: draft, hold for review, skip, already handled. Classify by purpose, not sentiment.

The drafting request receives: editable voice rules; post brief and pertinent thread; a few relevant human-curated examples; approved factual references when needed; recent replies under that post to discourage repetition.

Tags and local text search for example selection (no vector DB, no training). Keep approved examples distinct from unreviewed outputs. Allow promoting an edited reply as a good example.

Structured output fields: decision, draft_text, category, reason, facts_used, missing_context, review_flags, post_brief_version, voice_version. Validate before saving. Model self-reported confidence is not publishing permission.

Comments, transcripts and external content are untrusted data. They cannot modify voice rules, access secrets, authorize sending, or execute tools. The model drafts text; a separate application function controls publishing.

### 5. Review in one screen

Post beside comment, thread and editable draft. Actions: Approve and send, Edit, Regenerate, Skip, Hold, Pause post. Selected batch approval after text is visible. Queues: Ready, Needs attention, Sent, Skipped. Surface connection failures and uncertain sends.

Store the exact approved text. An edit, regeneration, or relevant context change invalidates approval. The sender must not regenerate text after approval.

### 6. Publish reliably

Immediately before sending, recheck the comment exists, is eligible, and is not already answered by Butter (in-app or on Instagram). Lock the outbound task. Persist the returned reply ID. After an uncertain timeout, reconcile the thread before retrying; if unresolved, hold for review. Keep auth failures, rate limits and permanent errors distinct. App-level daily limit, per-post limit and global pause enforced outside the model.

## Butter voice and autonomy

Concise, conversational, locally informed; humor when the post supports it; no forced slang; no generic corporate gratitude; no mandatory question; no invented attendance, relationships, experiences, endorsements or facts. Repeating the same joke across a thread is a failure.

Start in review mode. Later enable automation by category and post eligibility based on observed quality. Candidates: uncomplicated acknowledgments; questions answered explicitly in a current approved source. Ambiguous jokes, allegations, tragedies, sponsor issues, disputes and missing facts stay in review. Positive sentiment alone never makes a reply eligible. Configurable interaction limit. Local daily activity recap (sent, held, errors). Examples and rules editable without code changes.

## Minimum data records

| Record | Key fields |
| --- | --- |
| Posts | Platform ID, caption, source URL, media reference, brief, brief version, context status, monitored/paused flag. |
| Comments | Platform ID, post ID, parent ID, author ID, text, timestamps, visibility and handling status. |
| Drafts | Comment ID, exact draft text, version, decisions, sources, flags and approval record. |
| Outbound tasks | Draft version, status, lock, attempts, returned reply ID and reconciliation state. |
| Examples and knowledge | Approved text, category, factual source, validity date and reviewer. |

Credentials belong in protected config or the OS credential store; never in prompts, browser responses, exported examples or logs.

## Cost and delivery boundaries

No paid services required, contingent on suitable hardware and authorized platform access. If the computer sleeps, processing stops and backlog is collected on resume. If local models are too slow or poor, compare a smaller model, shorter context and fewer concurrent jobs first. A cloud model is optional, not baseline. TikTok is a subsequent adapter requiring separate confirmation.

## Acceptance checks and build order

1. Prove the real Instagram read connection and document granted permissions.
2. Build the persistent collector and cached post briefs.
3. Add local drafting and the approval interface.
4. Verify one authorized send and reconciliation behavior.
5. Evaluate roughly 100 real comments across 10 varied Butter posts, using the human-labeled baseline and the coverage, workload, quality, audience-response and trust measures.
6. Test duplicate delivery, a reply made directly in Instagram, deleted comments, an expired token, a paused post, an uncertain send timeout and an instruction-injection comment. Confirm unapproved text cannot publish.
7. Enable selected automation only after it meets the agreed quality bar.

Implementation inputs still needed: the computer's OS, processor/GPU and memory; authorized Meta account setup; representative Butter media and approved response examples.

## Standing rules (Butter.ATL canon, from the brand-voice skill)

These bind the default voice rules the app ships with and any Butter-facing copy:

- No emojis. No em dashes anywhere. No em spaces.
- No "let me know" closers, no filler ("you know", "it's important to note"), no robot language ("We are delighted", "With gratitude"), no corporate jargon, no rule-of-three padding, no significance inflation, no synonym cycling, no overuse of bold.
- No lazy contrast phrasing ("it's not X, it's Y", "not just X, but Y", "bigger than X", "not noise, signal").
- Don't overdo slang. Professional but cool, ATL-rooted, first person / "we" from inside the culture.
- Do-not-cover: murder, violent crime, shootings, stabbings, random tragedy. Comments on such posts always stay in human review; never auto-send.
- Never use #COCWeekend (use #CreativesOfColor or #CreativeHomecoming). Capture the Flag ATL: say "the app" and "check-ins", never "passport"/"stamps".
- Keep 404 Day separate from brand partnership talk.
- Do-the-work doctrine: hand Brandon finished work; only human-only steps (approve, connect account, decide) go in a short "Needs a human" list. Bottom line first.
- Brand tokens for the UI: Butter yellow #EFB82E (only yellow), Inter body, Space Mono utility. (Filson Pro is commercial and not bundled; fall back to system display font.)

## Build-environment constraints (this session)

- Built inside the `butternomics/open-saas` repo under a new standalone directory `butter-comment-assistant/`. It does not touch the Wasp template.
- No Instagram account, Meta app, Ollama or GPU is available in the build container. Real connectors must be implemented against documented APIs and exercised with recorded fixtures/fakes; the mock connector must be labeled MOCK in the UI. Live verification steps go in "Needs a human".
