"""Water mask generation from OSM coastline data for SAR ship detection."""

import json
import os
from pathlib import Path
from math import cos, radians

import numpy as np
import httpx
from shapely.geometry import shape, box, MultiPolygon, Polygon
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds


CACHE_DIR = Path(__file__).parent.parent / "data" / "water_masks"


def bbox_from_port(lat: float, lon: float, radius_km: float) -> tuple:
    """Convert port center + radius to (min_lon, min_lat, max_lon, max_lat)."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * cos(radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def fetch_osm_land_polygons(bbox: tuple) -> list:
    """Download land polygons from OSM Overpass API for the given bbox.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)

    Returns:
        List of shapely Polygon/MultiPolygon geometries representing land.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    overpass_bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    query = f"""
    [out:json][timeout:60];
    (
      way["natural"="coastline"]({overpass_bbox});
      relation["natural"="coastline"]({overpass_bbox});
      way["landuse"]({overpass_bbox});
      relation["boundary"="administrative"]["admin_level"~"[2-4]"]({overpass_bbox});
    );
    out body;
    >;
    out skel qt;
    """
    resp = httpx.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        timeout=90,
    )
    resp.raise_for_status()

    data = resp.json()
    nodes = {}
    ways = {}
    polygons = []

    for elem in data.get("elements", []):
        if elem["type"] == "node":
            nodes[elem["id"]] = (elem["lon"], elem["lat"])
        elif elem["type"] == "way":
            ways[elem["id"]] = elem.get("nodes", [])

    for way_id, node_ids in ways.items():
        coords = [nodes[nid] for nid in node_ids if nid in nodes]
        if len(coords) >= 4 and coords[0] == coords[-1]:
            try:
                poly = Polygon(coords)
                if poly.is_valid and poly.area > 0:
                    polygons.append(poly)
            except Exception:
                continue

    return polygons


def rasterize_water_mask(
    land_polygons: list,
    bbox: tuple,
    width: int = 1000,
    height: int = 1000,
) -> np.ndarray:
    """Rasterize land polygons into a boolean water mask.

    Args:
        land_polygons: list of shapely geometries representing land.
        bbox: (min_lon, min_lat, max_lon, max_lat).
        width: output raster width in pixels.
        height: output raster height in pixels.

    Returns:
        Boolean 2D array. True = water, False = land.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    if not land_polygons:
        return np.ones((height, width), dtype=bool)

    mask = geometry_mask(
        land_polygons,
        out_shape=(height, width),
        transform=transform,
        invert=False,
    )
    return mask


def get_water_mask(port_name: str, lat: float, lon: float, radius_km: float,
                   width: int = 1000, height: int = 1000) -> tuple:
    """Get or create cached water mask for a port.

    Returns:
        (water_mask array, bbox tuple)
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{port_name}.json"
    bbox = bbox_from_port(lat, lon, radius_km)

    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
        mask = np.array(cached["mask"], dtype=bool)
        return mask, tuple(cached["bbox"])

    try:
        land_polygons = fetch_osm_land_polygons(bbox)
    except Exception as e:
        print(f"OSM fetch failed for {port_name}: {e}. Using all-water fallback.")
        land_polygons = []

    mask = rasterize_water_mask(land_polygons, bbox, width, height)

    with open(cache_file, "w") as f:
        json.dump({"bbox": list(bbox), "mask": mask.tolist()}, f)

    return mask, bbox
