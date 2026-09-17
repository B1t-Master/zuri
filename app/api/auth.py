import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import get_current_agent
from app.models import Agent, Passenger
from app.schemas import (
    AnonymousSession,
    PassengerCreate,
    PassengerLogin,
    PassengerOut,
    Token,
)
from app.security import AGENT, PASSENGER, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=PassengerOut, status_code=status.HTTP_201_CREATED)
async def register(payload: PassengerCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Passenger).where(Passenger.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    passenger = Passenger(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(passenger)
    await db.commit()
    await db.refresh(passenger)
    return passenger


@router.post("/login", response_model=Token)
async def login(payload: PassengerLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Passenger).where(Passenger.email == payload.email))
    passenger = result.scalar_one_or_none()
    if passenger is None or passenger.password_hash is None or not verify_password(
        payload.password, passenger.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=str(passenger.id), role=PASSENGER)
    return Token(access_token=token, role=PASSENGER)


@router.post("/anonymous", response_model=Token)
async def anonymous(payload: AnonymousSession, db: AsyncSession = Depends(get_db)):
    passenger = Passenger(first_name=payload.first_name, is_anonymous=True)
    db.add(passenger)
    await db.commit()
    await db.refresh(passenger)
    token = create_access_token(subject=str(passenger.id), role=PASSENGER)
    return Token(access_token=token, role=PASSENGER)


@router.post("/agent/login", response_model=Token)
async def agent_login(payload: dict, db: AsyncSession = Depends(get_db)):
    username = payload.get("username")
    password = payload.get("password")
    if username != settings.agent_username or password != settings.agent_password:
        raise HTTPException(status_code=401, detail="Invalid agent credentials")

    result = await db.execute(select(Agent).where(Agent.email == username))
    agent = result.scalar_one_or_none()
    if agent is None:
        agent = Agent(name=username or "Agent", email=username or settings.agent_username, password_hash=hash_password(password or settings.agent_password))
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

    token = create_access_token(subject=str(agent.id), role=AGENT)
    return Token(access_token=token, role=AGENT)


@router.get("/me", response_model=PassengerOut)
async def me(passenger: Passenger = Depends(get_current_passenger)):
    return passenger