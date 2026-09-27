"""Toxic, sarcastic, and hilarious productivity nudges and quotes.

Because genuine motivation is overrated; toxic comparison gets things done.
"""

import random

# Quotes for 4-hour reminders
REMINDER_QUOTES = [
    "Tick-tock. Another 4 hours vanished into the void. Did you actually build something or just re-arrange browser tabs?",
    "4-hour check-in: While you were scrolling memes, someone half your age just shipped a SaaS company. Log your hours.",
    "Four hours have elapsed. Are you writing code, or just staring into the middle distance waiting for divine inspiration?",
    "Friendly reminder: Slacking off is fun until the deadline hits. Log your work before I mark it as 100% procrastination.",
    "Four hours gone. The shareholders are disappointed, your potential is weeping, but hey—at least you're breathing. What did you do?",
    "Ding dong. It's your 4-hour reality check. Did you accomplish anything of substance or just draft replies you'll never send?",
    "4 hours passed. Just checking if you're still employed or if you've quietly transitioned to professional slacker.",
]

# Quotes when logging productive work
WORK_LOG_QUOTES = [
    "Logged {hours}h on '{desc}'. Wow, look at you doing the bare minimum required to stay employed.",
    "Logged {hours}h on '{desc}'. Don't sprain your wrist patting yourself on the back.",
    "Logged {hours}h on '{desc}'. Mark this date on your calendar: you actually did something.",
    "Logged {hours}h on '{desc}'. Let's hope the code quality exceeds your motivation level.",
    "Logged {hours}h on '{desc}'. Your manager might shed a tear of mild, cautious satisfaction.",
    "Logged {hours}h on '{desc}'. That counts as work? Sure, whatever helps you sleep at night.",
    "Logged {hours}h on '{desc}'. Look at this hustle! Too bad hustle doesn't buy back squandered youth.",
]

# Quotes when logging wasted time
WASTE_LOG_QUOTES = [
    "Logged {hours}h of waste on '{desc}'. At least you are transparent about your failures.",
    "Logged {hours}h of '{desc}'. Outstanding commitment to squandering your prime years.",
    "Logged {hours}h of '{desc}'. A true masterclass in procrastination. Bravo.",
    "Logged {hours}h of '{desc}'. Netflix, Reddit, and your attention span thank you.",
    "Logged {hours}h of '{desc}'. If wasting time were an Olympic sport, you'd definitely take gold.",
    "Logged {hours}h of '{desc}'. Don't worry, your unfinished tasks will patiently wait to haunt your dreams.",
]

# Quotes for EoD personal summary
EOD_HIGH_PRODUCTIVITY = [
    "Look at this sweat-lord. Logged {work:.1f}h of work! Do you even remember what fresh air smells like?",
    "High productivity detected ({work:.1f}h work). Don't forget to casually brag about it in the group chat.",
    "{work:.1f}h of work today! Excellent, the capitalism machine feeds on your soul and is moderately pleased.",
]

EOD_MEDIUM_PRODUCTIVITY = [
    "Logged {work:.1f}h work and {waste:.1f}h waste. Aggressively mediocre. You survived another day on the hamster wheel.",
    "A solid C+ day: {work:.1f}h work, {waste:.1f}h waste. Perfectly blending into the background of society.",
    "{work:.1f}h work. Not bad enough to get fired, not good enough to get promoted. The sweet spot.",
]

EOD_LOW_PRODUCTIVITY = [
    "Only {work:.1f}h of work logged today, along with {waste:.1f}h of pure waste. Were you in a coma or just actively avoiding responsibility?",
    "{work:.1f}h of work? Even a screensaver moved more pixels than you today.",
    "A tragic {work:.1f}h of productive output. Tomorrow is another chance to disappoint yourself all over again.",
]

# Leaderboard titles and insults by tier
def get_leaderboard_title(rank: int, total: int) -> str:
    if rank == 1:
        return "👑 Corporate Overlord (Sweat-Lord Supreme)"
    elif rank == 2:
        return "🥈 Eager Sycophant (Trying too hard)"
    elif rank == 3:
        return "🥉 Mediocre Survivor (Barely safe)"
    elif rank == total and total > 3:
        return "🤡 Chief Procrastination Officer (Absolute Slacker)"
    else:
        return f"⚙️ Cog #{rank} (Disposable Resource)"

def get_reminder_quote() -> str:
    """Returns a random 4-hour reminder nudge."""
    return random.choice(REMINDER_QUOTES)

def get_work_quote(hours: float, desc: str) -> str:
    """Returns a toxic encouragement for logged work."""
    return random.choice(WORK_LOG_QUOTES).format(hours=hours, desc=desc)

def get_waste_quote(hours: float, desc: str) -> str:
    """Returns a sarcastic roast for wasted time."""
    return random.choice(WASTE_LOG_QUOTES).format(hours=hours, desc=desc)

def get_eod_quote(work_hours: float, waste_hours: float) -> str:
    """Returns an EoD quote based on productivity ratio."""
    if work_hours >= 6.0 and waste_hours <= 1.5:
        return random.choice(EOD_HIGH_PRODUCTIVITY).format(work=work_hours, waste=waste_hours)
    elif work_hours < 3.0:
        return random.choice(EOD_LOW_PRODUCTIVITY).format(work=work_hours, waste=waste_hours)
    else:
        return random.choice(EOD_MEDIUM_PRODUCTIVITY).format(work=work_hours, waste=waste_hours)

def get_weekly_award(rank: int, work_hours: float, waste_hours: float) -> str:
    """Assigns a toxic weekly trophy based on stats."""
    if rank == 1 and work_hours >= 35.0:
        return "🏆 Unhinged Grindset Champion (Seek help & touch grass)"
    elif rank == 1:
        return "🥇 King of the Hill (The bar was exceptionally low)"
    elif waste_hours > work_hours:
        return "💩 Professional Air Thief (Paid to waste oxygen)"
    elif work_hours < 10.0:
        return "🦥 Ghost Employee Award (Are you even on payroll?)"
    else:
        return "💼 Standard Corporate Drone (You exist, barely)"
