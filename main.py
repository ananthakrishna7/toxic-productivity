"""Main entry point for Toxic Productivity Telegram Bot.

Initializes SQLAlchemy database, registers commands and inline handlers,
configures background jobs, and starts the Telegram polling loop.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
)

import handlers
import models
import scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.environ.get("TOKEN")


async def post_init(application: Application):
    """Sets bot commands in Telegram menu on bot startup."""
    commands = [
        BotCommand("log", "Log activity: /log work coding 2.5"),
        BotCommand("summary", "View today's summary & toxic roast"),
        BotCommand("leaderboard", "View today's community leaderboard"),
        BotCommand("weekly", "View 7-day stats & toxic trophy"),
        BotCommand("workdays", "View or set working days"),
        BotCommand("workhours", "View or set working hours"),
        BotCommand("dayoff", "Schedule a planned day off"),
        BotCommand("days_off", "List upcoming planned days off"),
        BotCommand("cancel_dayoff", "Cancel a planned day off"),
        BotCommand("config", "Configure weekly stats schedule"),
        BotCommand("settings", "View current settings"),
        BotCommand("help", "Show cheatsheet and commands"),
        BotCommand("register", "Register or update profile"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Successfully registered %d bot commands with Telegram.", len(commands))
    except Exception as e:
        logger.warning("Could not set bot commands menu: %s", e)


def build_application(token: str, session_factory=None) -> Application:
    """Creates and configures the Telegram Application instance."""
    app_builder = ApplicationBuilder().token(token).post_init(post_init)
    application = app_builder.build()

    # Pass database session factory in bot_data
    if session_factory is not None:
        application.bot_data["session_factory"] = session_factory

    # Register Command Handlers
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("register", handlers.register))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("log", handlers.log_command))
    application.add_handler(CommandHandler(["summary", "today", "eod"], handlers.summary_command))
    application.add_handler(CommandHandler("leaderboard", handlers.leaderboard_command))
    application.add_handler(CommandHandler(["weekly", "stats"], handlers.weekly_command))
    application.add_handler(CommandHandler("workdays", handlers.workdays_command))
    application.add_handler(CommandHandler("workhours", handlers.workhours_command))
    application.add_handler(CommandHandler("dayoff", handlers.dayoff_command))
    application.add_handler(CommandHandler("cancel_dayoff", handlers.cancel_dayoff_command))
    application.add_handler(CommandHandler(["days_off", "list_days_off"], handlers.list_daysoff_command))
    application.add_handler(CommandHandler("config", handlers.config_command))
    application.add_handler(CommandHandler("settings", handlers.settings_command))

    # Register Callback Query Handler for Inline Buttons
    application.add_handler(CallbackQueryHandler(handlers.button_callback_handler))

    # Register Inline Query Handler for @bot queries
    application.add_handler(InlineQueryHandler(handlers.inline_query_handler))

    # Configure background reminder and summary jobs
    scheduler.setup_scheduler(application)

    return application


def main():
    """Main execution entry point."""
    if not TOKEN:
        logger.error(
            "ERROR: TOKEN environment variable is missing. "
            "Please create a .env file containing TOKEN=your_telegram_bot_token"
        )
        sys.exit(1)

    # Initialize SQLAlchemy database engine and tables
    engine, session_factory = models.init_db()
    logger.info("Initialized database with SQLAlchemy ORM.")

    application = build_application(TOKEN, session_factory=session_factory)
    logger.info("Starting Toxic Productivity Bot polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
