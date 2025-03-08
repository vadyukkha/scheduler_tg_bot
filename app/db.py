from bson.objectid import ObjectId
from pymongo import MongoClient

from app.config import NAME_OF_COLLECTION, NAME_OF_DATABASE, URI

client = MongoClient(URI)
db = client[NAME_OF_DATABASE]
collection = db[NAME_OF_COLLECTION]


def add_task(user_id, text, deadline):
    task = {
        "user_id": user_id,
        "text": text,
        "deadline": deadline,
        "status": "pending",
    }
    result = collection.insert_one(task)
    return str(result.inserted_id)


def get_tasks(user_id):
    tasks = list(collection.find({"user_id": user_id}))
    for task in tasks:
        task["_id"] = str(task["_id"])
    return tasks


def update_task(user_id, task_id, new_text):
    res = collection.update_one(
        {"user_id": user_id, "_id": ObjectId(task_id)}, {"$set": {"text": new_text}}
    )
    return res.modified_count != 0


def delete_tasks(user_id, date):
    collection.delete_many({"user_id": user_id, "deadline": {"$regex": f"^{date}"}})


def done_task(user_id, task_id):
    res = collection.update_one(
        {"user_id": user_id, "_id": ObjectId(task_id)},
        {"$set": {"status": "done"}},
        upsert=False,
    )
    return res


def delete_done_tasks(user_id):
    collection.delete_many({"user_id": user_id, "status": "done"})
