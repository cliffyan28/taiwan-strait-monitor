"""AIS vessel tracking via aisstream.io WebSocket API.

Maintains per-port MMSI tracking dicts, saves snapshots every N minutes,
and exposes get_ais_status() for health checks.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import websockets

from config import SAR_PORTS, AISSTREAM_API_KEY, AIS_SNAPSHOT_INTERVAL_MINUTES, DB_PATH
from database import get_db

# {port_name: {mmsi: last_seen_unix}}
_tracking: Dict[str, Dict[int, float]] = {p["name"]: {} for p in SAR_PORTS}

_status: Dict = {
    "connected": False,
    "last_message_at": None,
    "messages_received": 0,
    "reconnect_count": 0,
    "last_snapshot_at": None,
}

STALE_SECONDS = 30 * 60  # 30 min


def _build_bounding_boxes() -> list:
    """Build [[lat_min, lon_min, lat_max, lon_max], ...] for each port."""
    boxes = []
    for p in SAR_PORTS:
        dlat = p["radius_km"] / 111.0
        dlon = p["radius_km"] / (111.0 * math.cos(math.radians(p["lat"])))
        boxes.append([
            [p["lat"] - dlat, p["lon"] - dlon],
            [p["lat"] + dlat, p["lon"] + dlon],
        ])
    return boxes


def _point_in_port(lat: float, lon: float) -> Optional[str]:
    """Return the port name if (lat, lon) falls within any port radius, else None."""
    for p in SAR_PORTS:
        dlat = p["radius_km"] / 111.0
        dlon = p["radius_km"] / (111.0 * math.cos(math.radians(p["lat"])))
        if (p["lat"] - dlat <= lat <= p["lat"] + dlat and
                p["lon"] - dlon <= lon <= p["lon"] + dlon):
            return p["name"]
    return None


def _prune_stale() -> None:
    """Remove MMSIs not seen in the last STALE_SECONDS."""
    cutoff = time.time() - STALE_SECONDS
    for port_name in _tracking:
        _tracking[port_name] = {
            mmsi: ts for mmsi, ts in _tracking[port_name].items() if ts > cutoff
        }


def _save_snapshots() -> None:
    """Save current vessel counts to the database."""
    _prune_stale()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = get_db(str(DB_PATH))
    try:
        for port_name, mmsis in _tracking.items():
            mmsi_list = sorted(mmsis.keys())
            conn.execute(
                """INSERT INTO ais_snapshots (port_name, timestamp, vessel_count, mmsi_list)
                   VALUES (?, ?, ?, ?)""",
                (port_name, now, len(mmsi_list), json.dumps(mmsi_list)),
            )
        conn.commit()
        _status["last_snapshot_at"] = now
    finally:
        conn.close()


def get_ais_status() -> Dict:
    """Return current AIS collector status for health checks."""
    counts = {p["name"]: len(_tracking[p["name"]]) for p in SAR_PORTS}
    return {**_status, "port_vessel_counts": counts}


async def run_ais_collector() -> None:
    """Main loop: connect to aisstream.io, track vessels, save snapshots."""
    if not AISSTREAM_API_KEY:
        print("AIS collector: AISSTREAM_API_KEY not set, skipping.")
        return

    backoff = 1.0
    bounding_boxes = _build_bounding_boxes()

    subscribe_msg = json.dumps({
        "APIKey": AISSTREAM_API_KEY,
        "BoundingBoxes": bounding_boxes,
        "FilterMessageTypes": ["PositionReport"],
    })

    while True:
        try:
            async with websockets.connect(
                "wss://stream.aisstream.io/v0/stream",
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            ) as ws:
                _status["connected"] = True
                backoff = 1.0
                print("AIS collector: connected to aisstream.io")

                await ws.send(subscribe_msg)

                last_snapshot = time.time()

                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    _status["messages_received"] += 1
                    _status["last_message_at"] = datetime.now(timezone.utc).isoformat()

                    msg_type = msg.get("MessageType")
                    if msg_type != "PositionReport":
                        continue

                    report = msg.get("Message", {}).get("PositionReport", {})
                    meta = msg.get("MetaData", {})

                    lat = report.get("Latitude")
                    lon = report.get("Longitude")
                    mmsi = meta.get("MMSI")

                    if lat is None or lon is None or mmsi is None:
                        continue

                    port = _point_in_port(lat, lon)
                    if port:
                        _tracking[port][mmsi] = time.time()

                    # Save snapshots at interval
                    now = time.time()
                    if now - last_snapshot >= AIS_SNAPSHOT_INTERVAL_MINUTES * 60:
                        _save_snapshots()
                        last_snapshot = now
                        print(f"AIS snapshot saved: {', '.join(f'{p}={len(v)}' for p, v in _tracking.items() if v)}")

        except asyncio.CancelledError:
            _status["connected"] = False
            print("AIS collector: cancelled")
            return
        except Exception as e:
            _status["connected"] = False
            _status["reconnect_count"] += 1
            print(f"AIS collector error: {e}, reconnecting in {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
