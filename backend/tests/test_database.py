# backend/tests/test_database.py
import sqlite3
import os
import pytest
from database import init_db, get_db

TEST_DB = "/tmp/test_strait_monitor.db"

@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_init_db_creates_tables():
    init_db(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert "mnd_reports" in tables
    assert "opensky_snapshots" in tables
    assert "news_events" in tables
    assert "threat_index_history" in tables
    assert "config" in tables

def test_get_db_returns_connection():
    init_db(TEST_DB)
    conn = get_db(TEST_DB)
    assert conn is not None
    conn.close()
