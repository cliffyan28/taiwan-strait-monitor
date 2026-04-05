import pytest
from scrapers.opensky_poller import parse_opensky_response, classify_aircraft

SAMPLE_OPENSKY_RESPONSE = {
    "time": 1711900000,
    "states": [
        ["abc123", "CCA123 ", "China", 1711900000, 1711900000,
         120.0, 24.5, 10000, False, 250.0,
         180.0, 0.0, None, 10000, None,
         False, 0],
        ["def456", "RCH456 ", "United States", 1711900000, 1711900000,
         119.5, 25.0, 8000, False, 300.0,
         90.0, 0.0, None, 8000, None,
         False, 0],
    ],
}

def test_parse_opensky_response():
    results = parse_opensky_response(SAMPLE_OPENSKY_RESPONSE)
    assert len(results) == 2
    assert results[0]["icao24"] == "abc123"
    assert results[0]["callsign"] == "CCA123"
    assert results[0]["latitude"] == 24.5
    assert results[0]["longitude"] == 120.0

def test_parse_opensky_empty():
    results = parse_opensky_response({"time": 0, "states": None})
    assert results == []

def test_classify_aircraft_military():
    assert classify_aircraft("RCH456", "United States") == "military"

def test_classify_aircraft_civil():
    assert classify_aircraft("CCA123", "China") == "civil"
