import os
from fastapi import APIRouter
from database import get_db
from config import DB_PATH

router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("")
def get_status():
    conn = get_db(str(DB_PATH))
    mnd_last = conn.execute("SELECT MAX(created_at) as ts FROM mnd_reports").fetchone()
    opensky_last = conn.execute("SELECT MAX(timestamp) as ts FROM opensky_snapshots").fetchone()
    news_last = conn.execute("SELECT MAX(created_at) as ts FROM news_events").fetchone()
    mnd_count = conn.execute("SELECT COUNT(*) as c FROM mnd_reports").fetchone()["c"]
    news_count = conn.execute("SELECT COUNT(*) as c FROM news_events").fetchone()["c"]
    conn.close()
    db_size = os.path.getsize(str(DB_PATH)) / (1024 * 1024) if DB_PATH.exists() else 0
    return {
        "mnd_last_run": mnd_last["ts"] if mnd_last else None,
        "opensky_last_run": opensky_last["ts"] if opensky_last else None,
        "news_last_run": news_last["ts"] if news_last else None,
        "db_size_mb": round(db_size, 2),
        "total_mnd_records": mnd_count,
        "total_news_events": news_count,
    }
