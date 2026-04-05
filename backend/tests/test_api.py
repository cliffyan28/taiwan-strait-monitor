import os
import pytest

# Patch DB_PATH before importing app
import config
config.DB_PATH = __import__("pathlib").Path("/tmp/test_api_strait.db")

from main import app
from database import init_db
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db("/tmp/test_api_strait.db")
    yield
    if os.path.exists("/tmp/test_api_strait.db"):
        os.remove("/tmp/test_api_strait.db")


def test_threat_index_default():
    resp = client.get("/api/threat-index")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_score" in data
    assert "level" in data


def test_mnd_latest_empty():
    resp = client.get("/api/mnd/latest")
    assert resp.status_code == 200


def test_aircraft_live_empty():
    resp = client.get("/api/aircraft/live")
    assert resp.status_code == 200
    assert resp.json()["aircraft"] == []


def test_news_empty():
    resp = client.get("/api/news")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert "db_size_mb" in resp.json()
