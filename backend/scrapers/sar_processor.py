"""Sentinel-1 SAR processor: fetch clips from Copernicus, detect vessels, store counts."""

from __future__ import annotations

import os
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

import numpy as np
import httpx
import rasterio

from config import (
    SAR_PORTS,
    SAR_CFAR_GUARD_CELLS,
    SAR_CFAR_BG_CELLS,
    SAR_CFAR_PFA,
    SAR_MIN_VESSEL_PIXELS,
    SAR_COAST_BUFFER_PIXELS,
    DB_PATH,
)
from database import get_db
from services.cfar import os_cfar_2d, count_vessels
from services.water_mask import get_water_mask, bbox_from_port, refine_mask_with_sar


def get_ais_count_at_time(port_name: str, sar_timestamp: str) -> Tuple[Optional[int], Optional[str]]:
    """Query ais_snapshots for the closest record within ±5 min of sar_timestamp.

    Returns (vessel_count, ais_timestamp) or (None, None).
    """
    conn = get_db(str(DB_PATH))
    try:
        row = conn.execute(
            """SELECT vessel_count, timestamp,
                      ABS(strftime('%s', timestamp) - strftime('%s', ?)) AS diff
               FROM ais_snapshots
               WHERE port_name = ?
                 AND ABS(strftime('%s', timestamp) - strftime('%s', ?)) <= 300
               ORDER BY diff ASC
               LIMIT 1""",
            (sar_timestamp, port_name, sar_timestamp),
        ).fetchone()
        if row:
            return row["vessel_count"], row["timestamp"]
        return None, None
    finally:
        conn.close()


COPERNICUS_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)
SENTINEL_HUB_PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
SENTINEL_HUB_CATALOG_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"


