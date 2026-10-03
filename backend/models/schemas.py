"""Pydantic models shared across the API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------------------------------------------------------------------------
# Citizen profile / eligibility form
# ---------------------------------------------------------------------------
class Profile(BaseModel):
    full_name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    gender: Literal["male", "female", "other"]
    state: str
    district: str
    occupation: str
    education: str
    annual_income: int = Field(..., ge=0)
    category: Literal["general", "obc", "sc", "st", "ews", "other"]
    disability_status: bool = False
    minority_status: bool = False
    student_status: bool = False
    farmer_status: bool = False
    widow_status: bool = False
    senior_citizen_status: bool = False
    bpl_status: bool = False


# ---------------------------------------------------------------------------
# AI agent responses
# ---------------------------------------------------------------------------
class SchemeRecommendation(BaseModel):
    name: str
    why_eligible: str
    benefits: str
    required_documents: list[str] = []
    application_process: str
    official_website: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommendations: list[SchemeRecommendation]
    sources: list[str] = []
    message: Optional[str] = None


class RoadmapMilestone(BaseModel):
    stage: str  # e.g. "Eligible Now", "Age 25", "Age 60"
    schemes: list[str]
    reasoning: str


class RoadmapResponse(BaseModel):
    milestones: list[RoadmapMilestone]
    sources: list[str] = []
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


# ---------------------------------------------------------------------------
# Recent searches
# ---------------------------------------------------------------------------
class SearchRecord(BaseModel):
    id: str
    kind: Literal["recommendation", "roadmap", "chat"]
    summary: str
    created_at: datetime


# ---------------------------------------------------------------------------
# RAG status
# ---------------------------------------------------------------------------
class RagStatus(BaseModel):
    documents_indexed: int
    chunks_indexed: int
    embedding_model: str
    collection: str
    ready: bool
    message: str
