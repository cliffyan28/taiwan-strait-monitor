import statistics
from typing import Optional
from fastapi import APIRouter
from database import get_db
from config import DB_PATH, SAR_PORTS

router = APIRouter(prefix="/api/satellite", tags=["satellite"])

CURRENT_PORT_NAMES = [p["name"] for p in SAR_PORTS]


@router.get("/ports")
def get_port_snapshots(port: Optional[str] = None, days: int = 365):
    conn = get_db(str(DB_PATH))

    if port:
        port_names = [port]
    else:
        port_names = CURRENT_PORT_NAMES

    result = []
    for pname in port_names:
        snapshots = conn.execute(
            """SELECT timestamp, vessel_count, mean_background_db, product_id,
                      ais_vessel_count, military_estimate
               FROM sar_port_snapshots
               WHERE port_name = ? AND timestamp >= datetime('now', ? || ' days')
               ORDER BY timestamp DESC""",
            (pname, f"-{days}"),
        ).fetchall()

        if not snapshots:
            continue

        latest = snapshots[0]
        history = [
            {
                "timestamp": s["timestamp"],
                "vessel_count": s["vessel_count"],
                "ais_vessel_count": s["ais_vessel_count"],
                "military_estimate": s["military_estimate"],
            }
            for s in snapshots[1:]
        ]

        all_counts = [s["vessel_count"] for s in snapshots]
        baseline_counts = all_counts[:20]
        baseline_avg = statistics.mean(baseline_counts) if baseline_counts else 0
        baseline_std = statistics.stdev(baseline_counts) if len(baseline_counts) > 1 else 0

        # Use military_estimate for anomaly when available, else vessel_count
        anomaly_value = latest["vessel_count"]
        if latest["military_estimate"] is not None:
            anomaly_value = latest["military_estimate"]

        anomaly_sigma = 0.0
        if baseline_std > 0:
            anomaly_sigma = round((anomaly_value - baseline_avg) / baseline_std, 2)

        result.append({
            "port_name": pname,
            "latest": {
                "timestamp": latest["timestamp"],
                "vessel_count": latest["vessel_count"],
                "mean_background_db": latest["mean_background_db"],
                "ais_vessel_count": latest["ais_vessel_count"],
                "military_estimate": latest["military_estimate"],
            },
            "history": history,
            "baseline_avg": round(baseline_avg, 1),
            "baseline_std": round(baseline_std, 1),
            "anomaly_sigma": anomaly_sigma,
        })

    conn.close()
    return {"ports": result}


@router.get("/ais-status")
def get_ais_status():
    from scrapers.ais_collector import get_ais_status as _get_status
    return _get_status()
