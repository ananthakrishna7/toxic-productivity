This is a telegram bot to track productivity. We use python-telegram-bot to interface with telegram, and a siple sqlite database for tracking. Your job is to complete the code in `main.py` and test the app.

A skeleton exists in `main.py`. Here are the required features:
- Flexible SQLAlchemy based ORM support - this will be useful if we transition to some other backend in the future. We can avoid hardcoding queries.
- Logging to the app(database) via the `/log` command
- Inlining the commands
- User registration(maybe integrate with /start?; refuse to work without registration) and work tracking
- Reminders every 4 hours sking the user to log their activities.
- EoD personal summary and leaderboard of all users, with a random selection of slightly insulting nudges/encouragements.
- Weekly stats sent every Saturday at 7pm by default. This should be configurable, and the user can also request for this at any time in the week.
- Workday setup - timing and days (eg. Weekends off or Sundays off or planning a day off for a week via a command)
- GitHub Wiki setup with a usage guide and BotFather setup instructions. 
- Fancy README with cool tags and the like
- GitHub Actions setup (if free for public repos)