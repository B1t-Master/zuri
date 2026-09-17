import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PassengerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PassengerLogin(BaseModel):
    email: EmailStr
    password: str


class AnonymousSession(BaseModel):
    first_name: str = Field(default="Guest", min_length=1, max_length=120)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # passenger | agent


class PassengerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str | None
    email: str | None
    is_anonymous: bool


class MessageIn(BaseModel):
    conversation_id: uuid.UUID
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender: str
    content: str
    sentiment_score: float | None
    sentiment_label: str | None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    turn_count: int
    escalation_reason: str | None


class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    reason: str
    summary: str
    status: str
    created_at: datetime