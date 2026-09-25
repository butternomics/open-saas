# Phase 1: Foundation and Connectors - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 1-foundation-and-connectors
**Mode:** `--auto` (recommended defaults selected without prompting)
**Areas discussed:** Package layout and tooling, Storage schema and state machines, Settings and process configuration, Secrets and logging, Network binding and CSRF, App shell and UI tokens, Connector protocol, LLM client protocol, Connection status screen, Testing conventions

---

## Package layout and tooling

| Option | Description | Selected |
|--------|-------------|----------|
| src layout, package `butter_comment_assistant`, pyproject + uv with pip fallback | Standard modern Python packaging; importable name matches directory | ✓ |
| Flat `app/` package as sketched in ARCHITECTURE.md | Simpler tree, but `app` is a generic import name and collides with FastAPI conventions | |
| Poetry or requirements.txt only | Extra tool or no lockable metadata | |

**Auto selection:** src layout (recommended default). `[auto] Package layout — Q: "Flat app/ or src layout?" → Selected: "src layout" (recommended default)`
**Notes:** Module names from ARCHITECTURE.md are preserved (connectors, storage, web, llm) so later phases map 1:1.

---

## Storage schema and state machines

| Option | Description | Selected |
|--------|-------------|----------|
| Pin all ten tables plus enums and transition tables in the initial migration | Later phases add columns via new revisions but never restructure core tables | ✓ |
| Create only Phase 1 tables (settings, audit_log) and let each phase add its own | Smaller Phase 1, but every later phase would migrate core tables ad hoc | |

**Auto selection:** Pin everything now. `[auto] Schema — Q: "Pin the full schema now or grow per phase?" → Selected: "Pin now" (recommended default)`
**Notes:** `eval_labels` added beyond the ARCHITECTURE.md nine so Phase 5 does not need a core migration.

---

## Settings and process configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Env vars for process config, `settings` table for editable app settings via a typed `AppSettings` model | Separates what needs a restart from what Brandon edits in the UI | ✓ |
| Everything in a YAML/TOML file | Not editable without code or a file editor; violates FOUND-03 | |
| pydantic-settings dependency | Extra dependency for a handful of env vars | |

**Auto selection:** Two layers. `[auto] Settings — Q: "Where do editable settings live?" → Selected: "settings table + AppSettings" (recommended default)`

---

## Secrets and logging

| Option | Description | Selected |
|--------|-------------|----------|
| SecretStore protocol with keyring and 0600 file implementations, auto resolution with loud warning | Works on the deployment machine and in the headless container | ✓ |
| keyring only | Fails in the container (backend is fail.Keyring) | |
| keyrings.alt encrypted file | Extra dependency and a passphrase to manage | |

**Auto selection:** keyring + own file store. `[auto] Secrets — Q: "Fallback when no keyring backend?" → Selected: "0600 JSON file with warning" (recommended default)`

---

## Network binding and CSRF

| Option | Description | Selected |
|--------|-------------|----------|
| Loopback assertion before uvicorn plus lifespan check; env override `BCA_ALLOW_NON_LOOPBACK=1` | Refuses non-loopback by default, explicit documented override | ✓ |
| Rely on uvicorn default host | Nothing stops `--host 0.0.0.0` | |
| CSRF double-submit cookie plus header/form token, compared with constant time | No session store needed for a single-user local app | ✓ |
| Origin header check only | Weaker; some clients omit Origin | |

**Auto selection:** as above. `[auto] Security — Q: "CSRF mechanism?" → Selected: "double-submit cookie + header" (recommended default)`

---

## App shell and UI tokens

| Option | Description | Selected |
|--------|-------------|----------|
| Jinja2 base template, vendored htmx 2.0.4, CSS variables for Butter tokens, MOCK and AUTOMATION OFF badges in header | Meets REVIEW-06 and CONN-02 from day one | ✓ |
| Load fonts/htmx from a CDN | Violates local-only design | |

**Auto selection:** vendored assets. `[auto] UI — Q: "Vendor htmx or CDN?" → Selected: "vendor" (recommended default)`

---

## Connector protocol

| Option | Description | Selected |
|--------|-------------|----------|
| Async runtime-checkable Protocol with six methods plus kind/is_mock/display_name, DTOs as pydantic models, error hierarchy, factory with lazy import | Exactly the seam ARCHITECTURE.md describes, testable without network | ✓ |
| ABC base class | Works too, but Protocol keeps Mock free of inheritance coupling | |
| Sync methods | Would block the FastAPI loop during polling | |

**Auto selection:** async Protocol. `[auto] Connector — Q: "Sync or async interface?" → Selected: "async" (recommended default)`

---

## LLM client protocol

| Option | Description | Selected |
|--------|-------------|----------|
| `generate_structured(request, schema)` returning validated model, `LLMOutputInvalid` on failure, no tool parameters | Enforces strict schema and injection isolation structurally | ✓ |
| Free-text `generate()` plus JSON parsing in the caller | Lenient parsing is the pitfall PITFALLS.md warns about | |

**Auto selection:** structured-only interface. `[auto] LLM — Q: "Structured-only or free text?" → Selected: "structured-only" (recommended default)`

---

## Connection status screen

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated `/status` page with cached auth check and CSRF-protected refresh action, distinct AUTH PROBLEM block | Satisfies CONN-05 and prepares COLL-07 | ✓ |
| Status widget inside settings | Mixes concerns | |

**Auto selection:** dedicated page. `[auto] Status — Q: "Separate page?" → Selected: "yes" (recommended default)`

---

## Testing conventions

| Option | Description | Selected |
|--------|-------------|----------|
| pytest + pytest-asyncio auto mode + respx + TestClient, real migrations per test, Mock/Fake defaults in conftest | Whole suite offline in under a minute | ✓ |
| unittest | Weaker async and fixture story | |

**Auto selection:** pytest stack. `[auto] Tests — Q: "create_all or migrations in tests?" → Selected: "real migrations" (recommended default)`

---

## Claude's Discretion

- CSS beyond tokens, status label wording, mock dataset text, `MockScenario` internals, autogenerated vs hand-written initial revision, DTO base class.

## Deferred Ideas

- Collector, briefs, triage, inbox, sender, audit UI, recap, evaluation, automation gating, runbook, webhooks, TikTok, cloud LLM. All belong to Phases 2 to 5 or v2.
