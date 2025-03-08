from datetime import datetime

import pytz
from aiogram import Router, types
from aiogram.filters import Command
from db import (
    add_task,
    delete_done_tasks,
    delete_tasks,
    done_task,
    get_tasks,
    update_task,
)
from tasks import set_notification_task

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот-планировщик задач. Используйте /add, /tasks, /edit, /delete, /done, /delete_done, /set_notification."
    )


@router.message(Command("add"))
async def add(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Используйте: /add text YYYY-MM-DD HH:MM")
        return

    ans = args[1]
    parts = ans.rsplit(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Используйте: /add text YYYY-MM-DD HH:MM")
        return

    text, deadline = parts[0], parts[1] + " " + parts[2]

    try:
        datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")
        return

    task_id = add_task(str(message.from_user.id), text, deadline)
    await message.answer(f"Задача добавлена! ID: {task_id}")


@router.message(Command("tasks"))
async def tasks(message: types.Message):
    user_id = str(message.from_user.id)
    user_tasks = get_tasks(user_id)
    if not user_tasks:
        await message.answer("У вас нет задач.")
        return

    msg = "Ваши задачи:\n"
    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)

    for task in user_tasks:
        deadline_str = task["deadline"]
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")

        deadline_msk = msk_timezone.localize(deadline)
        remaining = (deadline_msk - now_msk).total_seconds()

        hours = int(abs(remaining) // 3600)
        minutes = int(abs(remaining) // 60 % 60)
        seconds = int(abs(remaining) % 60)

        status = ""
        if task["status"] == "done":
            status = "Выполнено"
        elif remaining > 0:
            status = f"Осталось {hours} часов {minutes} минут {seconds} секунд"
        else:
            status = f"Просрочено на {hours} часов {minutes} минут {seconds} секунд"
        msg += f"{task['_id']}: {task['text']} ({status})\n"

    await message.answer(msg)


@router.message(Command("edit"))
async def edit(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /edit task_id new_text")
        return

    task_id, new_text = args[1], args[2]
    if update_task(str(message.from_user.id), task_id, new_text):
        await message.answer("Задача обновлена!")
    else:
        await message.answer("Указанный task_id не существует!")


@router.message(Command("delete"))
async def delete(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /delete YYYY-MM-DD")
        return

    try:
        datetime.strptime(args[1], "%Y-%m-%d %H:%M")
        delete_tasks(str(message.from_user.id), args[1])
        await message.answer(f"Удалены задачи на {args[1]}")
    except ValueError:
        await message.answer(
            f"Ошибка удаления задач на {args[1]}. Проверьте формат даты."
        )


@router.message(Command("done"))
async def done(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Используйте /done task_id")
        return
    res = done_task(str(message.from_user.id), args[1])
    if res.modified_count == 0:
        await message.answer(
            f"Задача не выполнена, задача с id {args[1]} не существует"
        )
    else:
        await message.answer(f"Задача {args[1]} выполнена")


@router.message(Command("delete_done"))
async def delete_done(message: types.Message):
    delete_done_tasks(str(message.from_user.id))
    await message.answer("Удалены выполненные задачи")


@router.message(Command("set_notification"))
async def set_notification(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /set_notification task_id YYYY-MM-DD HH:MM")
        return

    task_id, deadline = args[1], args[2]
    try:
        deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")
        return

    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)
    deadline_msk = msk_timezone.localize(deadline)
    delay = (deadline_msk - now_msk).total_seconds()

    if delay < 0:
        await message.answer("Указанное время уже прошло.")
        return

    hours = int(delay // 3600)
    minutes = int(delay // 60 % 60)
    seconds = int(delay % 60)

    set_notification_task(
        message.from_user.id, f"Напоминание для задачи {task_id}", int(delay)
    )
    await message.answer(
        f"Напоминание установлено {hours} часов {minutes} минут {seconds} секунд"
    )
