"""Telegram bot command handlers, callbacks, and inline query handlers.

Implements registration enforcement, activity logging, summaries,
workday/schedule management, inline keyboard callbacks, and inline queries.
"""

from __future__ import annotations

import functools
import logging
from datetime import date
from typing import Callable

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import ContextTypes

import services
import toxic_quotes

logger = logging.getLogger(__name__)


def get_db_session(context: ContextTypes.DEFAULT_TYPE):
    """Retrieves a new SQLAlchemy session from context.bot_data."""
    session_factory = context.bot_data.get("session_factory")
    if not session_factory:
        raise RuntimeError("Database session factory is not configured in bot_data.")
    return session_factory()


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Returns persistent inline buttons for quick productivity actions."""
    keyboard = [
        [
            InlineKeyboardButton("💼 +1h Work", callback_data="quick_work_1"),
            InlineKeyboardButton("🗑️ +1h Waste", callback_data="quick_waste_1"),
        ],
        [
            InlineKeyboardButton("📊 Today's Summary", callback_data="view_summary"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="view_leaderboard"),
        ],
        [
            InlineKeyboardButton("📅 My Schedule", callback_data="view_schedule"),
            InlineKeyboardButton("📈 Weekly Stats", callback_data="view_weekly"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def require_registration(func: Callable):
    """Decorator to enforce user registration before accessing commands."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_tg = update.effective_user
        chat = update.effective_chat
        if not user_tg or not chat:
            return

        with get_db_session(context) as session:
            user = services.get_user_by_chat_id(session, chat.id)
            if not user or not user.is_active:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        "🚫 *Access Denied: Unregistered Slacker!*\n\n"
                        "You must register before logging your (lack of) productivity.\n"
                        "Run `/start` or `/register` to submit yourself to toxic accountability."
                    ),
                    parse_mode="Markdown",
                )
                return

        return await func(update, context, *args, **kwargs)

    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command. Registers user and presents toxic greeting."""
    user_tg = update.effective_user
    chat = update.effective_chat
    if not user_tg or not chat:
        return

    with get_db_session(context) as session:
        user, created = services.get_or_create_user(
            session=session,
            chat_id=chat.id,
            username=user_tg.username,
            first_name=user_tg.first_name,
        )

    greeting_name = user.first_name or user.username or "Corporate Drone"
    if created:
        text = (
            f"😈 *Welcome to Toxic Productivity, {greeting_name}!*\n\n"
            f"You are officially registered. The honeymoon phase ends right now.\n"
            f"Here, we track your productive hours, shame your wasted time, and pit you "
            f"against others on the daily leaderboard.\n\n"
            f"📌 *Default Schedule:* Mon-Fri, 09:00 - 18:00\n"
            f"⏰ *Reminders:* Every 4 hours during workdays.\n"
            f"📊 *Weekly Stats:* Saturdays at 19:00\n\n"
            f"Type `/help` to see commands or tap below to start logging:"
        )
    else:
        text = (
            f"😈 *Back already, {greeting_name}?*\n\n"
            f"Hopefully you're here to log actual work rather than just admiring your bot.\n"
            f"What have you accomplished recently?"
        )

    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /register [username]. Explicit registration command."""
    user_tg = update.effective_user
    chat = update.effective_chat
    if not user_tg or not chat:
        return

    custom_name = " ".join(context.args).strip() if context.args else None

    with get_db_session(context) as session:
        user, created = services.get_or_create_user(
            session=session,
            chat_id=chat.id,
            username=user_tg.username,
            first_name=custom_name or user_tg.first_name,
        )

    name = user.first_name or user.username or "Drone"
    status_str = "Successfully registered" if created else "Profile updated"
    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            f"✅ *{status_str}!* Welcome, `{name}`.\n"
            f"You are bound to the wheel of toxic accountability. Use `/help` to view all commands."
        ),
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /help command. Lists available commands and usage instructions."""
    help_text = (
        "🤖 *TOXIC PRODUCTIVITY BOT — COMMAND CHEATSHEET*\n\n"
        "⚡ *Core Tracking:*\n"
        "• `/log work <desc> <hours>` — Log productive work (e.g. `/log work refactoring 2.5`)\n"
        "• `/log waste <desc> <hours>` — Log wasted time (e.g. `/log waste doomscrolling 1`)\n"
        "• `/summary` or `/today` — View your today's breakdown and toxic roast\n"
        "• `/leaderboard` — Compare today's output with all users\n"
        "• `/weekly` or `/stats` — View your 7-day stats and toxic trophy\n\n"
        "⚙️ *Schedule & Workdays:*\n"
        "• `/workdays <spec>` — Set days (e.g. `weekdays`, `sundays-off`, `mon,wed,fri`)\n"
        "• `/workhours <start>-<end>` — Set hours (e.g. `/workhours 09:00-18:00`)\n"
        "• `/dayoff <date> [reason]` — Plan a day off (e.g. `/dayoff tomorrow Sick`)\n"
        "• `/days_off` — List upcoming planned days off\n"
        "• `/cancel_dayoff <date>` — Cancel a planned day off\n"
        "• `/config weekly <day> <time>` — Set weekly stats time (e.g. `/config weekly Sat 19:00`)\n"
        "• `/settings` — View your full current configuration\n\n"
        "💡 *Inline Features:*\n"
        "• Type `@your_bot_name` in any chat to share your summary or leaderboard inline!\n"
        "• Use the buttons below for fast 1-click logging."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


@require_registration
async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /log <type> <description> <hours>."""
    chat = update.effective_chat
    user_tg = update.effective_user
    if not chat or not user_tg:
        return

    full_text = update.message.text if update.message else ""
    try:
        log_type, description, hours = services.parse_log_input(full_text)
    except ValueError as e:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ *Invalid Format:*\n{e}",
            parse_mode="Markdown",
        )
        return

    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        services.add_work_log(
            session=session,
            user=user,
            log_type=log_type,
            description=description,
            hours=hours,
            log_date=date.today(),
        )

    # Pick sarcastic toxic quote
    if log_type == "work":
        nudge = toxic_quotes.get_work_quote(hours, description)
        icon = "💼"
    else:
        nudge = toxic_quotes.get_waste_quote(hours, description)
        icon = "🗑️"

    response = (
        f"{icon} *{log_type.upper()} LOGGED:*\n"
        f"• *Task:* `{description}`\n"
        f"• *Duration:* `{hours:.1f} hours`\n\n"
        f"_{nudge}_"
    )
    await context.bot.send_message(
        chat_id=chat.id,
        text=response,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


def format_daily_summary_text(summary: dict, user_name: str) -> str:
    """Formats daily summary dict into a stylized Markdown string."""
    work_h = summary["work_hours"]
    waste_h = summary["waste_hours"]
    net_h = summary["net_hours"]
    logs = summary["logs"]
    nudge = toxic_quotes.get_eod_quote(work_h, waste_h)

    lines = [
        f"📊 *DAILY SUMMARY — {summary['date'].strftime('%A, %b %d')}*",
        f"👤 *Subject:* `{user_name}`",
        "━━━━━━━━━━━━━━━━━━━",
        f"💼 *Productive Work:* `{work_h:.1f} hrs`",
        f"🗑️ *Wasted Time:* `{waste_h:.1f} hrs`",
        f"⚡ *Net Productivity:* `{net_h:+.1f} hrs`",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    if logs:
        lines.append("📋 *Activity Log:*")
        for idx, entry in enumerate(logs, 1):
            icon = "💼" if entry.log_type == "work" else "🗑️"
            lines.append(f"{idx}. {icon} `{entry.description}` ({entry.hours:.1f}h)")
    else:
        lines.append("🕸️ *No activities logged today. Peak laziness detected.*")

    lines.append(f"\n_{nudge}_")
    return "\n".join(lines)


@require_registration
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /summary or /today or /eod command."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        summary = services.get_daily_summary(session, user, date.today())
        name = user.first_name or user.username or "Drone"

    text = format_daily_summary_text(summary, name)
    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


def format_leaderboard_text(leaderboard: list, target_date: date) -> str:
    """Formats leaderboard list into a stylized Markdown ranking."""
    total_users = len(leaderboard)
    lines = [
        f"🏆 *DAILY LEADERBOARD — {target_date.strftime('%b %d, %Y')}*",
        f"Total active participants: {total_users}\n",
    ]

    if not leaderboard:
        lines.append("No active users found.")
        return "\n".join(lines)

    for entry in leaderboard:
        rank = entry["rank"]
        name = entry["name"]
        work_h = entry["work_hours"]
        waste_h = entry["waste_hours"]
        title = toxic_quotes.get_leaderboard_title(rank, total_users)

        lines.append(
            f"#{rank} *{name}* — {title}\n"
            f"   ↳ 💼 `{work_h:.1f}h work` | 🗑️ `{waste_h:.1f}h waste`\n"
        )

    # Random bottom roast
    lines.append(
        "_Remember: If you're not at the top, you're merely funding someone else's bonus._"
    )
    return "\n".join(lines)


@require_registration
async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /leaderboard command."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        leaderboard = services.get_daily_leaderboard(session, date.today())

    text = format_leaderboard_text(leaderboard, date.today())
    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


def format_weekly_stats_text(stats: dict, user_name: str, rank: int, total_users: int) -> str:
    """Formats weekly statistics into Markdown."""
    start_str = stats["start_date"].strftime("%b %d")
    end_str = stats["end_date"].strftime("%b %d, %Y")
    work_h = stats["work_hours"]
    waste_h = stats["waste_hours"]
    net_h = stats["net_hours"]
    award = toxic_quotes.get_weekly_award(rank, work_h, waste_h)

    lines = [
        f"📈 *WEEKLY REPORT: {start_str} - {end_str}*",
        f"👤 *Drone:* `{user_name}` (Rank #{rank} of {total_users})",
        "━━━━━━━━━━━━━━━━━━━━",
        f"💼 *Total Work:* `{work_h:.1f} hrs`",
        f"🗑️ *Total Waste:* `{waste_h:.1f} hrs`",
        f"⚡ *Net Productivity:* `{net_h:+.1f} hrs`",
        f"🎖️ *Weekly Title:* {award}",
        "━━━━━━━━━━━━━━━━━━━━",
        "📅 *Daily Breakdown:*",
    ]

    for d, d_stats in stats["daily_breakdown"].items():
        w = d_stats["work"]
        s = d_stats["waste"]
        day_name = d.strftime("%a (%b %d)")
        bar = "🟩" * int(w // 2) if w > 0 else "⬜"
        lines.append(f"• `{day_name}`: {w:.1f}h work / {s:.1f}h waste {bar}")

    nudge = toxic_quotes.get_eod_quote(work_h / 5.0, waste_h / 5.0)
    lines.append(f"\n_{nudge}_")
    return "\n".join(lines)


@require_registration
async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /weekly or /stats command. Shows 7-day stats and weekly leaderboard rank."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        stats = services.get_weekly_stats(session, user, date.today())
        board = services.get_weekly_leaderboard(session, date.today())
        rank = 1
        for entry in board:
            if entry["user"].id == user.id:
                rank = entry["rank"]
                break
        total = len(board)
        name = user.first_name or user.username or "Drone"

    text = format_weekly_stats_text(stats, name, rank, total)
    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


@require_registration
async def workdays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /workdays [spec]. Views or updates working days."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)

        if not context.args:
            current = services.format_workdays(user.work_days)
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"📅 *Current Workdays:* `{current}`\n\n"
                    f"To update, use:\n"
                    f"• `/workdays weekdays` (Mon-Fri)\n"
                    f"• `/workdays sundays-off` (Mon-Sat)\n"
                    f"• `/workdays mon,tue,wed,thu`"
                ),
                parse_mode="Markdown",
            )
            return

        spec = " ".join(context.args)
        try:
            formatted = services.set_user_workdays(session, user, spec)
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"✅ *Workdays updated:* `{formatted}`.\nSlack off outside these days at your own discretion.",
                parse_mode="Markdown",
            )
        except ValueError as e:
            await context.bot.send_message(chat_id=chat.id, text=f"⚠️ {e}")


