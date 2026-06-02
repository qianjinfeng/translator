"""Basic health check and DB connectivity tests."""

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.config import settings

client = TestClient(app)


def setup_module():
    """Create test tables."""
    Base.metadata.create_all(bind=engine)


def teardown_module():
    """Clean up."""
    Base.metadata.drop_all(bind=engine)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["app"] == settings.app_name


def test_list_tasks_empty():
    response = client.get("/api/translation/tasks")
    assert response.status_code == 200
    assert response.json()["tasks"] == []


def test_list_glossaries_empty():
    response = client.get("/api/glossary/")
    assert response.status_code == 200
    assert response.json()["glossaries"] == []
