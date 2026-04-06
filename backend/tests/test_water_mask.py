import numpy as np
import pytest
from services.water_mask import bbox_from_port, rasterize_water_mask


def test_bbox_from_port():
    """Bounding box should be centered on port with correct radius."""
    bbox = bbox_from_port(lat=24.45, lon=118.08, radius_km=5)
    assert len(bbox) == 4  # (min_lon, min_lat, max_lon, max_lat)
    min_lon, min_lat, max_lon, max_lat = bbox
    assert min_lat < 24.45 < max_lat
    assert min_lon < 118.08 < max_lon
    # ~5km is ~0.045 degrees
    assert abs((max_lat - min_lat) / 2 - 0.045) < 0.01


def test_rasterize_water_mask_returns_correct_shape():
    """Water mask should match the requested pixel dimensions."""
    # Create a simple polygon covering the whole bbox (all water)
    bbox = (118.0, 24.4, 118.1, 24.5)
    land_polygons = []  # no land
    mask = rasterize_water_mask(land_polygons, bbox, width=100, height=100)
    assert mask.shape == (100, 100)
    assert mask.dtype == bool
    assert mask.all()  # no land → all water


def test_rasterize_water_mask_with_land():
    """Land polygon should create False pixels in mask."""
    from shapely.geometry import box
    bbox = (118.0, 24.4, 118.1, 24.5)
    # Land covering the left half
    land = box(118.0, 24.4, 118.05, 24.5)
    mask = rasterize_water_mask([land], bbox, width=100, height=100)
    assert mask.shape == (100, 100)
    # Left half should be land (False), right half water (True)
    assert not mask[:, :50].all()  # some land on left
    assert mask[:, 75:].all()  # all water on right
