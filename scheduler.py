"""Scheduled background jobs for Toxic Productivity Bot.

Manages:
1. 4-hour reminder nudges during active work hours.
2. End-of-Day (EoD) personal summaries and community leaderboards.
3. Weekly performance recaps and toxic awards (default Saturday 19:00, configurable).
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from telegram.error import TelegramError
from telegram.ext import Application, ContextTypes

import handlers
import services
import toxic_quotes
from models import User, WorkLog, utc_now

logger = logging.getLogger(__name__)


def _get_session(context: ContextTypes.DEFAULT_TYPE):
    session_factory = context.bot_data.get("session_factory")
    if not session_factory:
        raise RuntimeError("session_factory not configured in bot_data")
    return session_factory()


async def check_reminders_job(context: ContextTypes.DEFAULT_TYPE):
    """Checks active users and sends a toxic reminder if 4 hours have passed during work hours."""
    now = utc_now()
    today = now.date()

    with _get_session(context) as session:
        users = list(
            session.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712
        )

        for user in users:
            # 1. Check if today is a workday for user
            if not services.is_workday(session, user, today):
                continue

            # 2. Check if within working hours
            if not services.is_within_work_hours(user, now.time()):
                continue

            # 3. Check elapsed time since last reminder or work start
            hours_since_reminder = 999.0
            if user.last_reminded_at:
                hours_since_reminder = (now - user.last_reminded_at).total_seconds() / 3600.0

            if hours_since_reminder < 4.0:
                continue

            # 4. Check if user logged any activity in the last 4 hours
            four_hours_ago = now - timedelta(hours=4)
            recent_log = session.execute(
                select(WorkLog)
                .where(WorkLog.user_id == user.id, WorkLog.created_at >= four_hours_ago)
                .limit(1)
            ).scalar_one_or_none()

            if recent_log:
                # User logged recently, postpone reminder
                user.last_reminded_at = now
                session.commit()
                continue

            # 5. Send 4-hour toxic reminder
            quote = toxic_quotes.get_reminder_quote()
            name = user.first_name or user.username or "Drone"
            message_text = (
                f"⏰ *4-HOUR PRODUCTIVITY CHECK-IN!*\n\n"
                f"Hey `{name}`, silence has reigned for 4 hours.\n\n"
                f"_{quote}_\n\n"
                f"What did you work on (or waste)? Tap below or use `/log`:"
            )

            try:
                await context.bot.send_message(
                    chat_id=user.chat_id,
                    text=message_text,
                    reply_markup=handlers.get_main_keyboard(),
                    parse_mode="Markdown",
                )
                user.last_reminded_at = now
                session.commit()
                logger.info("Sent 4-hour reminder to user %s (%d)", name, user.chat_id)
            except TelegramError as e:
                logger.warning("Failed to send reminder to %d: %s", user.chat_id, e)


async def eod_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """Sends EoD personal summary and daily leaderboard to active users at the end of their workday."""
    now = utc_now()
    today = now.date()

    with _get_session(context) as session:
        users = list(
            session.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712
        )
        if not users:
            return

        leaderboard = services.get_daily_leaderboard(session, today)
        leaderboard_text = handlers.format_leaderboard_text(leaderboard, today)

        for user in users:
            if not services.is_workday(session, user, today):
                continue

            # Trigger if within window of user's work_end (e.g. matching HH:MM or default 18:00)
            end_h, end_m = user.work_end.split(":")
            if now.hour == int(end_h) and abs(now.minute - int(end_m)) <= 15:
                summary = services.get_daily_summary(session, user, today)
                name = user.first_name or user.username or "Drone"
                summary_text = handlers.format_daily_summary_text(summary, name)

                full_eod = (
                    f"🏁 *END OF DAY REPORT*\n\n"
                    f"{summary_text}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{leaderboard_text}"
                )

                try:
                    await context.bot.send_message(
                        chat_id=user.chat_id,
                        text=full_eod,
                        reply_markup=handlers.get_main_keyboard(),
                        parse_mode="Markdown",
                    )
                    logger.info("Sent EoD summary to user %s", name)
                except TelegramError as e:
                    logger.warning("Failed to send EoD to %d: %s", user.chat_id, e)


async def weekly_stats_job(context: ContextTypes.DEFAULT_TYPE):
    """Sends weekly stats report every Saturday at 19:00 (or user configured day/time)."""
    now = utc_now()
    today = now.date()
    current_weekday = today.weekday()

    with _get_session(context) as session:
        users = list(
            session.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712
        )
        if not users:
            return

        board = services.get_weekly_leaderboard(session, today)
        total_users = len(board)

        for user in users:
            # Check configured day and time
            if user.weekly_stats_day == current_weekday:
                stat_h, stat_m = user.weekly_stats_time.split(":")
                if now.hour == int(stat_h) and abs(now.minute - int(stat_m)) <= 15:
                    stats = services.get_weekly_stats(session, user, today)
                    rank = 1
                    for entry in board:
                        if entry["user"].id == user.id:
                            rank = entry["rank"]
                            break

                    name = user.first_name or user.username or "Drone"
                    text = handlers.format_weekly_stats_text(stats, name, rank, total_users)

                    try:
                        await context.bot.send_message(
                            chat_id=user.chat_id,
                            text=text,
                            reply_markup=handlers.get_main_keyboard(),
                            parse_mode="Markdown",
                        )
                        logger.info("Sent scheduled weekly stats to user %s", name)
                    except TelegramError as e:
                        logger.warning("Failed to send weekly stats to %d: %s", user.chat_id, e)


def setup_scheduler(application: Application):
    """Configures scheduled background jobs in the telegram Application JobQueue."""
    job_queue = application.job_queue
    if not job_queue:
        logger.warning("JobQueue is not available in application. Background jobs disabled.")
        return

    # Check 4-hour reminders every 30 minutes
    job_queue.run_repeating(
        check_reminders_job,
        interval=1800,  # 30 minutes
        first=60,       # 1 minute after startup
        name="check_reminders",
    )

    # Check EoD summaries every 15 minutes
    job_queue.run_repeating(
        eod_summary_job,
        interval=900,  # 15 minutes
        first=120,
        name="eod_summary",
    )

    # Check weekly stats every 15 minutes
    job_queue.run_repeating(
        weekly_stats_job,
        interval=900,  # 15 minutes
        first=180,
        name="weekly_stats",
    )

    logger.info("Configured background reminder and summary jobs.")
