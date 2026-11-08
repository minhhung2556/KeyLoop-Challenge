from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_NORMALIZED_RE = re.compile(r"^\+?[0-9]{8,20}$")
LEAD_MESSAGE_MIN_LENGTH = 20
LEAD_MESSAGE_MAX_LENGTH = 2000
LEAD_ATTRIBUTION_MAX_LENGTH = 200


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"


class ActivityType(StrEnum):
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"


class LeadStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: LeadStatus


class LeadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=40)
    message: str = Field(..., min_length=LEAD_MESSAGE_MIN_LENGTH, max_length=LEAD_MESSAGE_MAX_LENGTH)
    vehicleInterest: Optional[str] = Field(default=None, max_length=150)
    utmSource: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)
    utmMedium: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)
    utmCampaign: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)
    utmContent: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)
    utmTerm: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)
    ref: Optional[str] = Field(default=None, max_length=LEAD_ATTRIBUTION_MAX_LENGTH)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name is required")
        return stripped

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        stripped = re.sub(r"[\s\-().]", "", value.strip())
        if not PHONE_NORMALIZED_RE.match(stripped):
            raise ValueError("Invalid phone number")
        return stripped

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < LEAD_MESSAGE_MIN_LENGTH:
            raise ValueError("Message is too short")
        if len(stripped) > LEAD_MESSAGE_MAX_LENGTH:
            raise ValueError("Message is too long")
        return stripped

    @field_validator("vehicleInterest", "utmSource", "utmMedium", "utmCampaign", "utmContent", "utmTerm", "ref")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ActivityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ActivityType = ActivityType.CALL
    summary: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=2000)
    createdBy: str = Field(default="Salesperson", min_length=1, max_length=120)

    @field_validator("summary", "createdBy")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Required")
        return stripped

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    leadId: str
    type: ActivityType
    summary: str
    notes: Optional[str] = None
    createdBy: str
    createdAt: datetime


class LeadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    email: EmailStr
    phone: str
    message: str
    createdAt: datetime
    vehicleInterest: Optional[str] = None
    utmSource: Optional[str] = None
    utmMedium: Optional[str] = None
    utmCampaign: Optional[str] = None
    utmContent: Optional[str] = None
    utmTerm: Optional[str] = None
    ref: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW


class LeadDetailResponse(LeadResponse):
    activities: list[ActivityResponse] = Field(default_factory=list)


class LeadListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LeadResponse]
    total: int
    limit: int
    offset: int
