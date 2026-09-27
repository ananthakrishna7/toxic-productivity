# Deployment & Architecture Guide

This document describes the technical architecture of **Toxic Productivity Bot** and instructions for hosting it in production using Docker or systemd.

---

## Architecture Overview

```
                      +-----------------------------+
                      |     Telegram Bot API        |
                      +--------------+--------------+
                                     |
               Long Polling / Webhook| (python-telegram-bot)
                                     v
                      +-----------------------------+
                      |         main.py             |
                      |  (Application & Dispatcher) |
                      +-------+--------------+------+
                              |              |
           +------------------+              +--------------------+
           |                                                      |
           v                                                      v
+---------------------+                                +---------------------+
|    handlers.py      |                                |    scheduler.py     |
| Command & Inline    |                                | 4h Reminders, EoD,  |
| Callback Handlers   |                                | Weekly Stats Jobs   |
+----------+----------+                                +----------+----------+
           |                                                      |
           +------------------+              +--------------------+
                              v              v
                      +-----------------------------+
                      |        services.py          |
                      |    (Domain & Logic Layer)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |          models.py          |
                      |    (SQLAlchemy 2.0 ORM)     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Database (SQLite/Postgres) |
                      +-----------------------------+
```

### Components
1. **`models.py`**: SQLAlchemy 2.0 Declarative ORM models (`User`, `WorkLog`, `DayOff`). Clean migration path from SQLite to PostgreSQL by adjusting `DATABASE_URL`.
2. **`services.py`**: Stateless, pure domain logic for log parsing, summary calculation, leaderboard rank ordering, and workday/holiday verification.
3. **`handlers.py`**: Telegram interaction layer handling commands, inline queries, and interactive keyboard callbacks.
4. **`scheduler.py`**: APScheduler-backed JobQueue executing 4-hour reminders, End-of-Day broadcasts, and configurable weekly stats.
5. **`toxic_quotes.py`**: Sarcastic and toxic commentary generators categorized by performance tiers.

---

## Database Configuration

The application uses SQLAlchemy, meaning it can connect to any SQL backend without code changes.

### SQLite (Default)
```bash
# In your .env file
DATABASE_URL=sqlite:///productivity.db
```

### PostgreSQL (Production)
```bash
# In your .env file
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/toxic_productivity
```

---

## Deployment with systemd (Linux Server)

Create `/etc/systemd/system/toxic-bot.service`:

```ini
[Unit]
Description=Toxic Productivity Telegram Bot
After=network.target

[Service]
Type=simple
User=ananth
WorkingDirectory=/home/ananth/repos/toxic-productivity
EnvironmentFile=/home/ananth/repos/toxic-productivity/.env
ExecStart=/home/ananth/repos/toxic-productivity/.venv/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable toxic-bot
sudo systemctl start toxic-bot
sudo systemctl status toxic-bot
```

---

## Deployment with Docker

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Docker Run
```bash
docker build -t toxic-productivity-bot .
docker run -d --name toxic-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL="sqlite:////app/data/productivity.db" \
  toxic-productivity-bot
```
