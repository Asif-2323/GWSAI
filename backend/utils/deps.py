"""Shared FastAPI dependencies (current-user resolution)."""
from __future__ import annotations

from typing import Annotated

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.mongodb import get_database
from utils.security import decode_access_token

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    """Resolve the authenticated user from the Bearer token."""
    creds_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise creds_error
    except jwt.PyJWTError as exc:
        raise creds_error from exc

    try:
        oid = ObjectId(user_id)
    except (InvalidId, TypeError) as exc:
        raise creds_error from exc

    db = get_database()
    user = await db["users"].find_one({"_id": oid})
    if user is None:
        raise creds_error
    return user
