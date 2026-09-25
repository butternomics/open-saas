"""Schema, migration and state-machine tests for the storage layer."""

import itertools

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, select

from butter_comment_assistant.storage.db import run_migrations
from butter_comment_assistant.storage.enums import (
    COMMENT_TRANSITIONS,
    DRAFT_TRANSITIONS,
    OUTBOUND_TRANSITIONS,
    CommentStatus,
    DraftStatus,
    IllegalTransition,
    OutboundStatus,
    assert_transition,
    new_id,
    utcnow,
)
from butter_comment_assistant.storage.models import (
    AuditLog,
    Comment,
    Draft,
    OutboundTask,
    Post,
    Setting,
)

TEN_TABLES = {
    "posts",
    "comments",
    "drafts",
    "outbound_tasks",
    "examples",
    "knowledge",
    "voice_rules",
    "settings",
    "audit_log",
    "eval_labels",
}


def test_migrations_create_all_ten_tables(db_url, engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
    table_names = {r[0] for r in rows}
    assert TEN_TABLES <= table_names


def test_run_migrations_is_idempotent(db_url, engine):
    # db_url fixture already ran migrations once; run again on the same file.
    run_migrations(db_url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == "0001"


def test_autogenerate_reports_zero_diff(engine):
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn, opts={"compare_type": True, "render_as_batch": True}
        )
        diff = compare_metadata(ctx, SQLModel.metadata)
    assert diff == []


def test_round_trip_insert_and_read(session):
    post = Post(id="post-1", caption="hello")
    comment = Comment(id="comment-1", post_id="post-1", parent_id=None, text="nice post")
    draft = Draft(
        comment_id="comment-1",
        draft_text="thanks!",
        facts_used_json=["k1"],
    )
    session.add(post)
    session.add(comment)
    session.add(draft)
    session.commit()

    task = OutboundTask(
        draft_id=draft.id,
        comment_id="comment-1",
        approved_text_hash="deadbeef",
        idempotency_key=new_id(),
    )
    audit = AuditLog(entity_type="comment", entity_id="comment-1", event="draft_created")
    setting = Setting(key="daily_send_limit", value_json=20)
    session.add(task)
    session.add(audit)
    session.add(setting)
    session.commit()

    reloaded_draft = session.exec(select(Draft).where(Draft.id == draft.id)).one()
    assert reloaded_draft.facts_used_json == ["k1"]

    reloaded_setting = session.exec(select(Setting).where(Setting.key == "daily_send_limit")).one()
    assert reloaded_setting.value_json == 20

    reloaded_task = session.exec(
        select(OutboundTask).where(OutboundTask.id == task.id)
    ).one()
    assert reloaded_task.idempotency_key == task.idempotency_key

    reloaded_audit = session.exec(select(AuditLog).where(AuditLog.id == audit.id)).one()
    assert reloaded_audit.event == "draft_created"


def test_duplicate_idempotency_key_raises_integrity_error(session):
    post = Post(id="post-2", caption="hello 2")
    comment = Comment(id="comment-2", post_id="post-2", text="hi")
    draft = Draft(comment_id="comment-2", draft_text="thanks!")
    session.add(post)
    session.add(comment)
    session.add(draft)
    session.commit()

    key = new_id()
    task1 = OutboundTask(
        draft_id=draft.id, comment_id="comment-2", approved_text_hash="h1", idempotency_key=key
    )
    session.add(task1)
    session.commit()

    task2 = OutboundTask(
        draft_id=draft.id, comment_id="comment-2", approved_text_hash="h2", idempotency_key=key
    )
    session.add(task2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


TRANSITION_TABLES = {
    CommentStatus: COMMENT_TRANSITIONS,
    DraftStatus: DRAFT_TRANSITIONS,
    OutboundStatus: OUTBOUND_TRANSITIONS,
}

ALLOWED_PAIRS = [
    (table, current, new)
    for table in TRANSITION_TABLES.values()
    for current, allowed in table.items()
    for new in allowed
]


@pytest.mark.parametrize("table,current,new", ALLOWED_PAIRS)
def test_allowed_transitions_pass(table, current, new):
    assert_transition(table, current, new)


TERMINAL_STATES = [
    (DRAFT_TRANSITIONS, DraftStatus.SENT),
    (DRAFT_TRANSITIONS, DraftStatus.INVALIDATED),
    (DRAFT_TRANSITIONS, DraftStatus.SKIPPED),
    (COMMENT_TRANSITIONS, CommentStatus.ALREADY_HANDLED),
]


@pytest.mark.parametrize("table,terminal_state", TERMINAL_STATES)
def test_terminal_states_have_no_outgoing_transitions(table, terminal_state):
    assert table.get(terminal_state, frozenset()) == frozenset()
    enum_cls = type(terminal_state)
    for candidate in enum_cls:
        if candidate == terminal_state:
            continue
        with pytest.raises(IllegalTransition):
            assert_transition(table, terminal_state, candidate)


def test_outbound_pending_to_sent_requires_locked():
    with pytest.raises(IllegalTransition):
        assert_transition(OUTBOUND_TRANSITIONS, OutboundStatus.PENDING, OutboundStatus.SENT)


def test_draft_sent_to_pending_review_illegal():
    with pytest.raises(IllegalTransition):
        assert_transition(DRAFT_TRANSITIONS, DraftStatus.SENT, DraftStatus.PENDING_REVIEW)


def test_utcnow_is_naive():
    assert utcnow().tzinfo is None


def test_new_id_is_32_hex_chars():
    value = new_id()
    assert len(value) == 32
    assert all(c in "0123456789abcdef" for c in value)


def test_every_enum_member_appears_in_its_transition_table_or_is_intentionally_absent():
    # Sanity check: every non-terminal-only member listed in a transition table
    # key set is a real enum member (guards against typos in the tables).
    for enum_cls, table in TRANSITION_TABLES.items():
        for member in itertools.chain(table.keys(), *table.values()):
            assert isinstance(member, enum_cls)
