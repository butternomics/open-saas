"""SQLModel table definitions for the ten core tables.

Append-only convention: audit_log rows are never updated or deleted; no
helper for that exists.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Index, String
from sqlmodel import Field, SQLModel

from butter_comment_assistant.storage.enums import new_id, utcnow


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: str = Field(primary_key=True)
    caption: str | None = None
    source_url: str | None = None
    media_type: str | None = None
    media_refs_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    posted_at: datetime | None = None
    brief_json: dict | None = Field(default=None, sa_column=Column(JSON))
    brief_version: int = 0
    context_status: str = Field(
        default="unprocessed", sa_column=Column(String(32), nullable=False, index=True)
    )
    sensitivity_flag: bool = False
    sensitivity_reason: str | None = None
    monitored: bool = False
    paused: bool = False
    last_synced_at: datetime | None = None
    checkpoint_cursor: str | None = None
    next_poll_at: datetime | None = None
    poll_interval_s: int | None = None
    quiet_cycles: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: str = Field(primary_key=True)
    post_id: str = Field(foreign_key="posts.id", index=True)
    parent_id: str | None = Field(default=None, foreign_key="comments.id", index=True)
    thread_root_id: str | None = None
    depth: int = 0
    author_id: str | None = None
    author_username: str | None = None
    text: str = ""
    is_own_reply: bool = False
    created_at_platform: datetime | None = None
    fetched_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None
    handling_status: str = Field(
        default="new", sa_column=Column(String(32), nullable=False, index=True)
    )
    handled_by_draft_id: str | None = None
    audience_replied_after_butter: bool = False
    updated_at: datetime = Field(default_factory=utcnow)


class Draft(SQLModel, table=True):
    __tablename__ = "drafts"

    id: str = Field(default_factory=new_id, primary_key=True)
    comment_id: str = Field(foreign_key="comments.id", index=True)
    version: int = 1
    draft_text: str
    decision: str | None = None
    category: str | None = None
    reason: str | None = None
    facts_used_json: list = Field(default_factory=list, sa_column=Column(JSON))
    missing_context_json: list = Field(default_factory=list, sa_column=Column(JSON))
    review_flags_json: list = Field(default_factory=list, sa_column=Column(JSON))
    system_flags_json: list = Field(default_factory=list, sa_column=Column(JSON))
    post_brief_version: int = 0
    voice_version: int = 0
    status: str = Field(
        default="pending_review", sa_column=Column(String(32), nullable=False, index=True)
    )
    approved_text: str | None = None
    approved_text_hash: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    invalidated_reason: str | None = None
    auto_sent: bool = False
    sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class OutboundTask(SQLModel, table=True):
    __tablename__ = "outbound_tasks"

    id: str = Field(default_factory=new_id, primary_key=True)
    draft_id: str = Field(foreign_key="drafts.id", index=True)
    comment_id: str
    approved_text_hash: str
    idempotency_key: str = Field(unique=True)
    status: str = Field(
        default="pending", sa_column=Column(String(32), nullable=False, index=True)
    )
    lock_owner: str | None = None
    locked_at: datetime | None = None
    attempts: int = 0
    last_attempt_at: datetime | None = None
    returned_reply_id: str | None = None
    error_class: str | None = Field(default=None, sa_column=Column(String(32)))
    error_detail: str | None = None
    reconciliation_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Example(SQLModel, table=True):
    __tablename__ = "examples"

    id: str = Field(default_factory=new_id, primary_key=True)
    text: str
    tags_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    kind: str = Field(default="positive", sa_column=Column(String(32), nullable=False))
    status: str = Field(default="unreviewed", sa_column=Column(String(32), nullable=False))
    source_comment_id: str | None = None
    reviewer: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Knowledge(SQLModel, table=True):
    __tablename__ = "knowledge"

    id: str = Field(default_factory=new_id, primary_key=True)
    fact_text: str
    category: str | None = None
    source: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    reviewer: str | None = None
    status: str = Field(default="active", sa_column=Column(String(32), nullable=False))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class VoiceRules(SQLModel, table=True):
    __tablename__ = "voice_rules"

    version: int = Field(primary_key=True)
    rules_text: str
    is_active: bool = True
    updated_by: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)


class Setting(SQLModel, table=True):
    __tablename__ = "settings"

    key: str = Field(primary_key=True)
    value_json: Any = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_entity", "entity_type", "entity_id"),)

    id: int | None = Field(default=None, primary_key=True)
    entity_type: str
    entity_id: str
    event: str = Field(sa_column=Column(String(32), nullable=False))
    from_status: str | None = None
    to_status: str | None = None
    actor: str = "system"
    original_text: str | None = None
    approved_text: str | None = None
    detail_json: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class EvalLabelRow(SQLModel, table=True):
    __tablename__ = "eval_labels"

    id: str = Field(default_factory=new_id, primary_key=True)
    comment_id: str = Field(index=True)
    sample_name: str
    label: str = Field(sa_column=Column(String(32), nullable=False))
    labeler: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