def get_copernicus_token(client_id: str, client_secret: str) -> Optional[str]:
    """Get OAuth2 access token from Copernicus Data Space."""
    try:
        resp = httpx.post(
            COPERNICUS_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print(f"Copernicus auth failed: {e}")
        return None


def search_sentinel1_products(token: str, bbox: tuple, since: str) -> List[Dict]:
    """Search for Sentinel-1 IW GRD products covering the bbox since a given date."""
    min_lon, min_lat, max_lon, max_lat = bbox
    payload = {
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "datetime": f"{since}/..",
        "collections": ["sentinel-1-grd"],
        "limit": 10,
    }
    try:
        resp = httpx.post(
            SENTINEL_HUB_CATALOG_URL,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        return [
            {"id": f["id"], "datetime": f["properties"]["datetime"]}
            for f in features
        ]
    except Exception as e:
        print(f"Catalog search failed: {e}")
        return []


def fetch_sar_clip(token: str, bbox: tuple, time_range: str) -> Optional[np.ndarray]:
    """Fetch a Sentinel-1 SAR clip from the Process API."""
    evalscript = """
    //VERSION=3
    function setup() {
      return {
        input: [{ bands: ["VV"] }],
        output: { bands: 1, sampleType: "FLOAT32" }
      };
    }
    function evaluatePixel(sample) {
      return [sample.VV];
    }
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    payload = {
        "input": {
            "bounds": {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [{
                "type": "sentinel-1-grd",
                "dataFilter": {
                    "timeRange": {
                        "from": time_range.split("/")[0],
                        "to": time_range.split("/")[1],
                    },
                    "acquisitionMode": "IW",
                    "polarization": "DV",
                    "resolution": "HIGH",
                },
                "processing": {
                    "backCoeff": "SIGMA0_ELLIPSOID",
                    "orthorectify": True,
                },
            }],
        },
        "output": {
            "width": 1000,
            "height": 1000,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
        },
        "evalscript": evalscript,
    }
    try:
        resp = httpx.post(
            SENTINEL_HUB_PROCESS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "image/tiff",
            },
            timeout=120,
        )
        resp.raise_for_status()
        with rasterio.open(io.BytesIO(resp.content)) as src:
            data = src.read(1).astype(np.float64)
        return data
    except Exception as e:
        print(f"Process API fetch failed: {e}")
        return None


def calibrate_sigma0(data: np.ndarray) -> np.ndarray:
    """Convert raw data to sigma0 linear intensity.

    When using Process API with backCoeff=SIGMA0_ELLIPSOID, data is already
    calibrated sigma0 in linear scale. Just clip negatives.
    """
    return np.clip(data, 0, None)


def process_port(token: str, port: Dict) -> Optional[Dict]:
    """Process one port: search, fetch, detect, count."""
    bbox = bbox_from_port(port["lat"], port["lon"], port["radius_km"])

    conn = get_db(str(DB_PATH))
    last_row = conn.execute(
        "SELECT timestamp FROM sar_port_snapshots WHERE port_name = ? ORDER BY timestamp DESC LIMIT 1",
        (port["name"],),
    ).fetchone()
    conn.close()

    since = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    if last_row:
        ts = last_row["timestamp"]
        since = ts if ts.endswith("Z") else ts + "Z"

    products = search_sentinel1_products(token, bbox, since)
    if not products:
        return None

    latest = products[0]
    acq_time = latest["datetime"]

    conn = get_db(str(DB_PATH))
    existing = conn.execute(
        "SELECT id FROM sar_port_snapshots WHERE port_name = ? AND product_id = ?",
        (port["name"], latest["id"]),
    ).fetchone()
    conn.close()
    if existing:
        return None

    dt = datetime.fromisoformat(acq_time.replace("Z", "+00:00"))
    time_from = (dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_to = (dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_range = f"{time_from}/{time_to}"

    sar_data = fetch_sar_clip(token, bbox, time_range)
    if sar_data is None:
        return None

    sigma0 = calibrate_sigma0(sar_data)

    raw_mask, _ = get_water_mask(
        port["name"], port["lat"], port["lon"], port["radius_km"],
        width=sigma0.shape[1], height=sigma0.shape[0],
    )
    water_mask = refine_mask_with_sar(raw_mask, sigma0, coast_buffer=SAR_COAST_BUFFER_PIXELS)

    water_pixels = sigma0[water_mask & (sigma0 > 0)]
    if len(water_pixels) > 0:
        mean_bg_db = float(10 * np.log10(np.mean(water_pixels)))
    else:
        mean_bg_db = -99.0

    detections = os_cfar_2d(
        sigma0, water_mask,
        guard_cells=SAR_CFAR_GUARD_CELLS,
        bg_cells=SAR_CFAR_BG_CELLS,
        pfa=SAR_CFAR_PFA,
    )

    vessel_count, centroids = count_vessels(detections, min_pixels=SAR_MIN_VESSEL_PIXELS)

    # AIS cross-reference for dark vessel detection
    ais_count, ais_ts = get_ais_count_at_time(port["name"], acq_time)
    military_estimate = None
    if ais_count is not None:
        military_estimate = max(0, vessel_count - ais_count)

    return {
        "port_name": port["name"],
        "timestamp": acq_time,
        "vessel_count": vessel_count,
        "mean_background_db": round(mean_bg_db, 2),
        "product_id": latest["id"],
        "ais_vessel_count": ais_count,
        "military_estimate": military_estimate,
    }


def save_sar_snapshot(conn, snapshot: Dict) -> None:
    """Save a SAR port snapshot to the database."""
    conn.execute(
        """INSERT INTO sar_port_snapshots
           (port_name, timestamp, vessel_count, mean_background_db, product_id,
            ais_vessel_count, military_estimate)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            snapshot["port_name"],
            snapshot["timestamp"],
            snapshot["vessel_count"],
            snapshot["mean_background_db"],
            snapshot["product_id"],
            snapshot.get("ais_vessel_count"),
            snapshot.get("military_estimate"),
        ),
    )
    conn.commit()


def process_all_ports() -> int:
    """Process all configured ports. Returns number of new snapshots saved."""
    client_id = os.environ.get("COPERNICUS_CLIENT_ID", "")
    client_secret = os.environ.get("COPERNICUS_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("SAR processor: COPERNICUS_CLIENT_ID/SECRET not configured, skipping.")
        return 0

    token = get_copernicus_token(client_id, client_secret)
    if not token:
        return 0

    saved = 0
    for port in SAR_PORTS:
        try:
            result = process_port(token, port)
            if result:
                conn = get_db(str(DB_PATH))
                save_sar_snapshot(conn, result)
                conn.close()
                saved += 1
                print(f"SAR: {port['name']} -> {result['vessel_count']} vessels detected")
            else:
                print(f"SAR: {port['name']} -> no new data")
        except Exception as e:
            print(f"SAR error ({port['name']}): {e}")

    return saved