@require_registration
async def workhours_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /workhours [HH:MM-HH:MM]. Views or updates working hours."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)

        if not context.args:
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"⏰ *Current Work Hours:* `{user.work_start} - {user.work_end}`\n\n"
                    f"To update: `/workhours 09:00-18:00` or `/workhours 10:00 19:00`"
                ),
                parse_mode="Markdown",
            )
            return

        raw = " ".join(context.args).replace("-", " ")
        parts = raw.split()
        if len(parts) < 2:
            await context.bot.send_message(
                chat_id=chat.id,
                text="⚠️ Usage: `/workhours 09:00-18:00` (specify start and end time).",
                parse_mode="Markdown",
            )
            return

        try:
            start_fmt, end_fmt = services.set_user_workhours(session, user, parts[0], parts[1])
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"✅ *Work hours set:* `{start_fmt} - {end_fmt}`.\nReminders will nag you during this window.",
                parse_mode="Markdown",
            )
        except ValueError as e:
            await context.bot.send_message(chat_id=chat.id, text=f"⚠️ {e}")


@require_registration
async def dayoff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /dayoff <date> [reason]. Plans a day off."""
    chat = update.effective_chat
    if not context.args:
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "🏖️ *Schedule a Day Off:*\n"
                "Usage: `/dayoff <today|tomorrow|YYYY-MM-DD> [reason]`\n"
                "Example: `/dayoff tomorrow Mental health break`\n"
                "Example: `/dayoff 2026-10-05 Vacation`"
            ),
            parse_mode="Markdown",
        )
        return

    date_raw = context.args[0]
    reason = " ".join(context.args[1:]).strip() if len(context.args) > 1 else "Unspecified holiday"

    try:
        target_date = services.parse_date_argument(date_raw)
    except ValueError as e:
        await context.bot.send_message(chat_id=chat.id, text=f"⚠️ {e}")
        return

    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        day_off, created = services.add_day_off(session, user, target_date, reason)

    action = "Scheduled" if created else "Updated"
    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            f"🌴 *{action} Day Off:*\n"
            f"• *Date:* `{target_date.strftime('%A, %b %d, %Y')}`\n"
            f"• *Reason:* `{reason}`\n\n"
            f"_Reminders will be paused on this day. Enjoy your guilt-ridden relaxation._"
        ),
        parse_mode="Markdown",
    )


@require_registration
async def cancel_dayoff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /cancel_dayoff <date>. Cancels a scheduled day off."""
    chat = update.effective_chat
    if not context.args:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Usage: `/cancel_dayoff <today|tomorrow|YYYY-MM-DD>`",
            parse_mode="Markdown",
        )
        return

    try:
        target_date = services.parse_date_argument(context.args[0])
    except ValueError as e:
        await context.bot.send_message(chat_id=chat.id, text=f"⚠️ {e}")
        return

    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        removed = services.remove_day_off(session, user, target_date)

    if removed:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"💼 Day off on `{target_date}` cancelled! Back to work, drone.",
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"❓ No planned day off found for `{target_date}`.",
            parse_mode="Markdown",
        )


