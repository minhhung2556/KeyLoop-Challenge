from __future__ import annotations

from typing import Optional

import structlog
from fastapi import HTTPException, status

from app.repositories.lead_repository import SQLiteLeadRepository
from app.schemas.lead import (
    ActivityCreate,
    ActivityResponse,
    ActivityType,
    LeadCreate,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    LeadStatus,
    LeadStatusUpdate,
)

logger = structlog.get_logger(__name__)

LEAD_NOT_FOUND = "LEAD_NOT_FOUND"


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error_code": LEAD_NOT_FOUND, "message": "Lead not found"},
    )


class LeadService:
    def __init__(self, repo: SQLiteLeadRepository) -> None:
        self.repo = repo

    async def create_lead(self, payload: LeadCreate) -> LeadResponse:
        lead = self.repo.create_lead(payload)
        logger.info("lead_created", lead_id=lead.id, status=lead.status.value)
        return lead

    async def list_leads(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: Optional[LeadStatus] = None,
        q: Optional[str] = None,
    ) -> LeadListResponse:
        items, total = self.repo.list_leads(limit=limit, offset=offset, status=status, q=q)
        return LeadListResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_lead_detail(self, lead_id: str) -> LeadDetailResponse:
        detail = self.repo.get_lead_detail(lead_id)
        if detail is None:
            raise _not_found()
        return detail

    async def update_lead_status(self, lead_id: str, payload: LeadStatusUpdate) -> LeadResponse:
        existing = self.repo.get_lead(lead_id)
        if existing is None:
            raise _not_found()
        updated = self.repo.update_status(lead_id, payload)
        if updated is None:
            raise _not_found()
        self.repo.insert_activity(
            lead_id,
            ActivityCreate(
                type=ActivityType.STATUS_CHANGE,
                summary=f"Status changed to {payload.status.value}",
                createdBy="Salesperson",
            ),
        )
        logger.info("lead_status_updated", lead_id=lead_id, status=payload.status.value)
        return updated

    async def log_activity(self, lead_id: str, payload: ActivityCreate) -> ActivityResponse:
        existing = self.repo.get_lead(lead_id)
        if existing is None:
            raise _not_found()
        next_status = None
        if existing.status == LeadStatus.NEW and payload.type in (
            ActivityType.CALL,
            ActivityType.EMAIL,
        ):
            next_status = LeadStatus.CONTACTED
        activity = self.repo.insert_activity(lead_id, payload, next_status=next_status)
        if activity is None:
            raise _not_found()
        logger.info(
            "lead_activity_logged",
            lead_id=lead_id,
            activity_id=activity.id,
            activity_type=payload.type.value,
        )
        return activity
