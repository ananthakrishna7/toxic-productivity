"""Business logic and service layer for Toxic Productivity Bot.

Handles user management, work log parsing, metrics aggregation,
leaderboard calculations, and workday scheduling.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import DayOff, User, WorkLog, utc_now

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_FULL = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def get_or_create_user(
    session: Session,
    chat_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> Tuple[User, bool]:
    """Retrieves an existing user by chat_id or registers a new user.

    Returns:
        tuple of (User, created_flag)
    """
    stmt = select(User).where(User.chat_id == chat_id)
    user = session.execute(stmt).scalar_one_or_none()
    created = False
    if not user:
        user = User(
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            registered_at=utc_now(),
            work_days="0,1,2,3,4",
            work_start="09:00",
            work_end="18:00",
            weekly_stats_day=5,  # Saturday
            weekly_stats_time="19:00",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        created = True
    else:
        # Update username/first_name if changed
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if updated:
            session.commit()
            session.refresh(user)
    return user, created


def get_user_by_chat_id(session: Session, chat_id: int) -> Optional[User]:
    """Retrieves a user by chat_id or returns None."""
    stmt = select(User).where(User.chat_id == chat_id)
    return session.execute(stmt).scalar_one_or_none()


def parse_log_input(text: str) -> Tuple[str, str, float]:
    """Parses user input for /log command.

    Supported patterns:
      /log work coding telegram bot 2.5
      /log waste doomscrolling twitter 1.5
      /log work 3 fixed database bugs
      /log waste 1h procrastinating

    Returns:
        tuple of (log_type, description, hours)
    Raises:
        ValueError if command input is invalid or missing required parameters.
    """
    cleaned = text.strip()
    # Strip leading command if passed
    if cleaned.startswith("/log"):
        cleaned = cleaned[4:].strip()

    if not cleaned:
        raise ValueError("Missing parameters. Usage: `/log <work|waste> <description> <hours>`")

    tokens = cleaned.split()
    if len(tokens) < 2:
        raise ValueError("Too few parameters. Usage: `/log <work|waste> <description> <hours>`")

    # Determine log type
    first_token = tokens[0].lower()
    if first_token in ("work", "w", "job", "study", "productive"):
        log_type = "work"
    elif first_token in ("waste", "slacking", "slack", "distraction", "procrastination"):
        log_type = "waste"
    else:
        raise ValueError(
            f"Invalid activity type '{tokens[0]}'. Allowed types are `work` or `waste`."
        )

    rem_tokens = tokens[1:]

    # Check if hours is the first token after type or the last token
    hours: Optional[float] = None
    desc_tokens: List[str] = []

    def try_parse_hours(token: str) -> Optional[float]:
        t = token.lower().rstrip("h").rstrip("hrs").rstrip("hr")
        try:
            val = float(t)
            return val if val > 0 else None
        except ValueError:
            return None

    # Check last token first (standard: /log work description 2.5)
    hours_from_last = try_parse_hours(rem_tokens[-1])
    if hours_from_last is not None and len(rem_tokens) > 1:
        hours = hours_from_last
        desc_tokens = rem_tokens[:-1]
    else:
        # Check first token (alternate: /log work 2.5 description)
        hours_from_first = try_parse_hours(rem_tokens[0])
        if hours_from_first is not None and len(rem_tokens) > 1:
            hours = hours_from_first
            desc_tokens = rem_tokens[1:]
        elif hours_from_last is not None and len(rem_tokens) == 1:
            hours = hours_from_last
            desc_tokens = [f"Unspecified {log_type}"]

    if hours is None:
        raise ValueError(
            "Could not parse hours. Please provide a positive number of hours (e.g. `2`, `1.5`, or `3h`).\n"
            "Example: `/log work backend API 2.5`"
        )

    description = " ".join(desc_tokens).strip()
    if not description:
        description = f"Unspecified {log_type}"

    return log_type, description, round(hours, 2)


def add_work_log(
    session: Session,
    user: User,
    log_type: str,
    description: str,
    hours: float,
    log_date: Optional[date] = None,
) -> WorkLog:
    """Creates and commits a new WorkLog entry."""
    entry_date = log_date or date.today()
    log = WorkLog(
        user_id=user.id,
        log_type=log_type,
        description=description,
        hours=hours,
        date=entry_date,
        created_at=utc_now(),
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_daily_summary(
    session: Session,
    user: User,
    target_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Calculates daily work summary for a user on target_date."""
    check_date = target_date or date.today()
    stmt = (
        select(WorkLog)
        .where(WorkLog.user_id == user.id, WorkLog.date == check_date)
        .order_by(WorkLog.created_at.asc())
    )
    logs = list(session.execute(stmt).scalars().all())

    work_hours = sum(entry.hours for entry in logs if entry.log_type == "work")
    waste_hours = sum(entry.hours for entry in logs if entry.log_type == "waste")
    total_hours = work_hours + waste_hours
    net_hours = work_hours - waste_hours

    return {
        "date": check_date,
        "work_hours": round(work_hours, 2),
        "waste_hours": round(waste_hours, 2),
        "total_hours": round(total_hours, 2),
        "net_hours": round(net_hours, 2),
        "logs": logs,
    }


