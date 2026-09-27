# BotFather Setup Guide

This guide walks you through setting up your Telegram bot using [@BotFather](https://t.me/botfather), enabling inline query mode, and configuring the command menu.

---

## Step 1: Create Your Bot

1. Open Telegram and search for `@BotFather` (verified account with blue checkmark).
2. Start the chat by sending `/start`.
3. Send the command:
   ```text
   /newbot
   ```
4. **Choose a Name**: Enter a display name for your bot (e.g., `Toxic Productivity Bot`).
5. **Choose a Username**: Enter a unique username ending in `bot` (e.g., `toxic_productivity_bot` or `my_toxic_tracker_bot`).
6. **Copy the Token**: BotFather will reply with your API authorization token formatted like:
   ```text
   123456789:ABCdefGHIjklmNOPqrsTUVwxyz
   ```
7. Store this token in your `.env` file:
   ```bash
   TOKEN=123456789:ABCdefGHIjklmNOPqrsTUVwxyz
   ```

---

## Step 2: Enable Inline Mode (Crucial)

Toxic Productivity Bot supports Telegram **Inline Queries** (typing `@your_bot_name` in any chat to instantly share your daily summary, leaderboard, or quick log templates).

To enable this:
1. In `@BotFather`, send:
   ```text
   /setinline
   ```
2. Select your newly created bot from the list.
3. When prompted for placeholder text, enter:
   ```text
   Search stats, leaderboard, or log templates...
   ```
4. BotFather will confirm: `Success! Inline mode has been enabled.`

---

## Step 3: Configure Bot Commands Menu

To give users an autocomplete `/` menu with full command descriptions in Telegram:

1. In `@BotFather`, send:
   ```text
   /setcommands
   ```
2. Select your bot.
3. Paste the following command list:
   ```text
   log - Record work or waste: /log work coding 2h
   undo - Revert most recently logged activity
   delete - Delete an entry by ID: /delete 12
   edit - Edit an entry: /edit 12 [changes]
   logs - View recent activity history with IDs
   summary - View today's summary & toxic roast
   leaderboard - View today's community leaderboard
   weekly - View 7-day stats & toxic trophy
   workdays - View or configure working days
   workhours - View or configure working hours
   dayoff - Schedule a planned day off
   days_off - List upcoming scheduled days off
   cancel_dayoff - Cancel a scheduled day off
   config - Configure weekly stats schedule
   settings - View current settings
   help - Show cheatsheet and usage guide
   register - Register or update profile
   ```
4. BotFather will confirm: `Success! Commands list has been updated.`

*(Note: The bot also automatically registers these commands via the Telegram Bot API `set_my_commands` on startup).*

---

## Step 4: Polish Bot Profile (Optional)

1. **Set Bot Description** (shown in empty chats before pressing Start):
   - Command: `/setdescription`
   - Text: `Track your productivity through toxic comparison, relentless 4-hour nudges, and public shaming on the daily leaderboard.`
2. **Set About Text** (shown in bot info card):
   - Command: `/setabouttext`
   - Text: `Toxic Productivity Bot: Because genuine motivation is overrated; peer pressure gets things done.`
3. **Set Bot Profile Picture**:
   - Command: `/setuserpic`
   - Upload an intimidating or sarcastic avatar image.
