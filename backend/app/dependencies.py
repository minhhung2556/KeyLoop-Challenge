from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.repositories.lead_repository import SQLiteLeadRepository
from app.services.lead_service import LeadService


@lru_cache
def get_repository() -> SQLiteLeadRepository:
    return SQLiteLeadRepository(settings.database_path)


def get_lead_service(
    repo: Annotated[SQLiteLeadRepository, Depends(get_repository)],
) -> LeadService:
    return LeadService(repo)


LeadRepoDep = Annotated[SQLiteLeadRepository, Depends(get_repository)]
LeadServiceDep = Annotated[LeadService, Depends(get_lead_service)]
