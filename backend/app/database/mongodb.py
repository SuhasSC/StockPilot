from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://127.0.0.1:27017"
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "LLM_DB"
)

client = MongoClient(
    MONGODB_URL,
    serverSelectionTimeoutMS=5000
)

database = client[DATABASE_NAME]


def check_mongodb():
    try:
        client.admin.command("ping")
        return {
            "connected": True,
            "database": DATABASE_NAME
        }
    except PyMongoError as error:
        return {
            "connected": False,
            "error": str(error)
        }
