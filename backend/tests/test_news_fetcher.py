import pytest
from scrapers.news_fetcher import analyze_keywords, calculate_multi_source_score

def test_analyze_keywords_high_tier():
    result = analyze_keywords("PLA announces blockade of Taiwan Strait")
    assert result["level"] == "high"
    assert "blockade" in result["matched_keywords"]

def test_analyze_keywords_medium_tier():
    result = analyze_keywords("China conducts live-fire exercise near Taiwan")
    assert result["level"] == "medium"
    assert "live-fire" in result["matched_keywords"]

def test_analyze_keywords_low_tier():
    result = analyze_keywords("Routine patrol conducted in South China Sea")
    assert result["level"] == "low"
    assert "patrol" in result["matched_keywords"]

def test_analyze_keywords_no_match():
    result = analyze_keywords("Stock market rises on positive economic data")
    assert result["level"] == "none"
    assert result["matched_keywords"] == []

def test_analyze_keywords_chinese():
    result = analyze_keywords("解放军在台海进行实弹演习")
    assert result["level"] == "medium"
    assert "实弹" in result["matched_keywords"]

def test_multi_source_score():
    assert calculate_multi_source_score(1) == 0
    assert calculate_multi_source_score(3) == 5
    assert calculate_multi_source_score(5) == 10
    assert calculate_multi_source_score(7) == 10  # capped
