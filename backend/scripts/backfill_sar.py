"""Backfill SAR port snapshots from March 2026 onwards.

Searches Copernicus catalog for ALL Sentinel-1 products since a start date,
then fetches and processes each one that isn't already in the database.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SAR_PORTS, DB_PATH
from database import get_db, init_db
from services.water_mask import bbox_from_port
from scrapers.sar_processor import (
    get_copernicus_token,
    search_sentinel1_products,
    fetch_sar_clip,
    calibrate_sigma0,
    save_sar_snapshot,
    get_ais_count_at_time,
)
from services.water_mask import get_water_mask, refine_mask_with_sar
from services.cfar import os_cfar_2d, count_vessels
from config import (
    SAR_CFAR_GUARD_CELLS, SAR_CFAR_BG_CELLS, SAR_CFAR_PFA,
    SAR_MIN_VESSEL_PIXELS, SAR_COAST_BUFFER_PIXELS,
)

import numpy as np
from datetime import datetime, timedelta

SINCE = "2025-12-01T00:00:00Z"


def backfill_port(token: str, port: dict) -> int:
    """Backfill all products for one port since SINCE. Returns count of new snapshots."""
    bbox = bbox_from_port(port["lat"], port["lon"], port["radius_km"])

    # Search with higher limit
    min_lon, min_lat, max_lon, max_lat = bbox
    import httpx
    payload = {
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "datetime": f"{SINCE}/..",
        "collections": ["sentinel-1-grd"],
        "limit": 50,
    }
    try:
        resp = httpx.post(
            "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        products = [
            {"id": f["id"], "datetime": f["properties"]["datetime"]}
            for f in features
        ]
    except Exception as e:
        print(f"  Catalog search failed: {e}")
        return 0

    if not products:
        print(f"  No products found")
        return 0

    # Sort oldest first
    products.sort(key=lambda p: p["datetime"])
    print(f"  Found {len(products)} products from {products[0]['datetime'][:10]} to {products[-1]['datetime'][:10]}")

    saved = 0
    for prod in products:
        # Skip if already exists
        conn = get_db(str(DB_PATH))
        existing = conn.execute(
            "SELECT id FROM sar_port_snapshots WHERE port_name = ? AND product_id = ?",
            (port["name"], prod["id"]),
        ).fetchone()
        conn.close()
        if existing:
            continue

        acq_time = prod["datetime"]
        dt = datetime.fromisoformat(acq_time.replace("Z", "+00:00"))
        time_from = (dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        time_to = (dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        time_range = f"{time_from}/{time_to}"

        sar_data = fetch_sar_clip(token, bbox, time_range)
        if sar_data is None:
            print(f"    {acq_time[:10]} - fetch failed, skipping")
            continue

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
        vessel_count, _ = count_vessels(detections, min_pixels=SAR_MIN_VESSEL_PIXELS)

        ais_count, _ = get_ais_count_at_time(port["name"], acq_time)
        military_estimate = None
        if ais_count is not None:
            military_estimate = max(0, vessel_count - ais_count)

        snapshot = {
            "port_name": port["name"],
            "timestamp": acq_time,
            "vessel_count": vessel_count,
            "mean_background_db": round(mean_bg_db, 2),
            "product_id": prod["id"],
            "ais_vessel_count": ais_count,
            "military_estimate": military_estimate,
        }

        conn = get_db(str(DB_PATH))
        save_sar_snapshot(conn, snapshot)
        conn.close()
        saved += 1
        print(f"    {acq_time[:10]} -> {vessel_count} vessels")

        # Small delay to avoid rate limiting
        time.sleep(1)

    return saved


def main():
    client_id = os.environ.get("COPERNICUS_CLIENT_ID", "")
    client_secret = os.environ.get("COPERNICUS_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("Error: COPERNICUS_CLIENT_ID/SECRET not set")
        sys.exit(1)

    init_db(str(DB_PATH))

    token = get_copernicus_token(client_id, client_secret)
    if not token:
        print("Error: Failed to get Copernicus token")
        sys.exit(1)

    total = 0
    for port in SAR_PORTS:
        print(f"\n[{port['name']}]")
        try:
            count = backfill_port(token, port)
            total += count
            print(f"  -> {count} new snapshots")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        # Re-auth every few ports in case token expires
        if SAR_PORTS.index(port) % 5 == 4:
            token = get_copernicus_token(client_id, client_secret) or token

    print(f"\nDone: {total} total new snapshots")


if __name__ == "__main__":
    main()
