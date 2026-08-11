from pymongo import MongoClient

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)


_client = None
_db = None
_collection = None


def get_collection():
    global _client
    global _db
    global _collection

    if _collection is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )

        _db = _client[DATABASE_NAME]
        _collection = _db[COLLECTION_NAME]

    return _collection


def test_connection():
    collection = get_collection()

    collection.database.client.admin.command(
        "ping"
    )

    return True


def find_many(pipeline):
    collection = get_collection()

    return list(
        collection.aggregate(pipeline)
    )


def find_one(pipeline):
    collection = get_collection()

    result = list(
        collection.aggregate(pipeline)
    )

    if result:
        return result[0]

    return None