import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from scrapers.sar_processor import (
    get_copernicus_token,
    search_sentinel1_products,
    calibrate_sigma0,
    process_port,
)


def test_calibrate_sigma0():
    """DN values should be converted to sigma0 linear intensity."""
    dn = np.array([[100.0, 200.0], [50.0, 0.0]])
    sigma0 = calibrate_sigma0(dn)
    assert sigma0.shape == (2, 2)
    assert sigma0[0, 0] > 0
    assert sigma0[1, 1] == 0  # zero stays zero


def test_calibrate_sigma0_handles_negatives():
    """Negative values should be clipped to zero."""
    dn = np.array([[-1.0, 5.0]])
    sigma0 = calibrate_sigma0(dn)
    assert sigma0[0, 0] == 0


@patch("scrapers.sar_processor.httpx.post")
def test_get_copernicus_token_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "test_token_123"}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    token = get_copernicus_token("client_id", "client_secret")
    assert token == "test_token_123"


@patch("scrapers.sar_processor.httpx.post")
def test_get_copernicus_token_failure(mock_post):
    mock_post.side_effect = Exception("Connection refused")
    token = get_copernicus_token("client_id", "client_secret")
    assert token is None
