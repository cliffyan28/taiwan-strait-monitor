import re
import httpx
from datetime import datetime
from config import STRAIT_BBOX, OPENSKY_API_URL

MILITARY_PREFIXES = [
    # US military
    "RCH", "REACH", "ATLAS",          # USAF Air Mobility Command
    "JAKE", "DUKE", "EVIL", "VIPER",  # USAF/USN fighter callsigns
    "HAVOC", "GHOST", "COBRA",
    "NAVY", "TOPGUN", "CNV",          # US Navy
    "CFC",                             # Combined Forces Command
    "BART", "USNAV",
    # Japan
    "JASDF", "JCG",                   # Japan Air Self-Defense Force / Coast Guard
    # Taiwan military
    "ROC",                             # Republic of China military
]

CIVIL_PREFIXES = [
    # Taiwan
    "CAL",  # China Airlines 中華航空
    "EVA",  # EVA Air 長榮航空
    "MDA",  # Mandarin Airlines 華信航空
    "SJX",  # StarLux Airlines 星宇航空
    "TTW",  # Tigerair Taiwan 台灣虎航
    "TWB",  # Far Eastern / charter Taiwan
    "TAX",  # charter Taiwan
    "TLM",  # charter Taiwan
    "TVJ",  # charter Taiwan
    "TVS",  # charter Taiwan
    "SYB",  # charter Taiwan
    "TGW",  # Tigerair Taiwan / Thai charter
    "UIA",  # Uni Air 立榮航空 (subsidiary of EVA)
    # China (Mainland)
    "CCA",  # Air China 中國國際航空
    "CES",  # China Eastern 中國東方航空
    "CSN",  # China Southern 中國南方航空
    "CSH",  # Shanghai Airlines 上海航空
    "CHH",  # Hainan Airlines 海南航空
    "CQH",  # Spring Airlines 春秋航空
    "CXA",  # Xiamen Airlines 廈門航空
    "CDC",  # Chengdu Airlines 成都航空
    "CDG",  # regional/cargo China
    "DKH",  # Donghai Airlines 東海航空
    "JYH",  # Joy Air 幸福航空
    "MJJ",  # Minshan Airlines / charter China
    "HGB",  # regional/cargo China
    # Hong Kong / Macau
    "CPA",  # Cathay Pacific 國泰航空
    "CRK",  # Hong Kong Airlines 香港航空
    "HKE",  # HK Express 香港快運
    "AMU",  # Air Macau 澳門航空
    # Korea
    "KAL",  # Korean Air 大韓航空
    "AAR",  # Asiana Airlines 韓亞航空
    "JJA",  # Jeju Air 濟州航空
    "ABL",  # Air Busan 釜山航空
    "TTW",  # T'Way Air (also Tigerair TW)
    # Japan
    "ANA",  # All Nippon Airways 全日空
    "JAL",  # Japan Airlines 日本航空
    "JJP",  # Jetstar Japan
    "APJ",  # Peach Aviation
    "JNA",  # Japan regional carrier
    # Southeast Asia
    "SIA",  # Singapore Airlines 新加坡航空
    "THA",  # Thai Airways 泰國航空
    "PAL",  # Philippine Airlines 菲律賓航空
    "APZ",  # regional charter
    # Cargo
    "FDX",  # FedEx Express
    "UPS",  # UPS Airlines
    "ABX",  # ABX Air
    # International
    "UAE",  # Emirates 阿聯酋航空
    "UAL",  # United Airlines 聯合航空
    "MAS",  # Malaysia Airlines 馬來西亞航空
    "QDA",  # Qingdao Airlines 青島航空
]

# Registration-number patterns → civil
# N12345  : US FAA (private/GA/cargo)
# B12345  : Chinese mainland / Taiwan / HK registration (CAAC/CAA)
# JA1234  : Japanese civil registration
# HL1234  : Korean civil registration
# RP-C... : Philippine civil registration
# 9V-...  : Singapore civil registration
# VH-...  : Australian civil registration
# VP-C/VR-C: Cayman Islands / overseas territories (private jets)
_CIVIL_REG_PATTERNS = re.compile(
    r'^(N[0-9]|B[0-9A-F]|JA[0-9]|HL[0-9]|RP[0-9C]|9V|VH|VP[A-Z]|VR[A-Z])'
)


def classify_aircraft(callsign: str, origin_country: str) -> str:
    callsign = callsign.strip().upper()
    if not callsign:
        return "unknown"

    for prefix in MILITARY_PREFIXES:
        if callsign.startswith(prefix):
            return "military"

    for prefix in CIVIL_PREFIXES:
        if callsign.startswith(prefix):
            return "civil"

    # Registration number patterns (no airline prefix → private/GA)
    if _CIVIL_REG_PATTERNS.match(callsign):
        return "civil"

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