@require_registration
async def list_daysoff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /days_off. Lists upcoming days off."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        days = services.get_upcoming_days_off(session, user)

    if not days:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🏖️ You have no upcoming scheduled days off. Grinding non-stop, as expected.",
            parse_mode="Markdown",
        )
        return

    lines = ["🏖️ *Upcoming Scheduled Days Off:*"]
    for d in days:
        lines.append(f"• `{d.date.strftime('%A, %b %d, %Y')}` — {d.reason or 'Day off'}")
    lines.append("\nTo cancel one, use `/cancel_dayoff <date>`.")
    await context.bot.send_message(chat_id=chat.id, text="\n".join(lines), parse_mode="Markdown")


@require_registration
async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /config weekly <day> <time>. Configures weekly stats broadcast schedule."""
    chat = update.effective_chat
    args = context.args or []
    if len(args) < 3 or args[0].lower() != "weekly":
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "⚙️ *Configure Weekly Stats:*\n"
                "Usage: `/config weekly <day> <HH:MM>`\n"
                "Example: `/config weekly Saturday 19:00`\n"
                "Example: `/config weekly Sunday 20:30`"
            ),
            parse_mode="Markdown",
        )
        return

    day_str, time_str = args[1], args[2]
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        try:
            day_name, time_fmt = services.set_weekly_config(session, user, day_str, time_str)
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"✅ *Weekly stats schedule updated!*\n"
                    f"You will receive stats every *{day_name}* at *{time_fmt}*.\n"
                    f"You can still request stats anytime via `/weekly`."
                ),
                parse_mode="Markdown",
            )
        except ValueError as e:
            await context.bot.send_message(chat_id=chat.id, text=f"⚠️ {e}")


@require_registration
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /settings. Displays full current configuration."""
    chat = update.effective_chat
    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat.id)
        workdays_str = services.format_workdays(user.work_days)
        stat_day = services.WEEKDAY_NAMES[user.weekly_stats_day]
        days_off = services.get_upcoming_days_off(session, user)

    text = (
        f"⚙️ *YOUR CONFIGURATION:*\n"
        f"• *User:* `{user.first_name or user.username or user.chat_id}`\n"
        f"• *Workdays:* `{workdays_str}`\n"
        f"• *Work Hours:* `{user.work_start} - {user.work_end}`\n"
        f"• *Weekly Report:* Every `{stat_day}` at `{user.weekly_stats_time}`\n"
        f"• *Upcoming Days Off:* `{len(days_off)} scheduled`\n\n"
        f"Use `/workdays`, `/workhours`, `/dayoff`, or `/config` to change any setting."
    )
    await context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline keyboard button presses."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    data = query.data
    chat_id = query.message.chat.id if query.message else update.effective_chat.id

    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, chat_id)
        if not user or not user.is_active:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please run `/start` to register first.",
                parse_mode="Markdown",
            )
            return

        if data == "quick_work_1":
            services.add_work_log(session, user, "work", "Quick Work Log", 1.0, date.today())
            nudge = toxic_quotes.get_work_quote(1.0, "Quick Work Log")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"💼 *Logged 1.0h of Work!*\n_{nudge}_",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        elif data == "quick_waste_1":
            services.add_work_log(session, user, "waste", "Quick Slacking", 1.0, date.today())
            nudge = toxic_quotes.get_waste_quote(1.0, "Quick Slacking")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🗑️ *Logged 1.0h of Waste!*\n_{nudge}_",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        elif data == "view_summary":
            summary = services.get_daily_summary(session, user, date.today())
            text = format_daily_summary_text(summary, user.first_name or user.username or "Drone")
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        elif data == "view_leaderboard":
            board = services.get_daily_leaderboard(session, date.today())
            text = format_leaderboard_text(board, date.today())
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        elif data == "view_weekly":
            stats = services.get_weekly_stats(session, user, date.today())
            board = services.get_weekly_leaderboard(session, date.today())
            rank = 1
            for entry in board:
                if entry["user"].id == user.id:
                    rank = entry["rank"]
                    break
            text = format_weekly_stats_text(
                stats, user.first_name or user.username or "Drone", rank, len(board)
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )

        elif data == "view_schedule":
            workdays_str = services.format_workdays(user.work_days)
            stat_day = services.WEEKDAY_NAMES[user.weekly_stats_day]
            text = (
                f"📅 *Schedule:* {workdays_str} ({user.work_start} - {user.work_end})\n"
                f"📈 *Weekly Stats:* {stat_day} at {user.weekly_stats_time}\n"
                f"Use `/workdays`, `/workhours`, or `/dayoff` to modify."
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown",
            )


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles Telegram inline query mode (@botname in any chat).

    Allows users to share their daily summary, the leaderboard, or quick log templates inline.
    """
    inline_query = update.inline_query
    if not inline_query:
        return

    query_user = inline_query.from_user
    results = []

    with get_db_session(context) as session:
        user = services.get_user_by_chat_id(session, query_user.id)
        if user and user.is_active:
            # 1. Personal Summary
            summary = services.get_daily_summary(session, user, date.today())
            name = user.first_name or user.username or "Drone"
            summary_text = format_daily_summary_text(summary, name)
            results.append(
                InlineQueryResultArticle(
                    id="my_summary",
                    title="📊 My Today's Summary",
                    description=f"{summary['work_hours']}h work, {summary['waste_hours']}h waste",
                    input_message_content=InputTextMessageContent(
                        summary_text, parse_mode="Markdown"
                    ),
                )
            )

            # 2. Leaderboard
            board = services.get_daily_leaderboard(session, date.today())
            board_text = format_leaderboard_text(board, date.today())
            results.append(
                InlineQueryResultArticle(
                    id="leaderboard",
                    title="🏆 Today's Leaderboard",
                    description=f"View community leaderboard ({len(board)} users)",
                    input_message_content=InputTextMessageContent(
                        board_text, parse_mode="Markdown"
                    ),
                )
            )

        # 3. Log Work Template
        results.append(
            InlineQueryResultArticle(
                id="log_work_template",
                title="💼 Quick Log Work",
                description="Template: /log work <task> <hours>",
                input_message_content=InputTextMessageContent(
                    "/log work  2.0",
                ),
            )
        )

        # 4. Log Waste Template
        results.append(
            InlineQueryResultArticle(
                id="log_waste_template",
                title="🗑️ Quick Log Waste",
                description="Template: /log waste <procrastination> <hours>",
                input_message_content=InputTextMessageContent(
                    "/log waste doomscrolling 1.0",
                ),
            )
        )

        # 5. Toxic Nudge
        random_quote = toxic_quotes.get_reminder_quote()
        results.append(
            InlineQueryResultArticle(
                id="toxic_nudge",
                title="😈 Send a Toxic Productivity Nudge",
                description=random_quote[:50] + "...",
                input_message_content=InputTextMessageContent(
                    f"😈 *Toxic Productivity Nudge:*\n_{random_quote}_",
                    parse_mode="Markdown",
                ),
            )
        )

    await inline_query.answer(results, cache_time=5, is_personal=True)
