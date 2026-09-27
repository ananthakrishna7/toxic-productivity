"""Pytest fixtures for Toxic Productivity Bot testing suite.

Sets up hermetic in-memory SQLite database sessions and mock Telegram objects.
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base, User, utc_now


@pytest.fixture
def db_session_factory():
    """Creates a temporary, hermetic in-memory SQLite database and session factory."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_session_factory) -> Generator[Session, None, None]:
    """Yields a single database session for a test."""
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Creates and returns a sample registered user."""
    user = User(
        chat_id=123456789,
        username="testdrone",
        first_name="Test Drone",
        registered_at=utc_now(),
        work_days="0,1,2,3,4",
        work_start="09:00",
        work_end="18:00",
        weekly_stats_day=5,
        weekly_stats_time="19:00",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_context(db_session_factory):
    """Creates a mock Telegram ContextTypes object with bot and bot_data."""
    context = MagicMock()
    context.bot = AsyncMock()
    context.bot_data = {"session_factory": db_session_factory}
    context.args = []
    return context


@pytest.fixture
def make_mock_update():
    """Factory fixture to create mock Telegram Update objects."""
    def _create(
        chat_id: int = 123456789,
        username: str = "testdrone",
        first_name: str = "Test Drone",
        text: str = "",
        is_callback: bool = False,
        callback_data: str = "",
    ):
        update = MagicMock()
        user = MagicMock()
        user.id = chat_id
        user.username = username
        user.first_name = first_name

        chat = MagicMock()
        chat.id = chat_id

        update.effective_user = user
        update.effective_chat = chat

        if is_callback:
            query = AsyncMock()
            query.data = callback_data
            query.from_user = user
            query.message = MagicMock()
            query.message.chat = chat
            update.callback_query = query
            update.message = None
        else:
            msg = MagicMock()
            msg.text = text
            msg.chat = chat
            msg.from_user = user
            update.message = msg
            update.callback_query = None

        return update

    return _create
