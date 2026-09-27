"""Unit tests for services.py business logic and domain operations."""

from datetime import date, time, timedelta

import pytest
from sqlalchemy.orm import Session

import services
from models import User


def test_get_or_create_user(db_session: Session):
    """Test user registration and subsequent profile updates."""
    user, created = services.get_or_create_user(
        db_session, chat_id=1001, username="drone1", first_name="Drone One"
    )
    assert created is True
    assert user.chat_id == 1001
    assert user.username == "drone1"
    assert user.first_name == "Drone One"

    # Second call should retrieve existing user and update details if modified
    user2, created2 = services.get_or_create_user(
        db_session, chat_id=1001, username="drone1_updated", first_name="Drone Prime"
    )
    assert created2 is False
    assert user2.id == user.id
    assert user2.username == "drone1_updated"
    assert user2.first_name == "Drone Prime"


def test_parse_log_input():
    """Test various input patterns for /log command."""
    # Standard: /log <type> <desc> <hours>
    t, d, h = services.parse_log_input("/log work coding rust backend 3.5")
    assert t == "work"
    assert d == "coding rust backend"
    assert h == 3.5

    # Waste: /log waste <desc> <hours>
    t, d, h = services.parse_log_input("/log waste youtube rabbit hole 1.5")
    assert t == "waste"
    assert d == "youtube rabbit hole"
    assert h == 1.5

    # Alternate: /log <type> <hours> <desc>
    t, d, h = services.parse_log_input("/log work 2 fixing tests")
    assert t == "work"
    assert d == "fixing tests"
    assert h == 2.0

    # Hours with 'h' / 'hrs' suffix
    t, d, h = services.parse_log_input("/log work writing documentation 4h")
    assert t == "work"
    assert d == "writing documentation"
    assert h == 4.0

    t, d, h = services.parse_log_input("/log waste 2.5hrs doomscrolling")
    assert t == "waste"
    assert d == "doomscrolling"
    assert h == 2.5


def test_parse_log_input_errors():
    """Test invalid /log inputs raise clear ValueErrors."""
    with pytest.raises(ValueError, match="Missing parameters"):
        services.parse_log_input("/log")

    with pytest.raises(ValueError, match="Invalid activity type"):
        services.parse_log_input("/log sleeping on keyboard 2")

    with pytest.raises(ValueError, match="Could not parse hours"):
        services.parse_log_input("/log work just sitting here")


def test_add_work_log_and_daily_summary(db_session: Session, sample_user: User):
    """Test logging activities and computing daily summary."""
    today = date.today()
    services.add_work_log(db_session, sample_user, "work", "Deep coding", 4.0, today)
    services.add_work_log(db_session, sample_user, "work", "Code review", 1.5, today)
    services.add_work_log(db_session, sample_user, "waste", "Social media", 1.0, today)

    summary = services.get_daily_summary(db_session, sample_user, today)
    assert summary["work_hours"] == 5.5
    assert summary["waste_hours"] == 1.0
    assert summary["total_hours"] == 6.5
    assert summary["net_hours"] == 4.5
    assert len(summary["logs"]) == 3


def test_daily_leaderboard(db_session: Session):
    """Test leaderboard ranking calculation across multiple users."""
    u1, _ = services.get_or_create_user(db_session, chat_id=1, username="alice", first_name="Alice")
    u2, _ = services.get_or_create_user(db_session, chat_id=2, username="bob", first_name="Bob")
    u3, _ = services.get_or_create_user(db_session, chat_id=3, username="slacker", first_name="Slacker")

    today = date.today()
    # Alice worked 7 hours, wasted 0.5
    services.add_work_log(db_session, u1, "work", "Feature build", 7.0, today)
    services.add_work_log(db_session, u1, "waste", "Slack talk", 0.5, today)

    # Bob worked 4 hours, wasted 1
    services.add_work_log(db_session, u2, "work", "Bugs", 4.0, today)
    services.add_work_log(db_session, u2, "waste", "Cat videos", 1.0, today)

    # Slacker worked 0 hours, wasted 3 hours
    services.add_work_log(db_session, u3, "waste", "Gaming", 3.0, today)

    leaderboard = services.get_daily_leaderboard(db_session, today)
    assert len(leaderboard) == 3

    assert leaderboard[0]["name"] == "Alice"
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["work_hours"] == 7.0

    assert leaderboard[1]["name"] == "Bob"
    assert leaderboard[1]["rank"] == 2
    assert leaderboard[1]["work_hours"] == 4.0

    assert leaderboard[2]["name"] == "Slacker"
    assert leaderboard[2]["rank"] == 3
    assert leaderboard[2]["work_hours"] == 0.0


def test_weekly_stats(db_session: Session, sample_user: User):
    """Test weekly stats calculation over a 7-day window."""
    today = date.today()
    three_days_ago = today - timedelta(days=3)
    ten_days_ago = today - timedelta(days=10)

    # Within weekly range
    services.add_work_log(db_session, sample_user, "work", "Sprint task 1", 5.0, today)
    services.add_work_log(db_session, sample_user, "work", "Sprint task 2", 3.0, three_days_ago)
    services.add_work_log(db_session, sample_user, "waste", "Procrastination", 2.0, three_days_ago)

    # Out of weekly range (should be ignored)
    services.add_work_log(db_session, sample_user, "work", "Old sprint task", 8.0, ten_days_ago)

    stats = services.get_weekly_stats(db_session, sample_user, today)
    assert stats["work_hours"] == 8.0
    assert stats["waste_hours"] == 2.0
    assert stats["net_hours"] == 6.0
    assert stats["logs_count"] == 3


