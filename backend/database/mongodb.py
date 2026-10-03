"""MongoDB connection management using Motor (async driver)."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings


class _Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


_mongo = _Mongo()


async def connect_to_mongo() -> None:
    """Open the MongoDB connection and ensure indexes."""
    if _mongo.client is not None:
        return
    _mongo.client = AsyncIOMotorClient(settings.mongodb_uri)
    _mongo.db = _mongo.client[settings.mongodb_db_name]
    # Unique index on user email.
    await _mongo.db["users"].create_index("email", unique=True)
    await _mongo.db["searches"].create_index([("user_id", 1), ("created_at", -1)])


async def close_mongo_connection() -> None:
    if _mongo.client is not None:
        _mongo.client.close()
        _mongo.client = None
        _mongo.db = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database, raising if the app is not connected."""
    if _mongo.db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_to_mongo() first.")
    return _mongo.db
