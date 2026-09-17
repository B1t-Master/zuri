from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_agent
from app.models import Agent, Escalation, EscalationStatus
from app.schemas import EscalationOut

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/dashboard/escalations", response_model=list[EscalationOut])
async def list_escalations(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Escalation)
        .where(Escalation.status == EscalationStatus.PENDING)
        .order_by(Escalation.created_at.asc())
    )
    return result.scalars().all()