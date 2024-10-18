import asyncio
import logging
import os
import signal
import threading
from asyncio import sleep
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import telegram_bot

from parser import get_today_articles
from model import db, Article, Subscriber
from ai import prepare_prompt, get_summary, get_voice

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('app/logs/service.log'), logging.StreamHandler()]
)

def initialize_database():
    try:
        db.connect()
        db.create_tables([Article, Subscriber], safe=True)
        print("Database initialized")
    except Exception as e:
        print(f"an error occurred {e}")
    finally:
        if not db.is_closed():
            db.close()

async def send_summary_to_subscribers():
    try:
        subscribers = Subscriber.select()
        chat_ids = [subscriber.chat_id for subscriber in subscribers]
        logging.info(f"sending summary to {len(chat_ids)} subscribers")

        if not chat_ids:
            logging.info("no subs to send summary to")
            return

        speech_file_path = Path(__file__).parent / "speech" / "speech.mp3"
        if not os.path.exists(speech_file_path):
            logging.error(f"voice file {speech_file_path} does not exist")
            return

        with open(speech_file_path, "rb") as voice_file:
            for chat_id in chat_ids:
                try:
                    await telegram_bot.app.bot.send_voice(chat_id=chat_id, voice=voice_file, caption="Here's your daily news summary!")
                    logging.info(f"sent summary to {chat_id}")
                except Exception as e:
                    logging.error(f"an error occurred {e}")

                voice_file.seek(0)

    except Exception as e:
        logging.error(f"an error occurred {e}")

async def scheduler_job():

    logging.info("starting scheduler job")
    articles = get_today_articles()
    prompt = prepare_prompt(articles)
    summary = get_summary(prompt)
    get_voice(summary)

    await send_summary_to_subscribers()
    logging.info("done sending summaries going to sleep")
    await sleep(300)
    await scheduler_job()

def run_bot_in_thread():
    bot_thread = threading.Thread(target=telegram_bot.start_bot, daemon=True)
    bot_thread.start()
    logging.info("Telegram bot started in a separate thread.")


async def main():
    initialize_database()
    await telegram_bot.start_bot()

    await scheduler_job()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("application stopped by user")
        asyncio.run(telegram_bot.stop_bot())