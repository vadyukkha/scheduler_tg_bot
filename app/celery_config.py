from datetime import timedelta

from celery import Celery

from app.config import REDIS_HOST, REDIS_PORT

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

celery = Celery(
    "notification_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    imports=["app.tasks"],
)


celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=False,
)

celery.conf.beat_schedule = {
    "check-expired-tasks": {
        "task": "send_info_expired_tasks",
        "schedule": timedelta(minutes=1),
    },
}
