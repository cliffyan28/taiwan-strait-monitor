import json
from fastapi import APIRouter
from database import get_db
from config import DB_PATH

router = APIRouter(prefix="/api/mnd", tags=["mnd"])


@router.get("/latest")
def get_latest_mnd():
    conn = get_db(str(DB_PATH))
    row = conn.execute("SELECT * FROM mnd_reports ORDER BY date DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return None
    return {
        "date": row["date"],
        "aircraft_count": row["aircraft_count"],
        "vessel_count": row["vessel_count"],
        "centerline_crossings": row["centerline_crossings"],
        "aircraft_types": json.loads(row["aircraft_types"]),
        "circumnavigation": bool(row["circumnavigation"]),
        "night_activity": bool(row["night_activity"]),
    }


@router.get("/history")
def get_mnd_history(from_date: str = "", to_date: str = ""):
    conn = get_db(str(DB_PATH))
    query = "SELECT * FROM mnd_reports"
    params = []
    conditions = []
    if from_date:
        conditions.append("date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("date <= ?")
        params.append(to_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [
        {
            "date": r["date"],
            "aircraft_count": r["aircraft_count"],
            "vessel_count": r["vessel_count"],
            "centerline_crossings": r["centerline_crossings"],
            "aircraft_types": json.loads(r["aircraft_types"]),
        }
        for r in rows
    ]