def get_daily_leaderboard(
    session: Session,
    target_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Calculates ranked daily leaderboard for all active users on target_date."""
    check_date = target_date or date.today()
    users_stmt = select(User).where(User.is_active == True)  # noqa: E712
    users = list(session.execute(users_stmt).scalars().all())

    user_stats = []
    for u in users:
        stmt = select(
            WorkLog.log_type, func.sum(WorkLog.hours).label("total_hours")
        ).where(WorkLog.user_id == u.id, WorkLog.date == check_date).group_by(WorkLog.log_type)
        results = session.execute(stmt).all()

        work_h = 0.0
        waste_h = 0.0
        for log_type, total_h in results:
            if log_type == "work":
                work_h = float(total_h or 0.0)
            elif log_type == "waste":
                waste_h = float(total_h or 0.0)

        user_stats.append({
            "user": u,
            "work_hours": round(work_h, 2),
            "waste_hours": round(waste_h, 2),
            "net_hours": round(work_h - waste_h, 2),
            "name": u.first_name or u.username or f"User-{u.id}",
        })

    # Sort users: descending work_hours, ascending waste_hours
    user_stats.sort(key=lambda s: (-s["work_hours"], s["waste_hours"]))

    # Assign ranks
    for idx, stat in enumerate(user_stats, 1):
        stat["rank"] = idx

    return user_stats


def get_weekly_stats(
    session: Session,
    user: User,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Calculates weekly work statistics for a user over the past 7 days."""
    target_end = end_date or date.today()
    start_date = target_end - timedelta(days=6)

    stmt = (
        select(WorkLog)
        .where(
            WorkLog.user_id == user.id,
            WorkLog.date >= start_date,
            WorkLog.date <= target_end,
        )
        .order_by(WorkLog.date.asc())
    )
    logs = list(session.execute(stmt).scalars().all())

    work_hours = sum(entry.hours for entry in logs if entry.log_type == "work")
    waste_hours = sum(entry.hours for entry in logs if entry.log_type == "waste")

    # Daily breakdown
    daily_breakdown: Dict[date, Dict[str, float]] = {}
    curr = start_date
    while curr <= target_end:
        daily_breakdown[curr] = {"work": 0.0, "waste": 0.0}
        curr += timedelta(days=1)

    for entry in logs:
        if entry.date in daily_breakdown:
            daily_breakdown[entry.date][entry.log_type] += entry.hours

    return {
        "start_date": start_date,
        "end_date": target_end,
        "work_hours": round(work_hours, 2),
        "waste_hours": round(waste_hours, 2),
        "net_hours": round(work_hours - waste_hours, 2),
        "daily_breakdown": daily_breakdown,
        "logs_count": len(logs),
    }


def get_weekly_leaderboard(
    session: Session,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Calculates weekly leaderboard rankings across all users over 7 days."""
    target_end = end_date or date.today()
    start_date = target_end - timedelta(days=6)

    users_stmt = select(User).where(User.is_active == True)  # noqa: E712
    users = list(session.execute(users_stmt).scalars().all())

    leaderboard = []
    for u in users:
        stmt = select(
            WorkLog.log_type, func.sum(WorkLog.hours).label("total_hours")
        ).where(
            WorkLog.user_id == u.id,
            WorkLog.date >= start_date,
            WorkLog.date <= target_end,
        ).group_by(WorkLog.log_type)
        results = session.execute(stmt).all()

        work_h = 0.0
        waste_h = 0.0
        for log_type, total_h in results:
            if log_type == "work":
                work_h = float(total_h or 0.0)
            elif log_type == "waste":
                waste_h = float(total_h or 0.0)

        leaderboard.append({
            "user": u,
            "work_hours": round(work_h, 2),
            "waste_hours": round(waste_h, 2),
            "net_hours": round(work_h - waste_h, 2),
            "name": u.first_name or u.username or f"User-{u.id}",
        })

    leaderboard.sort(key=lambda s: (-s["work_hours"], s["waste_hours"]))
    for idx, stat in enumerate(leaderboard, 1):
        stat["rank"] = idx

    return leaderboard


def parse_workdays_spec(spec: str) -> List[int]:
    """Parses a workdays specification string into a sorted list of weekday ints.

    Accepted formats:
      - 'weekdays', 'workdays', 'weekends-off' -> [0, 1, 2, 3, 4]
      - 'sundays-off' -> [0, 1, 2, 3, 4, 5]
      - 'all', 'everyday' -> [0, 1, 2, 3, 4, 5, 6]
      - 'mon,tue,wed,thu,fri'
      - '0,1,2,3,4'
    """
    clean = spec.strip().lower()
    if clean in ("weekdays", "workdays", "weekends-off", "weekend-off"):
        return [0, 1, 2, 3, 4]
    if clean in ("sundays-off", "sunday-off"):
        return [0, 1, 2, 3, 4, 5]
    if clean in ("all", "everyday", "7days"):
        return [0, 1, 2, 3, 4, 5, 6]

    items = re.split(r"[\s,]+", clean)
    days_set = set()
    for item in items:
        if not item:
            continue
        if item.isdigit():
            d = int(item)
            if 0 <= d <= 6:
                days_set.add(d)
        else:
            for idx, full in enumerate(WEEKDAY_FULL):
                if full.startswith(item):
                    days_set.add(idx)
                    break

    if not days_set:
        raise ValueError(
            "Could not parse work days. Provide e.g. `weekdays`, `weekends-off`, or `mon,tue,wed,thu,fri`."
        )
    return sorted(list(days_set))


def format_workdays(days_csv: str) -> str:
    """Formats comma-separated weekday integers into friendly text."""
    try:
        day_ints = [int(x) for x in days_csv.split(",") if x.strip()]
        names = [WEEKDAY_NAMES[d] for d in day_ints if 0 <= d <= 6]
        return ", ".join(names) if names else "None"
    except Exception:
        return days_csv


def set_user_workdays(session: Session, user: User, spec: str) -> str:
    """Updates user workdays configuration."""
    days = parse_workdays_spec(spec)
    csv_str = ",".join(str(d) for d in days)
    user.work_days = csv_str
    session.commit()
    session.refresh(user)
    return format_workdays(csv_str)


def parse_time_string(time_str: str) -> str:
    """Validates and normalizes HH:MM time string."""
    clean = time_str.strip()
    match = re.match(r"^(\d{1,2}):(\d{2})$", clean)
    if not match:
        raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM (e.g. 09:00, 18:30).")
    h, m = int(match.group(1)), int(match.group(2))
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Invalid time values in '{time_str}'. Hours must be 0-23, minutes 0-59.")
    return f"{h:02d}:{m:02d}"


def set_user_workhours(
    session: Session, user: User, start_time_str: str, end_time_str: str
) -> Tuple[str, str]:
    """Updates user workday hours."""
    start_fmt = parse_time_string(start_time_str)
    end_fmt = parse_time_string(end_time_str)
    user.work_start = start_fmt
    user.work_end = end_fmt
    session.commit()
    session.refresh(user)
    return start_fmt, end_fmt


def set_weekly_config(
    session: Session, user: User, day_str: str, time_str: str
) -> Tuple[str, str]:
    """Updates weekly stats scheduled day and time."""
    clean_day = day_str.strip().lower()
    day_idx: Optional[int] = None
    for idx, full in enumerate(WEEKDAY_FULL):
        if full.startswith(clean_day):
            day_idx = idx
            break
    if day_idx is None:
        if clean_day.isdigit() and 0 <= int(clean_day) <= 6:
            day_idx = int(clean_day)
        else:
            raise ValueError(
                f"Invalid day '{day_str}'. Please provide a day like 'Saturday' or 'Mon-Sun'."
            )

    time_fmt = parse_time_string(time_str)
    user.weekly_stats_day = day_idx
    user.weekly_stats_time = time_fmt
    session.commit()
    session.refresh(user)
    return WEEKDAY_NAMES[day_idx], time_fmt


def parse_date_argument(date_str: str) -> date:
    """Parses date string supporting 'today', 'tomorrow', or 'YYYY-MM-DD'."""
    clean = date_str.strip().lower()
    today = date.today()
    if clean in ("today", "tod"):
        return today
    if clean in ("tomorrow", "tom"):
        return today + timedelta(days=1)
    try:
        return datetime.strptime(clean, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"Invalid date '{date_str}'. Use 'today', 'tomorrow', or 'YYYY-MM-DD' format."
        )


def add_day_off(
    session: Session, user: User, target_date: date, reason: Optional[str] = None
) -> Tuple[DayOff, bool]:
    """Adds a scheduled day off for the user."""
    stmt = select(DayOff).where(DayOff.user_id == user.id, DayOff.date == target_date)
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        if reason and existing.reason != reason:
            existing.reason = reason
            session.commit()
            session.refresh(existing)
        return existing, False

    day_off = DayOff(user_id=user.id, date=target_date, reason=reason)
    session.add(day_off)
    session.commit()
    session.refresh(day_off)
    return day_off, True


def remove_day_off(session: Session, user: User, target_date: date) -> bool:
    """Removes a planned day off for the user."""
    stmt = select(DayOff).where(DayOff.user_id == user.id, DayOff.date == target_date)
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        session.delete(existing)
        session.commit()
        return True
    return False


def get_upcoming_days_off(
    session: Session, user: User, from_date: Optional[date] = None
) -> List[DayOff]:
    """Retrieves upcoming scheduled days off for user."""
    start = from_date or date.today()
    stmt = (
        select(DayOff)
        .where(DayOff.user_id == user.id, DayOff.date >= start)
        .order_by(DayOff.date.asc())
    )
    return list(session.execute(stmt).scalars().all())


def is_workday(session: Session, user: User, check_date: Optional[date] = None) -> bool:
    """Determines if a given date is an active working day for the user.

    Checks configured work_days and ensures the user doesn't have a DayOff scheduled.
    """
    target = check_date or date.today()
    weekday = target.weekday()
    try:
        user_days = [int(x) for x in user.work_days.split(",") if x.strip()]
    except Exception:
        user_days = [0, 1, 2, 3, 4]

    if weekday not in user_days:
        return False

    # Check for planned day off
    stmt = select(DayOff).where(DayOff.user_id == user.id, DayOff.date == target)
    day_off = session.execute(stmt).scalar_one_or_none()
    return day_off is None


def is_within_work_hours(user: User, current_time: Optional[time] = None) -> bool:
    """Checks if current time is within user's configured working hours."""
    now_t = current_time or datetime.now().time()
    try:
        start_h, start_m = map(int, user.work_start.split(":"))
        end_h, end_m = map(int, user.work_end.split(":"))
        start_t = time(start_h, start_m)
        end_t = time(end_h, end_m)
        if start_t <= end_t:
            return start_t <= now_t <= end_t
        else:
            # Over-midnight shift
            return now_t >= start_t or now_t <= end_t
    except Exception:
        return True
