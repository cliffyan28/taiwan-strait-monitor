"""Import historical ADIZ data from CSV/JSON for cold-start."""
import csv
import json
from collections import defaultdict
from datetime import datetime
from database import init_db, get_db
from config import DB_PATH


def import_csv(csv_path: str) -> None:
    """Import CSV with columns: date, aircraft_count, vessel_count,
    centerline_crossings, aircraft_types (pre-aggregated per date)."""
    init_db(str(DB_PATH))
    conn = get_db(str(DB_PATH))
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                """INSERT OR IGNORE INTO mnd_reports
                   (date, aircraft_count, vessel_count, centerline_crossings, aircraft_types)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    row["date"],
                    int(row.get("aircraft_count", 0)),
                    int(row.get("vessel_count", 0)),
                    int(row.get("centerline_crossings", 0)),
                    row.get("aircraft_types", "{}"),
                ),
            )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) as c FROM mnd_reports").fetchone()["c"]
    conn.close()
    print(f"Imported {count} total MND records")


def import_csis_csv(csv_path: str) -> None:
    """Import CSIS ADIZ detailed CSV (one row per aircraft-type per date).
    Aggregates by date before inserting into mnd_reports.

    Expected CSV columns: Date, Aircraft Type, # of Aircraft, Location, Night
    """
    init_db(str(DB_PATH))
    conn = get_db(str(DB_PATH))

    daily = defaultdict(lambda: {
        "aircraft_count": 0,
        "vessel_count": 0,
        "centerline_crossings": 0,
        "aircraft_types": defaultdict(int),
        "night_activity": False,
    })

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_date = row.get("Date", "").strip()
            if not raw_date:
                continue
            try:
                dt = datetime.strptime(raw_date, "%m/%d/%Y")
                iso_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

            try:
                count = int(row.get("# of Aircraft", "0").strip() or "0")
            except ValueError:
                count = 0

            d = daily[iso_date]
            d["aircraft_count"] += count

            location = row.get("Location", "").strip().lower()
            if "median" in location:
                d["centerline_crossings"] += count

            atype = row.get("Aircraft Type", "").strip()
            if atype and atype != "*Unspecified" and count > 0:
                d["aircraft_types"][atype] += count

            night = row.get("Night", "").strip()
            if night and night.lower() not in ("", "0", "no", "false"):
                d["night_activity"] = True

    for iso_date in sorted(daily.keys()):
        d = daily[iso_date]
        types_json = json.dumps(dict(d["aircraft_types"])) if d["aircraft_types"] else "{}"
        conn.execute(
            """INSERT OR IGNORE INTO mnd_reports
               (date, aircraft_count, vessel_count, centerline_crossings,
                aircraft_types, night_activity)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                iso_date,
                d["aircraft_count"],
                d["vessel_count"],
                d["centerline_crossings"],
                types_json,
                1 if d["night_activity"] else 0,
            ),
        )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) as c FROM mnd_reports").fetchone()["c"]
    conn.close()
    print(f"Imported CSIS data: {len(daily)} dates, {count} total MND records")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m services.history_import [--csis] <csv_path>")
        sys.exit(1)
    if sys.argv[1] == "--csis":
        import_csis_csv(sys.argv[2])
    else:
        import_csv(sys.argv[1])
