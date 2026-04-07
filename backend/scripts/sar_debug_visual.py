"""Diagnostic script: visualize SAR image, water mask, CFAR detections, and vessel centroids."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from config import SAR_PORTS, SAR_CFAR_GUARD_CELLS, SAR_CFAR_BG_CELLS, SAR_CFAR_PFA, SAR_MIN_VESSEL_PIXELS, SAR_COAST_BUFFER_PIXELS
from scrapers.sar_processor import (
    get_copernicus_token,
    search_sentinel1_products,
    fetch_sar_clip,
    calibrate_sigma0,
)
from services.cfar import os_cfar_2d, count_vessels
from services.water_mask import get_water_mask, bbox_from_port, refine_mask_with_sar


def debug_port(port_name: str, output_dir: str = "/tmp/sar_debug"):
    os.makedirs(output_dir, exist_ok=True)

    client_id = os.environ.get("COPERNICUS_CLIENT_ID", "")
    client_secret = os.environ.get("COPERNICUS_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("Set COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET")
        return

    port = next((p for p in SAR_PORTS if p["name"] == port_name), None)
    if not port:
        print(f"Port '{port_name}' not found. Available: {[p['name'] for p in SAR_PORTS]}")
        return

    print(f"Processing {port_name} (lat={port['lat']}, lon={port['lon']}, r={port['radius_km']}km)")

    token = get_copernicus_token(client_id, client_secret)
    if not token:
        return

    bbox = bbox_from_port(port["lat"], port["lon"], port["radius_km"])
    since = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    products = search_sentinel1_products(token, bbox, since)
    if not products:
        print("No SAR products found")
        return

    latest = products[0]
    print(f"Product: {latest['id']}, time: {latest['datetime']}")

    dt = datetime.fromisoformat(latest["datetime"].replace("Z", "+00:00"))
    time_from = (dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_to = (dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_range = f"{time_from}/{time_to}"

    print("Fetching SAR clip...")
    sar_data = fetch_sar_clip(token, bbox, time_range)
    if sar_data is None:
        print("Failed to fetch SAR data")
        return

    sigma0 = calibrate_sigma0(sar_data)
    sigma0_db = np.where(sigma0 > 0, 10 * np.log10(sigma0), -30)

    print("Getting water mask...")
    raw_mask, _ = get_water_mask(
        port["name"], port["lat"], port["lon"], port["radius_km"],
        width=sigma0.shape[1], height=sigma0.shape[0],
    )
    water_mask = refine_mask_with_sar(raw_mask, sigma0, coast_buffer=SAR_COAST_BUFFER_PIXELS)

    water_pixels = sigma0[water_mask & (sigma0 > 0)]
    mean_bg_db = float(10 * np.log10(np.mean(water_pixels))) if len(water_pixels) > 0 else -99.0

    raw_pct = 100 * raw_mask.sum() / raw_mask.size
    refined_pct = 100 * water_mask.sum() / water_mask.size
    print(f"Water pixels: raw={raw_pct:.1f}% -> refined={refined_pct:.1f}%")
    print(f"Mean background: {mean_bg_db:.2f} dB")

    print("Running CFAR detection...")
    detections = os_cfar_2d(
        sigma0, water_mask,
        guard_cells=SAR_CFAR_GUARD_CELLS,
        bg_cells=SAR_CFAR_BG_CELLS,
        pfa=SAR_CFAR_PFA,
    )
    vessel_count, centroids = count_vessels(detections, min_pixels=SAR_MIN_VESSEL_PIXELS)
    print(f"Detected: {vessel_count} vessels, {detections.sum()} detection pixels")

    # --- Plot ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(
        f"SAR Debug: {port_name} | {latest['datetime'][:16]} | {vessel_count} vessels | bg={mean_bg_db:.1f}dB",
        fontsize=13, fontweight="bold",
    )

    # 1. SAR image (dB scale)
    ax = axes[0, 0]
    im = ax.imshow(sigma0_db, cmap="gray", vmin=-25, vmax=0)
    ax.set_title("SAR Sigma0 (dB)")
    fig.colorbar(im, ax=ax, shrink=0.7, label="dB")

    # 2. Water mask overlay
    ax = axes[0, 1]
    ax.imshow(sigma0_db, cmap="gray", vmin=-25, vmax=0)
    mask_overlay = np.zeros((*water_mask.shape, 4))
    mask_overlay[~water_mask] = [1, 0, 0, 0.35]  # red = land
    ax.imshow(mask_overlay)
    ax.set_title(f"Water Mask (red=land, {100*water_mask.sum()/water_mask.size:.0f}% water)")

    # 3. CFAR detections
    ax = axes[1, 0]
    ax.imshow(sigma0_db, cmap="gray", vmin=-25, vmax=0)
    det_overlay = np.zeros((*detections.shape, 4))
    det_overlay[detections] = [0, 1, 0, 0.7]  # green = detection
    ax.imshow(det_overlay)
    ax.set_title(f"CFAR Detections ({detections.sum()} pixels)")

    # 4. Final vessels (centroids)
    ax = axes[1, 1]
    ax.imshow(sigma0_db, cmap="gray", vmin=-25, vmax=0)
    for cy, cx in centroids:
        circle = Circle((cx, cy), radius=5, fill=False, edgecolor="cyan", linewidth=1)
        ax.add_patch(circle)
    ax.set_title(f"Vessel Centroids ({vessel_count} vessels, min_pixels={SAR_MIN_VESSEL_PIXELS})")

    for ax in axes.flat:
        ax.set_xticks([])
        ax.set_yticks([])

    plt.tight_layout()
    out_path = os.path.join(output_dir, f"sar_debug_{port_name}.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "xiamen"
    debug_port(port)
