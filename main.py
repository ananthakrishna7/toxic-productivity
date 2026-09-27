from dotenv import load_dotenv
from os import environ
from pathlib import Path
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
import logging
import sqlite3
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
load_dotenv()
TOKEN=environ.get("TOKEN")

def init_database():
    if Path("productivity.db").exists:
        logging.info("Sqlite database file already exists. Not creating tables.")
        return
    con = sqlite3.connect("productivity.db")
    cur = con.cursor()
    cur.executemany("CREATE TABLE users(id int primary key autoincrement, chat_id int, name varchar(30));" \
    "CREATE TABLE work(userid int references users.id, description text, type enum(work, waste), date TEXT, hours);")
    logging.info(f"Initialized Sqlite database")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Get more productive with toxic comparison. To start, register yourself using `/register <your-username>`. Use `/help` to view other commands. Cheers!")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="HELP:\n/log type title/description hours")
    
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler("start", start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(start_handler)
    application.add_handler(echo_handler)

    application.run_polling()