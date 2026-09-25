"""Status enums, transition tables and small storage-level helpers.

Every later phase imports these names rather than redefining its own status
values or transition rules.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum


class CommentStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    DRAFTED = "drafted"
    HELD = "held"
    SKIPPED = "skipped"
    ALREADY_HANDLED = "already_handled"
    STALE = "stale"


class DraftStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    HELD = "held"
    APPROVED = "approved"
    QUEUED = "queued"
    SENT = "sent"
    INVALIDATED = "invalidated"
    SKIPPED = "skipped"


class OutboundStatus(str, Enum):
    PENDING = "pending"
    LOCKED = "locked"
    SENT = "sent"
    UNCERTAIN = "uncertain"
    RECONCILED = "reconciled"
    FAILED_AUTH = "failed_auth"
    RATE_LIMITED = "rate_limited"
    PERMANENT_ERROR = "permanent_error"


class ContextStatus(str, Enum):
    UNPROCESSED = "unprocessed"
    CAPTION_ONLY = "caption_only"
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


class ErrorClass(str, Enum):
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNCERTAIN = "uncertain"


class ConnectorKind(str, Enum):
    MOCK = "mock"
    INSTAGRAM = "instagram"


class LLMKind(str, Enum):
    FAKE = "fake"
    OLLAMA = "ollama"


class ExampleKind(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class ExampleStatus(str, Enum):
    APPROVED = "approved"
    UNREVIEWED = "unreviewed"
    RETIRED = "retired"


class KnowledgeStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class EvalLabel(str, Enum):
    RESPOND = "respond"
    SKIP = "skip"
    NEEDS_JUDGMENT = "needs_judgment"


class AuditEvent(str, Enum):
    DRAFT_CREATED = "draft_created"
    DRAFT_EDITED = "draft_edited"
    DRAFT_REGENERATED = "draft_regenerated"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_INVALIDATED = "draft_invalidated"
    DRAFT_HELD = "draft_held"
    DRAFT_SKIPPED = "draft_skipped"
    TASK_CREATED = "task_created"
    TASK_LOCKED = "task_locked"
    SEND_SUCCEEDED = "send_succeeded"
    SEND_UNCERTAIN = "send_uncertain"
    SEND_FAILED_AUTH = "send_failed_auth"
    SEND_RATE_LIMITED = "send_rate_limited"
    SEND_PERMANENT_ERROR = "send_permanent_error"
    RECONCILED_AS_SENT = "reconciled_as_sent"
    RECONCILED_AS_NOT_SENT = "reconciled_as_not_sent"
    POST_PAUSED = "post_paused"
    POST_RESUMED = "post_resumed"
    SETTINGS_CHANGED = "settings_changed"
    BRIEF_UPDATED = "brief_updated"
    VOICE_RULES_UPDATED = "voice_rules_updated"
    AUTH_FAILED = "auth_failed"
    SYNC_SUCCEEDED = "sync_succeeded"


COMMENT_TRANSITIONS: dict[CommentStatus, frozenset[CommentStatus]] = {
    CommentStatus.NEW: frozenset({CommentStatus.TRIAGED}),
    CommentStatus.TRIAGED: frozenset(
        {
            CommentStatus.DRAFTED,
            CommentStatus.HELD,
            CommentStatus.SKIPPED,
            CommentStatus.ALREADY_HANDLED,
        }
    ),
    CommentStatus.DRAFTED: frozenset(
        {
            CommentStatus.HELD,
            CommentStatus.SKIPPED,
            CommentStatus.ALREADY_HANDLED,
            CommentStatus.STALE,
        }
    ),
    CommentStatus.HELD: frozenset(
        {
            CommentStatus.TRIAGED,
            CommentStatus.SKIPPED,
            CommentStatus.ALREADY_HANDLED,
        }
    ),
    CommentStatus.STALE: frozenset({CommentStatus.TRIAGED}),
    CommentStatus.SKIPPED: frozenset({CommentStatus.TRIAGED}),
    CommentStatus.ALREADY_HANDLED: frozenset(),
}

DRAFT_TRANSITIONS: dict[DraftStatus, frozenset[DraftStatus]] = {
    DraftStatus.PENDING_REVIEW: frozenset(
        {
            DraftStatus.HELD,
            DraftStatus.APPROVED,
            DraftStatus.SKIPPED,
            DraftStatus.INVALIDATED,
        }
    ),
    DraftStatus.HELD: frozenset(
        {
            DraftStatus.PENDING_REVIEW,
            DraftStatus.SKIPPED,
            DraftStatus.INVALIDATED,
        }
    ),
    DraftStatus.APPROVED: frozenset({DraftStatus.QUEUED, DraftStatus.INVALIDATED}),
    DraftStatus.QUEUED: frozenset(
        {DraftStatus.SENT, DraftStatus.INVALIDATED, DraftStatus.APPROVED}
    ),
    DraftStatus.SENT: frozenset(),
    DraftStatus.INVALIDATED: frozenset(),
    DraftStatus.SKIPPED: frozenset(),
}

OUTBOUND_TRANSITIONS: dict[OutboundStatus, frozenset[OutboundStatus]] = {
    OutboundStatus.PENDING: frozenset({OutboundStatus.LOCKED}),
    OutboundStatus.LOCKED: frozenset(
        {
            OutboundStatus.SENT,
            OutboundStatus.UNCERTAIN,
            OutboundStatus.FAILED_AUTH,
            OutboundStatus.RATE_LIMITED,
            OutboundStatus.PERMANENT_ERROR,
            OutboundStatus.PENDING,
        }
    ),
    OutboundStatus.UNCERTAIN: frozenset({OutboundStatus.RECONCILED}),
    OutboundStatus.RECONCILED: frozenset({OutboundStatus.SENT, OutboundStatus.PENDING}),
    OutboundStatus.RATE_LIMITED: frozenset({OutboundStatus.PENDING}),
    OutboundStatus.FAILED_AUTH: frozenset({OutboundStatus.PENDING}),
    OutboundStatus.PERMANENT_ERROR: frozenset({OutboundStatus.PENDING}),
    OutboundStatus.SENT: frozenset(),
}


class IllegalTransition(ValueError):
    """Raised when a state machine transition is not allowed."""


def assert_transition(table: Mapping, current, new) -> None:
    """Raise IllegalTransition unless `new` is a legal next state from `current`."""
    allowed = table.get(current, frozenset())
    if new not in allowed:
        raise IllegalTransition(f"{current.value} -> {new.value} is not allowed")


def utcnow() -> datetime:
    """Naive UTC timestamp (no tzinfo) for storage columns."""
    return datetime.now(UTC).replace(tzinfo=None)


def new_id() -> str:
    """A UUID4 hex string, used as the primary key for non-platform-id tables."""
    return uuid.uuid4().hex


__all__ = [
    "CommentStatus",
    "DraftStatus",
    "OutboundStatus",
    "ContextStatus",
    "ErrorClass",
    "ConnectorKind",
    "LLMKind",
    "ExampleKind",
    "ExampleStatus",
    "KnowledgeStatus",
    "EvalLabel",
    "AuditEvent",
    "COMMENT_TRANSITIONS",
    "DRAFT_TRANSITIONS",
    "OUTBOUND_TRANSITIONS",
    "assert_transition",
    "IllegalTransition",
    "utcnow",
    "new_id",
]
