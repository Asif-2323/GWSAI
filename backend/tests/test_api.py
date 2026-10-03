"""Unit tests for the backend.

Run with:  cd backend && pytest

These tests stub MongoDB with mongomock-motor so they run without a real
database or network access.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import database.mongodb as mongo_module
from agents.common import NO_INFO_MESSAGE, extract_json, profile_summary
from main import app
from utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture(autouse=True)
def _mock_mongo(monkeypatch):
    """Swap the real Mongo connection for an in-memory mock."""
    client = AsyncMongoMockClient()
    db = client["welfare_test"]
    mongo_module._mongo.client = client  # type: ignore[attr-defined]
    mongo_module._mongo.db = db  # type: ignore[attr-defined]

    async def _noop():
        return None

    monkeypatch.setattr(mongo_module, "connect_to_mongo", _noop)
    monkeypatch.setattr(mongo_module, "close_mongo_connection", _noop)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# --- security helpers -----------------------------------------------------
def test_password_hash_roundtrip():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token("user-42")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-42"


# --- agent helpers --------------------------------------------------------
def test_profile_summary_includes_flags():
    summary = profile_summary(
        {
            "full_name": "Asha",
            "age": 65,
            "gender": "female",
            "state": "Kerala",
            "district": "Kochi",
            "occupation": "retired",
            "education": "graduate",
            "annual_income": 50000,
            "category": "general",
            "senior_citizen_status": True,
            "widow_status": True,
        }
    )
    assert "senior citizen" in summary
    assert "widow" in summary


def test_extract_json_from_fenced_block():
    text = '```json\n{"recommendations": []}\n```'
    assert extract_json(text) == {"recommendations": []}


# --- auth flow ------------------------------------------------------------
def test_register_login_and_me(client):
    reg = client.post(
        "/auth/register",
        json={"full_name": "Test User", "email": "t@example.com", "password": "pass123"},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]

    # duplicate registration blocked
    dup = client.post(
        "/auth/register",
        json={"full_name": "Test User", "email": "t@example.com", "password": "pass123"},
    )
    assert dup.status_code == 409

    login = client.post(
        "/auth/login",
        json={"email": "t@example.com", "password": "pass123"},
    )
    assert login.status_code == 200

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "t@example.com"


def test_protected_route_requires_token(client):
    assert client.get("/profile").status_code in (401, 403)


def test_rag_status_reports_not_ready(client):
    res = client.get("/rag/status")
    assert res.status_code == 200
    body = res.json()
    assert body["ready"] is False
    assert body["embedding_model"] == "BAAI/bge-small-en-v1.5"


def test_no_info_message_constant():
    assert "couldn't find" in NO_INFO_MESSAGE
