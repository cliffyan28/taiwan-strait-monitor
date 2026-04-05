import json
import httpx
from datetime import datetime
from config import STRAIT_BBOX, OPENSKY_API_URL

MILITARY_PREFIXES = [
    "RCH", "JAKE", "DUKE", "EVIL", "VIPER",
    "NAVY", "TOPGUN",
    "CNV", "CFC",
    "JASDF", "JCG",
]

CIVIL_PREFIXES = [
    "CCA", "CES", "CSN", "CAL", "EVA", "SIA", "CPA",
    "ANA", "JAL", "KAL", "AAR",
]


def classify_aircraft(callsign: str, origin_country: str) -> str:
    callsign = callsign.strip().upper()
    for prefix in MILITARY_PREFIXES:
        if callsign.startswith(prefix):
            return "military"
    for prefix in CIVIL_PREFIXES:
        if callsign.startswith(prefix):
            return "civil"
    if len(callsign) <= 5 and not any(c.isdigit() for c in callsign[:3]):
        return "unknown"
    return "unknown"


def parse_opensky_response(data: dict) -> list:
    states = data.get("states")
    if not states:
        return []
    results = []
    for s in states:
        if len(s) < 11:
            continue
        callsign = (s[1] or "").strip()
        results.append({
            "icao24": s[0],
            "callsign": callsign,
            "latitude": s[6],
            "longitude": s[5],
            "altitude": s[7],
            "on_ground": s[8],
            "velocity": s[9],
            "heading": s[10],
            "category": classify_aircraft(callsign, s[2] or ""),
        })
    return results


async def poll_opensky() -> list:
    params = {
        "lamin": STRAIT_BBOX["lamin"],
        "lamax": STRAIT_BBOX["lamax"],
        "lomin": STRAIT_BBOX["lomin"],
        "lomax": STRAIT_BBOX["lomax"],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(OPENSKY_API_URL, params=params)
            resp.raise_for_status()
            return parse_opensky_response(resp.json())
        except Exception as e:
            print(f"OpenSky poller error: {e}")
            return []


def save_opensky_snapshot(conn, aircraft_list: list) -> None:
    now = datetime.utcnow().isoformat()
    for ac in aircraft_list:
        conn.execute(
            """INSERT INTO opensky_snapshots
               (timestamp, icao24, callsign, latitude, longitude,
                altitude, velocity, heading, on_ground, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (now, ac["icao24"], ac["callsign"], ac["latitude"],
             ac["longitude"], ac["altitude"], ac["velocity"],
             ac["heading"], ac["on_ground"], ac["category"]),
        )
    conn.commit()
