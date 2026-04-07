import json
from fastapi import APIRouter
from models import ThreatIndexResponse, ThreatBreakdown
from database import get_db
from config import DB_PATH

router = APIRouter(prefix="/api/threat-index", tags=["threat"])


@router.get("", response_model=ThreatIndexResponse)
def get_current_threat_index():
    conn = get_db(str(DB_PATH))
    row = conn.execute(
        "SELECT * FROM threat_index_history ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return ThreatIndexResponse(
            total_score=0,
            level="normal",
            breakdown=ThreatBreakdown(
                aircraft=0, centerline=0, vessels=0, pattern=0, port_surge=0, port_departure=0
            ),
            timestamp="",
        )
    breakdown = json.loads(row["breakdown"])
    return ThreatIndexResponse(
        total_score=row["total_score"],
        level=row["level"],
        breakdown=ThreatBreakdown(**breakdown),
        timestamp=row["timestamp"],
    )


@router.get("/history")
def get_threat_history(days: int = 30):
    conn = get_db(str(DB_PATH))
    rows = conn.execute(
        "SELECT * FROM threat_index_history WHERE timestamp >= datetime('now', ? || ' days') ORDER BY timestamp",
        (f"-{days}",),
    ).fetchall()
    conn.close()
    return [
        {
            "timestamp": r["timestamp"],
            "total_score": r["total_score"],
            "level": r["level"],
            "breakdown": json.loads(r["breakdown"]),
        }
        for r in rows
    ]
