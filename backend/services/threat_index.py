import json
import statistics
from datetime import datetime
from config import THREAT_WEIGHTS, SAR_PORTS, PORT_ROLES, DB_PATH
from database import get_db


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
    """Tiered centerline scoring based on total aircraft count.

    The tier caps the maximum achievable score so that a small number of
    aircraft crossing the median line cannot produce a disproportionately
    high threat score.

    Tiers (total aircraft -> max achievable):
      0-5   -> 25% of max (5 pts)
      6-15  -> 50% of max (10 pts)
      16-30 -> 75% of max (15 pts)
      31+   -> 100% of max (20 pts)
    """
    max_score = THREAT_WEIGHTS["centerline_ratio_max"]
    if total == 0 or crossings == 0:
        return 0

    # Determine tier ceiling based on total aircraft
    if total <= 5:
        tier_cap = 0.25
    elif total <= 15:
        tier_cap = 0.50
    elif total <= 30:
        tier_cap = 0.75
    else:
        tier_cap = 1.0

    ratio = crossings / total
    raw_score = min(ratio / 0.5, 1.0) * max_score
    return round(min(raw_score, tier_cap * max_score), 1)


def calculate_pattern_score(circumnavigation: bool, night: bool, multi_branch: bool) -> int:
    score = 0
    if circumnavigation:
        score += 5
    if night:
        score += 3
    if multi_branch:
        score += 2
    return min(score, THREAT_WEIGHTS["activity_pattern_max"])


def calculate_port_vessel_scores() -> tuple:
    """Calculate port surge and departure scores from SAR data.

    Uses port role weighting (deployment/forward/buildup), rate-of-change
    detection, and combo signal amplification (deployment ports emptying +
    forward ports filling simultaneously).

    Returns (surge_score, departure_score).
    """
    conn = get_db(str(DB_PATH))
    weighted_surge = 0.0
    weighted_departure = 0.0
    has_deployment_departure = False
    has_forward_surge = False

    for port in SAR_PORTS:
        name = port["name"]
        role_info = PORT_ROLES.get(name)
        if not role_info:
            continue
        weight = role_info["weight"]
        role = role_info["role"]

        rows = conn.execute(
            """SELECT vessel_count FROM sar_port_snapshots
               WHERE port_name = ? ORDER BY timestamp DESC LIMIT 20""",
            (name,),
        ).fetchall()

        if len(rows) < 2:
            continue

        counts = [r["vessel_count"] for r in rows]
        latest = counts[0]
        previous = counts[1]
        mean = statistics.mean(counts)
        std = statistics.stdev(counts) if len(counts) > 1 else 0

        # Sigma (absolute anomaly)
        sigma = (latest - mean) / std if std > 0 else 0.0

        # Delta ratio (rate of change)
        delta_ratio = (latest - previous) / previous if previous > 0 else 0.0

        # Surge signal: abnormally high or rapid increase
        is_surge = sigma >= 2.0 or delta_ratio >= 0.5
        # Departure signal: abnormally low or rapid decrease
        is_departure = sigma <= -2.0 or delta_ratio <= -0.4

        if is_surge:
            weighted_surge += weight
            if role == "forward":
                has_forward_surge = True
        if is_departure:
            weighted_departure += weight
            if role == "deployment":
                has_deployment_departure = True

    conn.close()

    # Combo detection: deployment ports emptying + forward ports filling
    if has_deployment_departure and has_forward_surge:
        weighted_surge *= 1.5
        weighted_departure *= 1.5

    def weighted_to_score(w: float, max_score: int) -> int:
        if w < 1.0:
            return 0
        if w < 2.0:
            return 3
        if w < 3.0:
            return 6
        if w < 5.0:
            return 10
        return max_score

    surge_score = min(weighted_to_score(weighted_surge, THREAT_WEIGHTS["port_surge_max"]), 15)
    departure_score = min(weighted_to_score(weighted_departure, THREAT_WEIGHTS["port_departure_max"]), 15)

    return surge_score, departure_score


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
) -> dict:
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
    port_surge, port_departure = calculate_port_vessel_scores()

    total = (aircraft_score + vessel_score + centerline_score +
             pattern_score + port_surge + port_departure)
    total = round(min(total, 100), 1)

    return {
        "total_score": total,
        "level": score_to_level(total),
        "breakdown": {
            "aircraft": aircraft_score,
            "centerline": centerline_score,
            "vessels": vessel_score,
            "pattern": pattern_score,
            "port_surge": port_surge,
            "port_departure": port_departure,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def save_threat_index(conn, index_data: dict) -> None:
    # Only save if no entry exists in the last hour
    recent = conn.execute(
        """SELECT id FROM threat_index_history
           WHERE timestamp >= datetime(?, '-1 hour')
             AND total_score = ?""",
        (index_data["timestamp"], index_data["total_score"]),
    ).fetchone()
    if recent:
        return

    conn.execute(
        """INSERT INTO threat_index_history (timestamp, total_score, breakdown, level)
           VALUES (?, ?, ?, ?)""",
        (index_data["timestamp"], index_data["total_score"],
         json.dumps(index_data["breakdown"]), index_data["level"]),
    )
    conn.commit()
