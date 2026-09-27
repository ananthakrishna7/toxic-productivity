"""Unit tests for background jobs in scheduler.py."""

from datetime import date, timedelta

import pytest

import scheduler
import services
from models import User, WorkLog, utc_now


@pytest.mark.asyncio
async def test_check_reminders_job_sends_when_due(
    mock_context, sample_user: User, db_session_factory
):
    """Test 4-hour reminder job triggers when 4 hours elapsed with no logs."""
    # Configure user so now is within work hours and workday
    with db_session_factory() as session:
        u = services.get_user_by_chat_id(session, sample_user.chat_id)
        u.work_start = "00:00"
        u.work_end = "23:59"
        u.work_days = "0,1,2,3,4,5,6"  # All days
        u.last_reminded_at = utc_now() - timedelta(hours=5)
        session.commit()

    await scheduler.check_reminders_job(mock_context)

    mock_context.bot.send_message.assert_called_once()
    assert "4-HOUR PRODUCTIVITY CHECK-IN" in mock_context.bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_check_reminders_job_skips_if_recent_log(
    mock_context, sample_user: User, db_session_factory
):
    """Test 4-hour reminder job skips if user has logged in the last 4 hours."""
    with db_session_factory() as session:
        u = services.get_user_by_chat_id(session, sample_user.chat_id)
        u.work_start = "00:00"
        u.work_end = "23:59"
        u.work_days = "0,1,2,3,4,5,6"
        u.last_reminded_at = utc_now() - timedelta(hours=5)
        # Add log 1 hour ago
        log = WorkLog(
            user_id=u.id,
            log_type="work",
            description="Active task",
            hours=1.0,
            date=date.today(),
            created_at=utc_now() - timedelta(hours=1),
        )
        session.add(log)
        session.commit()

    await scheduler.check_reminders_job(mock_context)
    mock_context.bot.send_message.assert_not_called()
