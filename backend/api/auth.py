"""Authentication endpoints: register, login, current user."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from database.mongodb import get_database
from models.schemas import Token, UserLogin, UserPublic, UserRegister
from utils.deps import get_current_user
from utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(user: dict) -> UserPublic:
    return UserPublic(
        id=str(user["_id"]),
        full_name=user["full_name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister) -> Token:
    db = get_database()
    doc = {
        "full_name": payload.full_name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
        "profile": None,
    }
    try:
        result = await db["users"].insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    doc["_id"] = result.inserted_id
    token = create_access_token(str(result.inserted_id))
    return Token(access_token=token, user=_to_public(doc))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin) -> Token:
    db = get_database()
    user = await db["users"].find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = create_access_token(str(user["_id"]))
    return Token(access_token=token, user=_to_public(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[dict, Depends(get_current_user)]) -> UserPublic:
    return _to_public(current_user)