def test_workdays_parsing_and_formatting():
    """Test parsing workdays specs and formatting text."""
    assert services.parse_workdays_spec("weekdays") == [0, 1, 2, 3, 4]
    assert services.parse_workdays_spec("weekends-off") == [0, 1, 2, 3, 4]
    assert services.parse_workdays_spec("sundays-off") == [0, 1, 2, 3, 4, 5]
    assert services.parse_workdays_spec("all") == [0, 1, 2, 3, 4, 5, 6]
    assert services.parse_workdays_spec("mon,wed,fri") == [0, 2, 4]

    formatted = services.format_workdays("0,2,4")
    assert formatted == "Mon, Wed, Fri"


def test_set_user_workdays_and_workhours(db_session: Session, sample_user: User):
    """Test updating user schedule settings."""
    formatted = services.set_user_workdays(db_session, sample_user, "mon,tue,wed")
    assert formatted == "Mon, Tue, Wed"
    assert sample_user.work_days == "0,1,2"

    start_fmt, end_fmt = services.set_user_workhours(db_session, sample_user, "08:30", "17:15")
    assert start_fmt == "08:30"
    assert end_fmt == "17:15"
    assert sample_user.work_start == "08:30"
    assert sample_user.work_end == "17:15"


def test_days_off_scheduling(db_session: Session, sample_user: User):
    """Test scheduling, checking, and cancelling planned days off."""
    tomorrow = date.today() + timedelta(days=1)
    day_off, created = services.add_day_off(db_session, sample_user, tomorrow, "Conference")
    assert created is True
    assert day_off.reason == "Conference"

    # Verify duplicate handling updates reason
    day_off2, created2 = services.add_day_off(db_session, sample_user, tomorrow, "Updated Conference")
    assert created2 is False
    assert day_off2.reason == "Updated Conference"

    upcoming = services.get_upcoming_days_off(db_session, sample_user)
    assert len(upcoming) == 1
    assert upcoming[0].date == tomorrow

    # Verify is_workday respects DayOff
    # Even if tomorrow's weekday is in work_days, day off makes is_workday False
    sample_user.work_days = "0,1,2,3,4,5,6"  # All days
    assert services.is_workday(db_session, sample_user, tomorrow) is False

    # Remove day off
    removed = services.remove_day_off(db_session, sample_user, tomorrow)
    assert removed is True
    assert services.is_workday(db_session, sample_user, tomorrow) is True


def test_is_within_work_hours(sample_user: User):
    """Test work hours window checking."""
    sample_user.work_start = "09:00"
    sample_user.work_end = "18:00"

    assert services.is_within_work_hours(sample_user, time(9, 30)) is True
    assert services.is_within_work_hours(sample_user, time(17, 59)) is True
    assert services.is_within_work_hours(sample_user, time(8, 59)) is False
    assert services.is_within_work_hours(sample_user, time(18, 30)) is False


def test_undo_last_work_log(db_session: Session, sample_user: User):
    """Test undoing the most recently created log."""
    assert services.undo_last_work_log(db_session, sample_user) is None

    log1 = services.add_work_log(db_session, sample_user, "work", "First task", 1.0)
    log2 = services.add_work_log(db_session, sample_user, "waste", "Second task", 2.0)

    undone = services.undo_last_work_log(db_session, sample_user)
    assert undone is not None
    assert undone.id == log2.id
    assert undone.description == "Second task"

    # Only log1 remains
    remaining = services.get_user_recent_logs(db_session, sample_user)
    assert len(remaining) == 1
    assert remaining[0].id == log1.id


def test_delete_work_log(db_session: Session, sample_user: User):
    """Test deleting an entry by ID, and enforcing user ownership."""
    log1 = services.add_work_log(db_session, sample_user, "work", "Task A", 1.5)
    log2 = services.add_work_log(db_session, sample_user, "work", "Task B", 2.5)

    # Deleting non-existent log returns None
    assert services.delete_work_log(db_session, sample_user, 99999) is None

    # Deleting existing log succeeds
    deleted = services.delete_work_log(db_session, sample_user, log1.id)
    assert deleted is not None
    assert deleted.id == log1.id

    remaining = services.get_user_recent_logs(db_session, sample_user)
    assert len(remaining) == 1
    assert remaining[0].id == log2.id


def test_edit_work_log_and_parse_input(db_session: Session, sample_user: User):
    """Test modifying existing logs and parsing partial updates."""
    log = services.add_work_log(db_session, sample_user, "work", "Initial Task", 2.0)

    # Test parse_edit_input for hours only
    new_type, new_desc, new_hours = services.parse_edit_input(["3.5"], log)
    assert new_type == "work"
    assert new_desc == "Initial Task"
    assert new_hours == 3.5

    # Test parse_edit_input for type change and description
    new_type2, new_desc2, new_hours2 = services.parse_edit_input(["waste", "Doomscrolling", "1.0"], log)
    assert new_type2 == "waste"
    assert new_desc2 == "Doomscrolling"
    assert new_hours2 == 1.0

    # Apply edit
    updated = services.edit_work_log(db_session, sample_user, log.id, new_type2, new_desc2, new_hours2)
    assert updated is not None
    assert updated.log_type == "waste"
    assert updated.description == "Doomscrolling"
    assert updated.hours == 1.0

