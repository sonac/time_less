import asyncio
import logging
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

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

async def summarize_and_send():
    logging.info("starting summarization job")
    articles = get_today_articles()
    prompt = prepare_prompt(articles)
    summary = get_summary(prompt)
    get_voice(summary)

    await send_summary_to_subscribers()
    logging.info("done sending summaries going to sleep")

def wait_one_minute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    sleep_duration = (next_minute - now).total_seconds()
    time.sleep(sleep_duration)


async def scheduler_job():
    task_executed_today = False
    while True:
        now = datetime.now(timezone.utc)
        if now.hour == 6 and (now.minute == 0 and not task_executed_today):
            await summarize_and_send()
            task_executed_today = True
        elif now.hour != 6:
            task_executed_today = False
        wait_one_minute()

def scheduler_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduler_job())
    loop.close()

def main():
    initialize_database()
    s_task = threading.Thread(target=scheduler_loop)
    s_task.start()
    #telegram_bot.run_bot()


if __name__ == '__main__':
    try:
        articles = get_today_articles()
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info("application stopped by user")