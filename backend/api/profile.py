"""Citizen profile and recent-search endpoints."""
from __future__ import annotations

from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends

from database.mongodb import get_database
from models.schemas import Profile, SearchRecord
from utils.deps import get_current_user

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=Profile | None)
async def get_profile(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user.get("profile")


@router.put("/profile", response_model=Profile)
async def update_profile(
    profile: Profile,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Profile:
    db = get_database()
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"profile": profile.model_dump()}},
    )
    return profile


@router.get("/searches", response_model=list[SearchRecord])
async def recent_searches(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[SearchRecord]:
    db = get_database()
    cursor = (
        db["searches"]
        .find({"user_id": current_user["_id"]})
        .sort("created_at", -1)
        .limit(10)
    )
    records: list[SearchRecord] = []
    async for doc in cursor:
        records.append(
            SearchRecord(
                id=str(doc["_id"]),
                kind=doc["kind"],
                summary=doc["summary"],
                created_at=doc["created_at"],
            )
        )
    return records


async def record_search(user_id: ObjectId, kind: str, summary: str) -> None:
    """Persist a search/interaction for the dashboard 'recent searches' list."""
    from datetime import datetime, timezone

    db = get_database()
    await db["searches"].insert_one(
        {
            "user_id": user_id,
            "kind": kind,
            "summary": summary,
            "created_at": datetime.now(timezone.utc),
        }
    )
