"""Unit tests for Telegram command handlers, callbacks, and inline queries in handlers.py."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

import handlers
import services
from models import User


@pytest.mark.asyncio
async def test_start_command_registers_new_user(mock_context, make_mock_update, db_session_factory):
    """Test /start registers a user and responds with greeting."""
    update = make_mock_update(chat_id=999, username="newuser", first_name="Newbie", text="/start")

    await handlers.start(update, mock_context)

    # Verify message sent
    mock_context.bot.send_message.assert_called_once()
    call_args = mock_context.bot.send_message.call_args[1]
    assert call_args["chat_id"] == 999
    assert "Welcome to Toxic Productivity" in call_args["text"]

    # Verify user exists in database
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, 999)
        assert user is not None
        assert user.username == "newuser"


@pytest.mark.asyncio
async def test_unregistered_user_blocked(mock_context, make_mock_update):
    """Test commands decorated with @require_registration reject unregistered users."""
    update = make_mock_update(chat_id=888, username="stranger", text="/summary")

    await handlers.summary_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    call_args = mock_context.bot.send_message.call_args[1]
    assert "Access Denied: Unregistered Slacker" in call_args["text"]


@pytest.mark.asyncio
async def test_log_command_work_and_waste(mock_context, make_mock_update, sample_user: User, db_session_factory):
    """Test registered user logging work and waste."""
    # 1. Log work
    update = make_mock_update(
        chat_id=sample_user.chat_id,
        username=sample_user.username,
        text="/log work implemented auth endpoint 2.5",
    )
    await handlers.log_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    sent_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "WORK LOGGED" in sent_text
    assert "2.5 hours" in sent_text

    # 2. Log waste
    mock_context.bot.send_message.reset_mock()
    update2 = make_mock_update(
        chat_id=sample_user.chat_id,
        username=sample_user.username,
        text="/log waste playing chess 1.0",
    )
    await handlers.log_command(update2, mock_context)

    sent_text2 = mock_context.bot.send_message.call_args[1]["text"]
    assert "WASTE LOGGED" in sent_text2
    assert "1.0 hours" in sent_text2

    # Verify database entries
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        summary = services.get_daily_summary(session, user, date.today())
        assert summary["work_hours"] == 2.5
        assert summary["waste_hours"] == 1.0


@pytest.mark.asyncio
async def test_summary_and_leaderboard_commands(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /summary and /leaderboard commands produce formatted responses."""
    # Add a work log
    with db_session_factory() as session:
        u = services.get_user_by_chat_id(session, sample_user.chat_id)
        services.add_work_log(session, u, "work", "Test task", 3.0, date.today())

    # Summary
    update = make_mock_update(chat_id=sample_user.chat_id, text="/summary")
    await handlers.summary_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    summary_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "DAILY SUMMARY" in summary_text
    assert "3.0 hrs" in summary_text

    # Leaderboard
    mock_context.bot.send_message.reset_mock()
    update_lb = make_mock_update(chat_id=sample_user.chat_id, text="/leaderboard")
    await handlers.leaderboard_command(update_lb, mock_context)

    mock_context.bot.send_message.assert_called_once()
    lb_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "DAILY LEADERBOARD" in lb_text
    assert "Corporate Overlord" in lb_text


