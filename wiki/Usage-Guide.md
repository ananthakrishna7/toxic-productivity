# User Usage Guide

This guide covers all features of **Toxic Productivity Bot**, from registration to daily logging, inline queries, and leaderboard competition.

---

## 1. User Registration & Work Tracking

### The Registration Gate
The bot strictly enforces registration. If an unregistered user attempts to log hours or check statistics, the bot rejects the request:
> 🚫 **Access Denied: Unregistered Slacker!**  
> You must register before logging your (lack of) productivity. Run `/start` or `/register` to submit yourself to toxic accountability.

### How to Register
- Send `/start` in a direct message with the bot. You are registered immediately with default work hours (Mon-Fri, 09:00 - 18:00).
- Or run `/register [custom-name]` to register or update your display name.

---

## 2. Logging Activities (`/log`)

The `/log` command accepts both productive **work** and unadulterated **waste**.

### Syntax
```text
/log <work|waste> <task description> <hours>
/log <work|waste> <hours> <task description>
```

### Examples
- **Productive Work:**
  ```text
  /log work refactoring database models 2.5
  /log work 3 fixed production deadlock
  /log work writing API tests 1.5h
  ```
- **Wasted Time / Procrastination:**
  ```text
  /log waste doomscrolling Twitter 1.5
  /log waste 2h watching documentary on Roman aqueducts
  /log waste argument with strangers on Reddit 1.0
  ```

### Snarky Feedback
Every log entry receives an instant, context-aware sarcastic remark:
- *Work example:* `Logged 2.5h on 'writing API tests'. Wow, look at you doing the bare minimum required to stay employed.`
- *Waste example:* `Logged 1.5h of waste on 'doomscrolling Twitter'. At least you are transparent about your failures.`

---

## 3. Inlining the Commands

The bot provides two modes of inlining:

### A. Telegram Inline Queries (`@botname`)
You can use the bot inside **any chat or group** by typing `@your_bot_name` in the input bar:
1. **My Today's Summary**: Instantly shares your personal work/waste breakdown.
2. **Today's Leaderboard**: Broadcasts the ranked community leaderboard into the chat.
3. **Quick Log Work Template**: Pastes a pre-filled `/log work` command.
4. **Quick Log Waste Template**: Pastes a pre-filled `/log waste` command.
5. **Toxic Nudge**: Sends a randomly selected insult/motivation quote into the group.

### B. Interactive Inline Buttons
Every summary and reminder includes 1-tap interactive inline buttons:
- `[ 💼 +1h Work ]`: Instantly logs 1 hour of productive work.
- `[ 🗑️ +1h Waste ]`: Instantly logs 1 hour of slacking.
- `[ 📊 Today's Summary ]`: Refreshes your today's metrics.
- `[ 🏆 Leaderboard ]`: Fetches latest leaderboard rankings.
- `[ 📈 Weekly Stats ]`: Shows your weekly progress.

---

## 4. Daily Summaries & Leaderboard

### End of Day (EoD) Summary
- Trigger on-demand at any time: `/summary` or `/today` or `/eod`.
- Output displays total productive hours, total wasted hours, net productivity (`work - waste`), itemized breakdown, and a productivity-tier roast.
- The bot also dispatches an automatic EoD recap to active users at the conclusion of their scheduled workday.

### Community Leaderboard
- Trigger via `/leaderboard`.
- Users are ranked by productive hours logged today:
  - **Rank #1**: 👑 `Corporate Overlord (Sweat-Lord Supreme)`
  - **Rank #2**: 🥈 `Eager Sycophant (Trying too hard)`
  - **Rank #3**: 🥉 `Mediocre Survivor (Barely safe)`
  - **Last Rank**: 🤡 `Chief Procrastination Officer (Absolute Slacker)`
  - **Other Drones**: ⚙️ `Cog #N (Disposable Resource)`

---

## 5. Weekly Stats & Toxic Trophies

- Trigger via `/weekly` or `/stats`.
- Summarizes the trailing 7 days with daily mini-bar charts (`🟩`), total work vs waste, net balance, and an assigned toxic weekly award (e.g. *Unhinged Grindset Champion*, *Professional Air Thief*, *Ghost Employee Award*).
- Dispatched automatically every Saturday at 19:00 by default (customizable via `/config weekly <day> <time>`).

---

## 6. Four-Hour Reminders

Every 4 hours during your configured working hours, if no activity has been logged, the bot checks in:
> ⏰ **4-HOUR PRODUCTIVITY CHECK-IN!**  
> *Four hours have elapsed. Are you writing code, or just staring into the middle distance waiting for divine inspiration?*  
> What did you work on (or waste)? Tap below or use `/log`.
