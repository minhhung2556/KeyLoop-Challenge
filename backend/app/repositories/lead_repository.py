from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

from app.schemas.lead import (
    ActivityCreate,
    ActivityResponse,
    ActivityType,
    LeadCreate,
    LeadDetailResponse,
    LeadResponse,
    LeadStatus,
    LeadStatusUpdate,
)

logger = structlog.get_logger(__name__)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  message TEXT NOT NULL,
  vehicleInterest TEXT,
  utmSource TEXT,
  utmMedium TEXT,
  utmCampaign TEXT,
  utmContent TEXT,
  utmTerm TEXT,
  ref TEXT,
  status TEXT NOT NULL,
  createdAt TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lead_activities (
  id TEXT PRIMARY KEY,
  leadId TEXT NOT NULL,
  type TEXT NOT NULL,
  summary TEXT NOT NULL,
  notes TEXT,
  createdBy TEXT NOT NULL,
  createdAt TEXT NOT NULL,
  FOREIGN KEY (leadId) REFERENCES leads(id)
);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(createdAt DESC);
CREATE INDEX IF NOT EXISTS idx_activities_lead ON lead_activities(leadId, createdAt ASC);
"""


class SQLiteLeadRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="init_schema", exc_info=True)
            raise
        finally:
            conn.close()

    def _row_to_lead(self, row: sqlite3.Row) -> LeadResponse:
        data = dict(row)
        return LeadResponse(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            message=data["message"],
            createdAt=datetime.fromisoformat(data["createdAt"]),
            vehicleInterest=data.get("vehicleInterest"),
            utmSource=data.get("utmSource"),
            utmMedium=data.get("utmMedium"),
            utmCampaign=data.get("utmCampaign"),
            utmContent=data.get("utmContent"),
            utmTerm=data.get("utmTerm"),
            ref=data.get("ref"),
            status=LeadStatus(data["status"]),
        )

    def _row_to_activity(self, row: sqlite3.Row) -> ActivityResponse:
        data = dict(row)
        return ActivityResponse(
            id=data["id"],
            leadId=data["leadId"],
            type=ActivityType(data["type"]),
            summary=data["summary"],
            notes=data.get("notes"),
            createdBy=data["createdBy"],
            createdAt=datetime.fromisoformat(data["createdAt"]),
        )

    def count_leads(self) -> int:
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM leads").fetchone()
            return int(row["n"] if row else 0)
        finally:
            conn.close()

    def create_lead(self, payload: LeadCreate) -> LeadResponse:
        lead_id = str(uuid.uuid4())
        now = datetime.utcnow()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO leads (
                  id, name, email, phone, message, vehicleInterest,
                  utmSource, utmMedium, utmCampaign, utmContent, utmTerm, ref,
                  status, createdAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    payload.name,
                    str(payload.email).lower(),
                    payload.phone,
                    payload.message,
                    payload.vehicleInterest,
                    payload.utmSource,
                    payload.utmMedium,
                    payload.utmCampaign,
                    payload.utmContent,
                    payload.utmTerm,
                    payload.ref,
                    LeadStatus.NEW.value,
                    now.isoformat(),
                ),
            )
            conn.commit()
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="create_lead", lead_id=lead_id, exc_info=True)
            raise
        finally:
            conn.close()
        return self.get_lead(lead_id)  # type: ignore[return-value]

    def list_leads(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: Optional[LeadStatus] = None,
        q: Optional[str] = None,
    ) -> tuple[list[LeadResponse], int]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM leads").fetchall()
            leads = [self._row_to_lead(row) for row in rows]
            leads.sort(key=lambda item: item.createdAt, reverse=True)
            if status is not None:
                leads = [lead for lead in leads if lead.status == status]
            needle = (q or "").strip().casefold()
            if needle:
                leads = [lead for lead in leads if self._matches(lead, needle)]
            total = len(leads)
            return leads[offset : offset + limit], total
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="list_leads", exc_info=True)
            raise
        finally:
            conn.close()

    def _matches(self, lead: LeadResponse, needle: str) -> bool:
        parts = (
            lead.name,
            str(lead.email),
            lead.phone,
            lead.message,
            lead.vehicleInterest,
            lead.utmSource,
            lead.utmMedium,
            lead.utmCampaign,
            lead.utmContent,
            lead.utmTerm,
            lead.ref,
        )
        return any(part and needle in str(part).casefold() for part in parts)

    def get_lead(self, lead_id: str) -> Optional[LeadResponse]:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return self._row_to_lead(row) if row else None
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="get_lead", lead_id=lead_id, exc_info=True)
            raise
        finally:
            conn.close()

    def get_lead_detail(self, lead_id: str) -> Optional[LeadDetailResponse]:
        lead = self.get_lead(lead_id)
        if lead is None:
            return None
        activities = self.list_activities(lead_id)
        return LeadDetailResponse(**lead.model_dump(), activities=activities)

    def list_activities(self, lead_id: str) -> list[ActivityResponse]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM lead_activities WHERE leadId = ? ORDER BY createdAt ASC",
                (lead_id,),
            ).fetchall()
            return [self._row_to_activity(row) for row in rows]
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="list_activities", lead_id=lead_id, exc_info=True)
            raise
        finally:
            conn.close()

    def update_status(self, lead_id: str, payload: LeadStatusUpdate) -> Optional[LeadResponse]:
        conn = self._connect()
        try:
            cur = conn.execute(
                "UPDATE leads SET status = ? WHERE id = ?",
                (payload.status.value, lead_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return None
            conn.commit()
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="update_status", lead_id=lead_id, exc_info=True)
            raise
        finally:
            conn.close()
        return self.get_lead(lead_id)

    def insert_activity(
        self,
        lead_id: str,
        payload: ActivityCreate,
        *,
        next_status: Optional[LeadStatus] = None,
        created_at: Optional[datetime] = None,
        activity_id: Optional[str] = None,
    ) -> Optional[ActivityResponse]:
        now = created_at or datetime.utcnow()
        act_id = activity_id or str(uuid.uuid4())
        conn = self._connect()
        try:
            exists = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if not exists:
                return None
            conn.execute(
                """
                INSERT INTO lead_activities (id, leadId, type, summary, notes, createdBy, createdAt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    act_id,
                    lead_id,
                    payload.type.value,
                    payload.summary,
                    payload.notes,
                    payload.createdBy,
                    now.isoformat(),
                ),
            )
            if next_status is not None:
                conn.execute("UPDATE leads SET status = ? WHERE id = ?", (next_status.value, lead_id))
            conn.commit()
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="insert_activity", lead_id=lead_id, exc_info=True)
            raise
        finally:
            conn.close()
        row = ActivityResponse(
            id=act_id,
            leadId=lead_id,
            type=payload.type,
            summary=payload.summary,
            notes=payload.notes,
            createdBy=payload.createdBy,
            createdAt=now,
        )
        return row

    def insert_seed_lead(self, lead: dict[str, Any], activities: list[dict[str, Any]]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO leads (
                  id, name, email, phone, message, vehicleInterest,
                  utmSource, utmMedium, utmCampaign, utmContent, utmTerm, ref,
                  status, createdAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead["id"],
                    lead["name"],
                    lead["email"],
                    lead["phone"],
                    lead["message"],
                    lead.get("vehicleInterest"),
                    lead.get("utmSource"),
                    lead.get("utmMedium"),
                    lead.get("utmCampaign"),
                    lead.get("utmContent"),
                    lead.get("utmTerm"),
                    lead.get("ref"),
                    lead["status"],
                    lead["createdAt"],
                ),
            )
            for act in activities:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO lead_activities
                    (id, leadId, type, summary, notes, createdBy, createdAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        act["id"],
                        lead["id"],
                        act["type"],
                        act["summary"],
                        act.get("notes"),
                        act["createdBy"],
                        act["createdAt"],
                    ),
                )
            conn.commit()
        except sqlite3.Error:
            logger.error("db_operation_failed", operation="insert_seed_lead", lead_id=lead.get("id"), exc_info=True)
            raise
        finally:
            conn.close()
