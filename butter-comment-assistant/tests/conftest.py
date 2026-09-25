"""Shared pytest fixtures: a migrated temp SQLite database per test.

Later plans (see 01-07) extend this file with app/connector fixtures.
"""

from collections.abc import Iterator

import pytest
from sqlmodel import Session

from butter_comment_assistant.storage.db import make_engine, run_migrations, sqlite_url


@pytest.fixture
def db_url(tmp_path) -> str:
    """A tmp_path SQLite file URL with migrations already applied."""
    url = sqlite_url(tmp_path / "butter.db")
    run_migrations(url)
    return url


@pytest.fixture
def engine(db_url):
    eng = make_engine(db_url)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine) -> Iterator[Session]:
    with Session(engine) as sess:
        yield sess
