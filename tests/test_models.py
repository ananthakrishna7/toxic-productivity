"""Unit tests for SQLAlchemy models in models.py."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import DayOff, User, WorkLog


def test_user_creation_and_defaults(db_session: Session):
    """Test user model instantiation and default column values."""
    user = User(
        chat_id=987654321,
        username="grinder",
        first_name="The Grinder",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.chat_id == 987654321
    assert user.username == "grinder"
    assert user.work_days == "0,1,2,3,4"
    assert user.work_start == "09:00"
    assert user.work_end == "18:00"
    assert user.weekly_stats_day == 5
    assert user.weekly_stats_time == "19:00"
    assert user.is_active is True
    assert isinstance(user.registered_at, datetime)


def test_user_worklog_relationship_and_cascade(db_session: Session):
    """Test relationship between User and WorkLog, including cascade deletion."""
    user = User(chat_id=111222, username="worker")
    db_session.add(user)
    db_session.commit()

    log1 = WorkLog(
        user_id=user.id,
        log_type="work",
        description="Building feature X",
        hours=3.5,
        date=date.today(),
    )
    log2 = WorkLog(
        user_id=user.id,
        log_type="waste",
        description="Coffee break and cat videos",
        hours=1.0,
        date=date.today(),
    )
    db_session.add_all([log1, log2])
    db_session.commit()

    # Verify query through relationship
    db_session.refresh(user)
    assert len(user.work_logs) == 2
    assert user.work_logs[0].hours in (3.5, 1.0)

    # Test cascade delete
    db_session.delete(user)
    db_session.commit()

    remaining_logs = db_session.execute(select(WorkLog)).scalars().all()
    assert len(remaining_logs) == 0


def test_user_dayoff_relationship_and_cascade(db_session: Session):
    """Test relationship between User and DayOff, including cascade deletion."""
    user = User(chat_id=333444, username="holidaylover")
    db_session.add(user)
    db_session.commit()

    day_off = DayOff(
        user_id=user.id,
        date=date(2026, 10, 1),
        reason="Vacation day",
    )
    db_session.add(day_off)
    db_session.commit()

    db_session.refresh(user)
    assert len(user.days_off) == 1
    assert user.days_off[0].reason == "Vacation day"

    # Delete user and ensure DayOff is cascade deleted
    db_session.delete(user)
    db_session.commit()

    remaining_days = db_session.execute(select(DayOff)).scalars().all()
    assert len(remaining_days) == 0
