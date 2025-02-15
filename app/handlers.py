from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from db import add_task, delete_tasks, get_tasks, update_task

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот-планировщик задач. Используйте /add, /tasks, /edit, /delete."
    )


@router.message(Command("add"))
async def add(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /add text YYYY-MM-DD HH:MM")
        return

    try:
        datetime.strptime(args[2], "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")
        return

    text, deadline = args[1], args[2]
    task_id = add_task(str(message.from_user.id), text, deadline)
    await message.answer(f"Задача добавлена! ID: {task_id}")


@router.message(Command("tasks"))
async def tasks(message: types.Message):
    user_tasks = get_tasks(str(message.from_user.id))
    if not user_tasks:
        await message.answer("У вас нет задач.")
        return

    msg = "Ваши задачи:\n"
    now = datetime.now()
    for task in user_tasks:
        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
        remaining = (deadline - now).total_seconds() // 3600
        status = (
            "Завершено" if task.get("status") == "done" else f"Осталось {remaining} ч."
        )
        msg += f"{task['_id']}: {task['text']} ({status})\n"

    await message.answer(msg)


@router.message(Command("edit"))
async def edit(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /edit task_id new_text")
        return

    task_id, new_text = args[1], args[2]
    update_task(str(message.from_user.id), task_id, new_text)
    await message.answer("Задача обновлена!")


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
