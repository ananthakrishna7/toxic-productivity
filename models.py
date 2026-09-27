"""SQLAlchemy ORM models and database initialization for Toxic Productivity Bot.

Provides database models for Users, WorkLogs, and DaysOff, with flexible
backend support (SQLite by default, compatible with PostgreSQL/MySQL).
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

DEFAULT_DATABASE_URL = "sqlite:///productivity.db"


def utc_now() -> datetime:
    """Returns the current naive datetime in UTC (avoids deprecation and DB mismatches)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class User(Base):
    """User model representing a registered Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Workday configuration
    # work_days: comma-separated list of weekdays (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)
    work_days: Mapped[str] = mapped_column(String(32), default="0,1,2,3,4", nullable=False)
    work_start: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)  # HH:MM
    work_end: Mapped[str] = mapped_column(String(5), default="18:00", nullable=False)    # HH:MM

    # Weekly stats configuration (default: Saturday at 19:00)
    weekly_stats_day: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 5 = Saturday
    weekly_stats_time: Mapped[str] = mapped_column(String(5), default="19:00", nullable=False)  # HH:MM

    # Reminders and state
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reminded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    work_logs: Mapped[List[WorkLog]] = relationship(
        "WorkLog", back_populates="user", cascade="all, delete-orphan", order_by="desc(WorkLog.created_at)"
    )
    days_off: Mapped[List[DayOff]] = relationship(
        "DayOff", back_populates="user", cascade="all, delete-orphan", order_by="DayOff.date"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, chat_id={self.chat_id}, username='{self.username}')>"


class WorkLog(Base):
    """WorkLog model recording logged productive work or wasted time."""

    __tablename__ = "work_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'work' or 'waste'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="work_logs")

    def __repr__(self) -> str:
        return (
            f"<WorkLog(id={self.id}, user_id={self.user_id}, "
            f"type='{self.log_type}', hours={self.hours}, date={self.date})>"
        )


class DayOff(Base):
    """DayOff model storing planned or scheduled days off for users."""

    __tablename__ = "days_off"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="days_off")

    def __repr__(self) -> str:
        return f"<DayOff(id={self.id}, user_id={self.user_id}, date={self.date}, reason='{self.reason}')>"


def get_database_url() -> str:
    """Returns database connection URL from environment or default."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def init_db(db_url: Optional[str] = None):
    """Initializes database tables.

    Args:
        db_url: Optional database connection URL.
    Returns:
        tuple of (engine, sessionmaker)
    """
    url = db_url or get_database_url()
    engine = create_engine(url, echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return engine, session_factory
