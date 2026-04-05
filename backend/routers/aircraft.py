from fastapi import APIRouter
from database import get_db
from config import DB_PATH

router = APIRouter(prefix="/api/aircraft", tags=["aircraft"])


@router.get("/live")
def get_live_aircraft():
    conn = get_db(str(DB_PATH))
    latest = conn.execute(
        "SELECT MAX(timestamp) as ts FROM opensky_snapshots"
    ).fetchone()
    if not latest or not latest["ts"]:
        conn.close()
        return {"timestamp": None, "aircraft": []}
    rows = conn.execute(
        "SELECT * FROM opensky_snapshots WHERE timestamp = ?",
        (latest["ts"],),
    ).fetchall()
    conn.close()
    return {
        "timestamp": latest["ts"],
        "aircraft": [
            {
                "icao24": r["icao24"],
                "callsign": r["callsign"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "altitude": r["altitude"],
                "velocity": r["velocity"],
                "heading": r["heading"],
                "on_ground": bool(r["on_ground"]),
                "category": r["category"],
            }
            for r in rows
        ],
    }
