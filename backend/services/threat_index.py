import json
from datetime import datetime
from config import THREAT_WEIGHTS


def calculate_anomaly_score(current: float, mean: float, std: float, max_score: int) -> float:
    if std == 0:
        return max_score if current > mean else 0
    sigma = (current - mean) / std
    if sigma <= 1.0:
        return 0
    if sigma >= 3.0:
        return max_score
    return round(max_score * (sigma - 1.0) / 2.0, 1)


def calculate_centerline_score(crossings: int, total: int) -> float:
    max_score = THREAT_WEIGHTS["centerline_ratio_max"]
    if total == 0:
        return 0
    ratio = crossings / total
    return round(min(ratio / 0.5, 1.0) * max_score, 1)


def calculate_pattern_score(circumnavigation: bool, night: bool, multi_branch: bool) -> int:
    score = 0
    if circumnavigation:
        score += 5
    if night:
        score += 3
    if multi_branch:
        score += 2
    return min(score, THREAT_WEIGHTS["activity_pattern_max"])


def calculate_news_keyword_score(highest_level: str) -> int:
    scores = {"none": 0, "low": 5, "medium": 12, "high": 20}
    return scores.get(highest_level, 0)


def score_to_level(score: float) -> str:
    if score <= 20:
        return "normal"
    if score <= 40:
        return "elevated"
    if score <= 60:
        return "tense"
    if score <= 80:
        return "high_alert"
    return "crisis"


def calculate_threat_index(
    aircraft_count: int,
    aircraft_mean: float,
    aircraft_std: float,
    vessel_count: int,
    vessel_mean: float,
    vessel_std: float,
    centerline_crossings: int,
    circumnavigation: bool,
    night_activity: bool,
    multi_branch: bool,
    news_keyword_level: str,
    news_source_count: int,
) -> dict:
    from scrapers.news_fetcher import calculate_multi_source_score

    aircraft_score = calculate_anomaly_score(
        aircraft_count, aircraft_mean, aircraft_std,
        THREAT_WEIGHTS["aircraft_anomaly_max"],
    )
    vessel_score = calculate_anomaly_score(
        vessel_count, vessel_mean, vessel_std,
        THREAT_WEIGHTS["vessel_anomaly_max"],
    )
    centerline_score = calculate_centerline_score(centerline_crossings, aircraft_count)
    pattern_score = calculate_pattern_score(circumnavigation, night_activity, multi_branch)
    news_kw_score = calculate_news_keyword_score(news_keyword_level)
    news_ms_score = calculate_multi_source_score(news_source_count)

    total = aircraft_score + vessel_score + centerline_score + pattern_score + news_kw_score + news_ms_score
    total = round(min(total, 100), 1)

    return {
        "total_score": total,
        "level": score_to_level(total),
        "breakdown": {
            "aircraft": aircraft_score,
            "centerline": centerline_score,
            "vessels": vessel_score,
            "pattern": pattern_score,
            "news_nlp": news_kw_score,
            "multi_source": news_ms_score,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def save_threat_index(conn, index_data: dict) -> None:
    conn.execute(
        """INSERT INTO threat_index_history (timestamp, total_score, breakdown, level)
           VALUES (?, ?, ?, ?)""",
        (index_data["timestamp"], index_data["total_score"],
         json.dumps(index_data["breakdown"]), index_data["level"]),
    )
    conn.commit()