@pytest.mark.asyncio
async def test_workdays_and_workhours_commands(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /workdays and /workhours commands."""
    update = make_mock_update(chat_id=sample_user.chat_id, text="/workdays weekdays")
    mock_context.args = ["weekdays"]
    await handlers.workdays_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    assert "Workdays updated" in mock_context.bot.send_message.call_args[1]["text"]

    # Workhours
    mock_context.bot.send_message.reset_mock()
    update_wh = make_mock_update(chat_id=sample_user.chat_id, text="/workhours 10:00-19:00")
    mock_context.args = ["10:00-19:00"]
    await handlers.workhours_command(update_wh, mock_context)

    assert "Work hours set" in mock_context.bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_dayoff_and_cancel_commands(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /dayoff and /cancel_dayoff commands."""
    update = make_mock_update(chat_id=sample_user.chat_id, text="/dayoff tomorrow Sick leave")
    mock_context.args = ["tomorrow", "Sick", "leave"]
    await handlers.dayoff_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    assert "Scheduled Day Off" in mock_context.bot.send_message.call_args[1]["text"]

    # Cancel day off
    mock_context.bot.send_message.reset_mock()
    update_cancel = make_mock_update(chat_id=sample_user.chat_id, text="/cancel_dayoff tomorrow")
    mock_context.args = ["tomorrow"]
    await handlers.cancel_dayoff_command(update_cancel, mock_context)

    assert "cancelled" in mock_context.bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_button_callback_handler_prompts_description(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test inline keyboard button clicks prompt user for task description."""
    mock_context.user_data = {}
    update = make_mock_update(
        chat_id=sample_user.chat_id,
        is_callback=True,
        callback_data="quick_work_1",
    )
    await handlers.button_callback_handler(update, mock_context)

    update.callback_query.answer.assert_called_once()
    mock_context.bot.send_message.assert_called_once()
    assert "Logging 1.0h of Work" in mock_context.bot.send_message.call_args[1]["text"]
    assert mock_context.user_data.get("pending_log") == {"type": "work", "hours": 1.0}


@pytest.mark.asyncio
async def test_text_message_fulfills_pending_description(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test sending text description fulfills pending log."""
    mock_context.user_data = {"pending_log": {"type": "work", "hours": 1.0}}
    update = make_mock_update(
        chat_id=sample_user.chat_id,
        text="Refactored database schema",
    )
    await handlers.text_message_handler(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    sent_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "WORK LOGGED" in sent_text
    assert "Refactored database schema" in sent_text
    assert "pending_log" not in mock_context.user_data

    # Verify saved in database
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        recent = services.get_user_recent_logs(session, user)
        assert len(recent) == 1
        assert recent[0].description == "Refactored database schema"


@pytest.mark.asyncio
async def test_skip_description_callback(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test tapping Skip Description logs with default task description."""
    mock_context.user_data = {"pending_log": {"type": "work", "hours": 1.0}}
    update = make_mock_update(
        chat_id=sample_user.chat_id,
        is_callback=True,
        callback_data="skip_desc_work_1",
    )
    await handlers.button_callback_handler(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    assert "General Work" in mock_context.bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_undo_and_delete_commands(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /undo and /delete commands remove entries from database."""
    # Add two logs
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        log1 = services.add_work_log(session, user, "work", "Task 1", 1.0)
        log2 = services.add_work_log(session, user, "waste", "Task 2", 2.0)

    # 1. Test /undo (should remove log2)
    update_undo = make_mock_update(chat_id=sample_user.chat_id, text="/undo")
    await handlers.undo_command(update_undo, mock_context)

    mock_context.bot.send_message.assert_called_once()
    assert f"REVERTED ENTRY (ID #{log2.id})" in mock_context.bot.send_message.call_args[1]["text"]

    # 2. Test /delete log1.id
    mock_context.bot.send_message.reset_mock()
    update_del = make_mock_update(chat_id=sample_user.chat_id, text=f"/delete {log1.id}")
    mock_context.args = [str(log1.id)]
    await handlers.delete_command(update_del, mock_context)

    assert f"DELETED ENTRY (ID #{log1.id})" in mock_context.bot.send_message.call_args[1]["text"]

    # Database should now be empty
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        assert len(services.get_user_recent_logs(session, user)) == 0


@pytest.mark.asyncio
async def test_edit_command(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /edit command updates entry values."""
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        log = services.add_work_log(session, user, "work", "Old Title", 1.0)

    update = make_mock_update(chat_id=sample_user.chat_id, text=f"/edit {log.id} New Title 2.5")
    mock_context.args = [str(log.id), "New", "Title", "2.5"]
    await handlers.edit_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    sent_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "UPDATED ENTRY" in sent_text
    assert "New Title" in sent_text
    assert "2.5 hrs" in sent_text


@pytest.mark.asyncio
async def test_logs_command(
    mock_context, make_mock_update, sample_user: User, db_session_factory
):
    """Test /logs command lists entries with IDs."""
    with db_session_factory() as session:
        user = services.get_user_by_chat_id(session, sample_user.chat_id)
        services.add_work_log(session, user, "work", "Important Meeting", 1.5)

    update = make_mock_update(chat_id=sample_user.chat_id, text="/logs")
    await handlers.logs_command(update, mock_context)

    mock_context.bot.send_message.assert_called_once()
    sent_text = mock_context.bot.send_message.call_args[1]["text"]
    assert "RECENT ACTIVITY LOGS" in sent_text
    assert "Important Meeting" in sent_text


@pytest.mark.asyncio
async def test_inline_query_handler(mock_context, sample_user: User, db_session_factory):
    """Test inline query handler returns articles for sharing summary and leaderboard."""
    update = MagicMock()
    inline_query = AsyncMock()
    inline_query.from_user = MagicMock(id=sample_user.chat_id)
    inline_query.query = ""
    update.inline_query = inline_query

    await handlers.inline_query_handler(update, mock_context)

    inline_query.answer.assert_called_once()
    results = inline_query.answer.call_args[0][0]
    assert len(results) >= 4
    result_ids = [r.id for r in results]
    assert "my_summary" in result_ids
    assert "leaderboard" in result_ids
    assert "log_work_template" in result_ids
    assert "toxic_nudge" in result_ids
