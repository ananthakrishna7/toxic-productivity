# Workdays & Schedule Configuration Guide

Toxic Productivity Bot allows users to configure individual working hours, workdays, planned vacations, and weekly report schedules so reminders and reports match your actual routine.

---

## 1. Configuring Working Days (`/workdays`)

By default, every user is configured for standard weekdays (`Mon, Tue, Wed, Thu, Fri`).

### View Current Schedule
Run without arguments:
```text
/workdays
```

### Update Working Days
You can use natural presets or custom day lists:
- **Standard Weekdays:**
  ```text
  /workdays weekdays
  /workdays weekends-off
  ```
- **6-Day Workweek (Sundays Off):**
  ```text
  /workdays sundays-off
  ```
- **No Days Off (7-Day Grind):**
  ```text
  /workdays all
  ```
- **Custom Days:**
  ```text
  /workdays mon,wed,fri
  /workdays tue,thu,sat
  ```

---

## 2. Configuring Working Hours (`/workhours`)

Working hours define the daily active window during which 4-hour reminders can be dispatched.

### View Working Hours
```text
/workhours
```

### Update Working Hours
Provide start and end time in 24-hour `HH:MM` format:
```text
/workhours 09:00-18:00
/workhours 10:00 19:30
/workhours 08:30-17:00
```

---

## 3. Planning Days Off (`/dayoff`)

When you plan a day off, the bot suspends all 4-hour reminder nudges for that date.

### Scheduling a Day Off
Provide relative keywords (`today`, `tomorrow`) or ISO dates (`YYYY-MM-DD`):
```text
/dayoff tomorrow Mental health day
/dayoff today Dentist appointment
/dayoff 2026-10-15 Vacation
```

### Listing Upcoming Days Off
View all scheduled future leaves:
```text
/days_off
```

### Cancelling a Planned Day Off
If your vacation was cancelled or guilt compelled you to work:
```text
/cancel_dayoff tomorrow
/cancel_dayoff 2026-10-15
```

---

## 4. Weekly Report Schedule (`/config weekly`)

By default, weekly recaps are delivered every **Saturday at 19:00 (7:00 PM)**.

### Customizing the Delivery Day and Time
```text
/config weekly Saturday 19:00
/config weekly Sunday 20:00
/config weekly Friday 17:30
```

---

## 5. Reviewing Settings (`/settings`)

To view your complete profile and schedule at a glance:
```text
/settings
```

Output:
```text
⚙️ YOUR CONFIGURATION:
• User: Alice
• Workdays: Mon, Tue, Wed, Thu, Fri
• Work Hours: 09:00 - 18:00
• Weekly Report: Every Sat at 19:00
• Upcoming Days Off: 1 scheduled
```
