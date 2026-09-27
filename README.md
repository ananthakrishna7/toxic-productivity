<div align="center">

# 😈 Toxic Productivity Bot

**Because gentle encouragement is overrated. Unfiltered accountability and toxic peer pressure get things done.**

[![CI](https://github.com/ananthakrishna7/toxic-productivity/actions/workflows/ci.yml/badge.svg)](https://github.com/ananthakrishna7/toxic-productivity/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v22-2CA5E0.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-d71f00.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Toxicity Score](https://img.shields.io/badge/Toxicity%20Level-Maximum-red.svg?logo=danger&logoColor=white)](#)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-command-cheatsheet">Command Cheatsheet</a> •
  <a href="#-inlining-support">Inline Support</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-wiki--guides">Wiki & Docs</a>
</p>

</div>

---

> *"Tick-tock. Another 4 hours vanished into the void. Did you actually build something or just re-arrange browser tabs?"*

**Toxic Productivity Bot** is a high-performance Telegram bot built with **python-telegram-bot** and **SQLAlchemy 2.0**. It tracks productive hours, records confessionals of wasted time, shames your slacking through automated 4-hour nudges, and ranks all users on a competitive daily leaderboard.

---

## ⚡ Key Features

- 🔒 **Registration Guard**: Refuses to engage with unregistered slackers. One command `/start` binds you to the rat race.
- 💼 **Productive & Waste Tracking**: Simple syntax `/log work <task> <hours>` or `/log waste <excuse> <hours>` with instant sarcastic replies.
- ⚡ **Inlining Everywhere**:
  - **Inline Queries**: Type `@botname` in any group or DM to instantly drop your summary, the community leaderboard, or quick log templates.
  - **Interactive Keyboards**: 1-click buttons (`[💼 +1h Work]`, `[🗑️ +1h Waste]`, `[📊 Today]`, `[🏆 Leaderboard]`).
- ⏰ **4-Hour Relentless Nudges**: Automatic background reminders during active work hours if you go dark.
- 🏆 **Daily EoD Summary & Leaderboards**: Ranks users from 👑 **Corporate Overlord** down to 🤡 **Chief Procrastination Officer**.
- 📈 **Customizable Weekly Reports**: Weekly breakdowns and toxic trophies dispatched every Saturday at 19:00 (configurable via `/config weekly <day> <time>`).
- 🏖️ **Workday & Schedule Setup**: Configure custom workdays (`weekdays`, `sundays-off`, etc.), working hours, and schedule planned days off (`/dayoff`).
- 🗄️ **Flexible SQLAlchemy ORM**: Decoupled database engine supporting SQLite by default, easily switchable to PostgreSQL or MySQL via `DATABASE_URL`.

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.11+
- A Telegram Bot Token from [@BotFather](https://t.me/botfather) (see [BotFather Setup Guide](wiki/BotFather-Setup.md))

### 2. Clone and Setup Environment

```bash
git clone https://github.com/ananthakrishna7/toxic-productivity.git
cd toxic-productivity

# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt

# Or using standard pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 3. Configure `.env`

Create a `.env` file in the repository root:

```bash
TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite:///productivity.db  # optional, default is sqlite:///productivity.db
```

### 4. Run the Bot

```bash
python main.py
```

---

## 📋 Command Cheatsheet

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `/start` | — | Register and get toxic greeting | `/start` |
| `/register` | `[name]` | Register or update display name | `/register Neo` |
| `/log` | `<type> <desc> <hours>` | Log work or waste | `/log work coding bot 2.5` |
| `/undo` | — | Immediately revert most recent entry | `/undo` |
| `/delete` | `<id>` | Delete an entry by ID | `/delete 14` (aliases: `/del`, `/remove`) |
| `/edit` | `<id> [changes]` | Modify task, hours, or type | `/edit 14 3.0` or `/edit 14 Refactored API` |
| `/logs` | — | View recent activity history with IDs | `/logs` (alias: `/entries`) |
| `/summary` | — | Personal today's summary & roast | `/summary` (aliases: `/today`, `/eod`) |
| `/leaderboard`| — | Community leaderboard for today | `/leaderboard` |
| `/weekly` | — | 7-day stats and toxic trophy | `/weekly` (alias: `/stats`) |
| `/workdays` | `[spec]` | View or update workdays | `/workdays weekdays` |
| `/workhours`| `[start-end]` | View or update working hours | `/workhours 09:00-18:00` |
| `/dayoff` | `<date> [reason]`| Plan a day off | `/dayoff tomorrow Sick` |
| `/days_off` | — | View upcoming scheduled leaves | `/days_off` |
| `/cancel_dayoff`| `<date>` | Cancel scheduled day off | `/cancel_dayoff tomorrow` |
| `/config` | `weekly <day> <time>` | Set weekly report schedule | `/config weekly Saturday 19:00` |
| `/settings` | — | Inspect current configuration | `/settings` |
| `/help` | — | Display command cheatsheet | `/help` |

---

## 💡 Inlining Support

- **Interactive Inline Buttons**:
  - `[💼 +1h Work]` & `[🗑️ +1h Waste]`: Prompts you for what you worked on, with a **Skip Description** button for 1-tap default logging.
  - `[📊 Today's Summary]`, `[🏆 Leaderboard]`, `[📈 Weekly Stats]`, `[📅 My Schedule]`.
- **Inline Queries**: Type `@your_bot_name` in any chat window to access instant inline options:

```text
@toxic_productivity_bot
  ├── 📊 My Today's Summary   (Share your work vs waste into the group)
  ├── 🏆 Today's Leaderboard  (Broadcast group standings)
  ├── 💼 Quick Log Work       (Auto-fills /log work <task> <hours>)
  ├── 🗑️ Quick Log Waste      (Auto-fills /log waste <procrastination> <hours>)
  └── 😈 Send a Toxic Nudge   (Drop a random motivational insult)
```

---

## 🧪 Testing & Verification

All domain logic, models, handlers, and background schedulers are thoroughly covered by hermetic tests.

```bash
# Run tests with pytest
pytest -v

# Run linting with Ruff
ruff check .
```

---

## 🏗️ Architecture

```
                  ┌────────────────────────┐
                  │    Telegram Bot API    │
                  └───────────┬────────────┘
                              │
             Long Polling / Webhook (python-telegram-bot)
                              │
                  ┌───────────▼────────────┐
                  │        main.py         │
                  └─────┬────────────┬─────┘
                        │            │
         ┌──────────────┘            └──────────────┐
         ▼                                          ▼
┌──────────────────┐                      ┌──────────────────┐
│   handlers.py    │                      │   scheduler.py   │
│ Commands & Inline│                      │ 4h Nudges & EoD  │
└────────┬─────────┘                      └────────┬─────────┘
         │                                         │
         └──────────────┐            ┌─────────────┘
                        ▼            ▼
                  ┌────────────────────────┐
                  │      services.py       │
                  │  (Pure Domain Logic)   │
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │       models.py        │
                  │  (SQLAlchemy 2.0 ORM)  │
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │  SQLite / PostgreSQL   │
                  └────────────────────────┘
```

---

## 📖 Wiki & Guides

- [BotFather Setup Guide](wiki/BotFather-Setup.md): Token generation and inline query enablement.
- [User Usage Guide](wiki/Usage-Guide.md): Detailed workflows for users and teams.
- [Workdays and Scheduling](wiki/Workdays-and-Scheduling.md): Setting up work windows and vacation days.
- [Deployment & Architecture](wiki/Deployment-and-Architecture.md): Systemd service and Docker instructions.

---

## ⚖️ License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.