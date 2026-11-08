import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.dependencies import get_repository
from app.main import app
from app.repositories.lead_repository import SQLiteLeadRepository


@pytest.fixture
def client(tmp_path):
    repo = SQLiteLeadRepository(tmp_path / "test.db")
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
