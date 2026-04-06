import json
from fastapi import APIRouter
from database import get_db
from config import DB_PATH

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
def get_news(page: int = 1, limit: int = 20):
    conn = get_db(str(DB_PATH))
    offset = (page - 1) * limit
    rows = conn.execute(
        "SELECT * FROM news_events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as c FROM news_events").fetchone()["c"]
    conn.close()
    return {
        "total": total,
        "page": page,
        "events": [
            {
                "timestamp": r["timestamp"],
                "title": r["title"],
                "title_zh": r["title_zh"] or "",
                "source": r["source"],
                "url": r["url"],
                "matched_keywords": json.loads(r["matched_keywords"]),
                "keyword_level": r["keyword_level"],
                "language": r["language"],
            }
            for r in rows
        ],
    }
