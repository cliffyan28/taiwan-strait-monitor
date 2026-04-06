import numpy as np
import pytest
from services.cfar import os_cfar_2d


def test_cfar_detects_bright_target_on_dark_background():
    """A single bright pixel on uniform dark background should be detected."""
    img = np.full((100, 100), 0.01, dtype=np.float64)
    img[50, 50] = 10.0  # bright target
    mask = np.ones((100, 100), dtype=bool)  # all water

    detections = os_cfar_2d(img, mask, guard_cells=4, bg_cells=16, pfa=1e-4, os_rank=0.75)

    assert detections[50, 50] == True
    assert detections.sum() >= 1
    assert detections.sum() < 10  # not too many false alarms


def test_cfar_ignores_land_pixels():
    """Bright pixels masked as land should not be detected."""
    img = np.full((100, 100), 0.01, dtype=np.float64)
    img[50, 50] = 10.0
    mask = np.ones((100, 100), dtype=bool)
    mask[50, 50] = False  # mark target pixel as land

    detections = os_cfar_2d(img, mask, guard_cells=4, bg_cells=16, pfa=1e-4, os_rank=0.75)

    assert detections[50, 50] == False


def test_cfar_no_false_alarms_on_uniform_background():
    """Uniform background should produce zero or near-zero detections."""
    np.random.seed(42)
    img = np.random.exponential(scale=0.01, size=(100, 100))
    mask = np.ones((100, 100), dtype=bool)

    detections = os_cfar_2d(img, mask, guard_cells=4, bg_cells=16, pfa=1e-4, os_rank=0.75)

    # With Pfa=1e-4 on 10000 water pixels, expect ~1 false alarm max
    assert detections.sum() <= 3


def test_cfar_detects_multiple_targets():
    """Multiple bright targets should all be detected."""
    img = np.full((100, 100), 0.01, dtype=np.float64)
    targets = [(20, 30), (50, 50), (70, 80)]
    for r, c in targets:
        img[r, c] = 10.0
    mask = np.ones((100, 100), dtype=bool)

    detections = os_cfar_2d(img, mask, guard_cells=4, bg_cells=16, pfa=1e-4, os_rank=0.75)

    for r, c in targets:
        assert detections[r, c] == True


def test_cfar_returns_correct_shape():
    img = np.ones((50, 60), dtype=np.float64)
    mask = np.ones((50, 60), dtype=bool)
    detections = os_cfar_2d(img, mask, guard_cells=2, bg_cells=8, pfa=1e-3, os_rank=0.75)
    assert detections.shape == (50, 60)
    assert detections.dtype == bool
