import asyncio
from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from celery import shared_task

from app.config import TOKEN
from app.db import collection

bot = Bot(token=TOKEN)


def set_notification_task(user_id, text, diff):
    send_notification.apply_async(args=[user_id, text], countdown=60)


@shared_task(name="send_notification")
def send_notification(user_id, text):
    asyncio.run(bot.send_message(chat_id=user_id, text=f"Напоминание: {text}"))


@shared_task(name="send_info_expired_tasks")
def send_info_expired_tasks():
    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)

    overdue_tasks = collection.find(
        {"deadline": {"$lt": now_msk.strftime("%Y-%m-%d %H:%M")}, "status": "pending"}
    )

    for task in overdue_tasks:
        task_deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
        new_deadline = task_deadline + timedelta(days=1)
        new_deadline_str = new_deadline.strftime("%Y-%m-%d %H:%M")

        collection.update_one(
            {"_id": task["_id"]}, {"$set": {"deadline": new_deadline_str}}
        )

        asyncio.run(
            bot.send_message(
                chat_id=task["user_id"],
                text=f"Задача просрочена! Новый дедлайн: {new_deadline_str}",
            )
        )
