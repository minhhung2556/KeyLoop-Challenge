from typing import Optional

from fastapi import APIRouter, Query, status

from app.dependencies import LeadServiceDep
from app.schemas.lead import (
    ActivityCreate,
    ActivityResponse,
    LeadCreate,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    LeadStatus,
    LeadStatusUpdate,
)

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lead(payload: LeadCreate, service: LeadServiceDep) -> LeadResponse:
    return await service.create_lead(payload)


@router.get("", response_model=LeadListResponse)
async def list_leads(
    service: LeadServiceDep,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[LeadStatus] = None,
    q: Optional[str] = None,
) -> LeadListResponse:
    return await service.list_leads(limit=limit, offset=offset, status=status, q=q)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead_detail(lead_id: str, service: LeadServiceDep) -> LeadDetailResponse:
    return await service.get_lead_detail(lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead_status(
    lead_id: str,
    payload: LeadStatusUpdate,
    service: LeadServiceDep,
) -> LeadResponse:
    return await service.update_lead_status(lead_id, payload)


@router.post("/{lead_id}/activities", status_code=status.HTTP_201_CREATED)
async def create_lead_activity(
    lead_id: str,
    payload: ActivityCreate,
    service: LeadServiceDep,
) -> ActivityResponse:
    return await service.log_activity(lead_id, payload)
