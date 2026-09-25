"""Engine creation, programmatic Alembic migrations and session scope."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

# butter-comment-assistant/ (this file is src/butter_comment_assistant/storage/db.py)
PACKAGE_ROOT: Path = Path(__file__).resolve().parents[3]


def sqlite_url(db_path: Path) -> str:
    return f"sqlite:///{db_path}"


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, connect_args={"check_same_thread": False})


def run_migrations(database_url: str) -> None:
    """Run Alembic migrations to head against `database_url`. Safe to call twice."""
    if database_url.startswith("sqlite:///"):
        db_file = database_url.removeprefix("sqlite:///")
        if db_file and db_file != ":memory:":
            Path(db_file).resolve().parent.mkdir(parents=True, exist_ok=True)

    cfg = Config(str(PACKAGE_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PACKAGE_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Yield a Session, committing on success and rolling back on exception."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
