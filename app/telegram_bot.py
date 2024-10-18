import asyncio
import logging
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, Application, CommandHandler

from dotenv import load_dotenv

from model import db, Subscriber

load_dotenv()

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s', level=logging.DEBUG, handlers=[logging.StreamHandler(), logging.FileHandler(
    'app/logs/telegram.log')])

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logging.error('TELEGRAM_BOT_TOKEN environment variable not set')
    raise ValueError('TELEGRAM_BOT_TOKEN environment variable not set')

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        with db.atomic():
            subscriber, created = Subscriber.get_or_create(chat_id=chat_id)
            if created:
                await update.message.reply_text("You've subscribed to the new summarizer. Welcome!")
                logging.info(f"New subscriber added: {subscriber.chat_id}")
            else:
                await update.message.reply_text("You've already subscribed to the new summarizer.")
                logging.info(f"existing subscriber tried to : {subscriber.chat_id}")
    except Exception as e:
        logging.error(f"error adding subscriber {chat_id}: {e}")
        await update.message.reply_text("Error adding subscriber.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        with db.atomic():
            subscriber, created = Subscriber.get_or_none(chat_id=chat_id)
            if subscriber:
                subscriber.delete_instance()
                await update.message.reply_text("You've been unsubscribed to the new summarizer. Thanks for using me!")
                logging.info(f"Subscriber removed: {subscriber.chat_id}")
            else:
                await update.message.reply_text("You're not subscribed!.")
                logging.info(f"non-existing subscriber tried to : {subscriber.chat_id}")
    except Exception as e:
        logging.error(f"error removing subscriber {chat_id}: {e}")
        await update.message.reply_text("Error removing subscriber.")

async def resend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        voice_file_path = "../speech.mp3"
        if not os.path.exists(voice_file_path):
            logging.error(f"voice file {voice_file_path} does not exist")
            return

        with open(voice_file_path, "rb") as voice_file:
            try:
                await app.bot.send_voice(chat_id=chat_id, voice=voice_file,
                                                      caption="Here's your daily news summary!")
                logging.info(f"sent summary to {chat_id}")
            except Exception as e:
                logging.error(f"an error occurred {e}")

            voice_file.seek(0)
    except Exception as e:
        logging.error(f"error sending summary to {chat_id}: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Welcome to the News Summary Bot!\n\n"
        "Commands: \n"
        "/start - Subscribe to a news summaries\n"
        "/stop - Unsubscribe\n"
        "/resend - Send again latest voice\n"
        "/help - Show this message\n"
    )
    await update.message.reply_text(help_text)

def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("resend", resend))
    app.add_handler(CommandHandler("help", help_command))


async def start_bot():
    register_handlers(app)
    logging.info("Starting Telegram Bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

async def stop_bot():
    await app.updater.stop()
    await app.stop()
    await app.shutdown()