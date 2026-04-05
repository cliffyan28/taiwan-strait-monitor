import pytest
from services.threat_index import (
    calculate_anomaly_score,
    calculate_centerline_score,
    calculate_pattern_score,
    calculate_news_keyword_score,
    calculate_threat_index,
    score_to_level,
)

def test_anomaly_score_normal():
    assert calculate_anomaly_score(current=10, mean=10, std=5, max_score=25) == 0

def test_anomaly_score_within_1sigma():
    assert calculate_anomaly_score(current=14, mean=10, std=5, max_score=25) == 0

def test_anomaly_score_at_2sigma():
    score = calculate_anomaly_score(current=20, mean=10, std=5, max_score=25)
    assert 10 < score < 15

def test_anomaly_score_at_3sigma():
    assert calculate_anomaly_score(current=25, mean=10, std=5, max_score=25) == 25

def test_anomaly_score_beyond_3sigma_capped():
    assert calculate_anomaly_score(current=50, mean=10, std=5, max_score=25) == 25

def test_anomaly_score_zero_std():
    assert calculate_anomaly_score(current=15, mean=10, std=0, max_score=25) == 25

def test_centerline_score():
    assert calculate_centerline_score(crossings=0, total=20) == 0
    assert calculate_centerline_score(crossings=5, total=20) == 10
    assert calculate_centerline_score(crossings=10, total=20) == 20
    assert calculate_centerline_score(crossings=20, total=20) == 20

def test_pattern_score():
    assert calculate_pattern_score(circumnavigation=False, night=False, multi_branch=False) == 0
    assert calculate_pattern_score(circumnavigation=True, night=False, multi_branch=False) == 5
    assert calculate_pattern_score(circumnavigation=True, night=True, multi_branch=True) == 10

def test_news_keyword_score():
    assert calculate_news_keyword_score("none") == 0
    assert calculate_news_keyword_score("low") == 5
    assert calculate_news_keyword_score("medium") == 12
    assert calculate_news_keyword_score("high") == 20

def test_score_to_level():
    assert score_to_level(10) == "normal"
    assert score_to_level(30) == "elevated"
    assert score_to_level(50) == "tense"
    assert score_to_level(70) == "high_alert"
    assert score_to_level(90) == "crisis"

def test_calculate_threat_index_normal():
    result = calculate_threat_index(
        aircraft_count=10, aircraft_mean=10, aircraft_std=5,
        vessel_count=3, vessel_mean=3, vessel_std=2,
        centerline_crossings=0,
        circumnavigation=False, night_activity=False, multi_branch=False,
        news_keyword_level="none", news_source_count=0,
    )
    assert result["total_score"] < 20
    assert result["level"] == "normal"
