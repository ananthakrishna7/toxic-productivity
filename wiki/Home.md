# Toxic Productivity Bot — GitHub Wiki

Welcome to the official documentation for **Toxic Productivity Bot**, the Telegram bot that replaces gentle encouragement with unfiltered accountability, sarcastic nudges, and toxic social comparison.

---

## 📚 Wiki Contents

1. **[[BotFather Setup Guide|BotFather-Setup]]**  
   Step-by-step instructions on obtaining your Telegram Bot token, enabling inline queries, and configuring command menus.

2. **[[User Usage Guide|Usage-Guide]]**  
   Complete guide to registering, logging productive work and wasted time, reading daily summaries, and competing on the leaderboard.

3. **[[Workday & Schedule Configuration|Workdays-and-Scheduling]]**  
   How to configure working hours, set customized workdays (e.g., weekends off, Sundays off), and schedule planned days off.

4. **[[Deployment & Architecture|Deployment-and-Architecture]]**  
   Architecture breakdown (SQLAlchemy ORM, Python-Telegram-Bot, APScheduler), Docker deployment, systemd service configuration, and environment setup.

---

## ⚡ Quick Cheat Sheet

| Command | Description |
| :--- | :--- |
| `/start` | Register yourself into the rat race |
| `/log work <task> <hours>` | Record productive work hours |
| `/log waste <task> <hours>` | Confess your procrastination hours |
| `/undo` | Immediately revert most recent entry |
| `/delete <id>` | Delete a specific entry by ID |
| `/edit <id> [changes]` | Modify an entry's task, hours, or type |
| `/logs` | View recent entries with ID tags |
| `/summary` (or `/today`) | View today's personal summary and toxic roast |
| `/leaderboard` | Inspect the daily community leaderboard |
| `/weekly` (or `/stats`) | View 7-day performance breakdown and toxic award |
| `/workdays <weekdays\|mon,tue...>` | Configure active working days |
| `/workhours <09:00-18:00>` | Configure daily working hours |
| `/dayoff <date> [reason]` | Plan a day off (suspends reminders) |
| `/config weekly <day> <time>` | Configure scheduled weekly stats dispatch |
| `/settings` | Inspect your current preferences |
| `@botname` | Inline query in any chat to share stats |
