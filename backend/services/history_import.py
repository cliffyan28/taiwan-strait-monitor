"""Import historical ADIZ data from CSV/JSON for cold-start."""
import csv
import json
from datetime import date
from database import init_db, get_db
from config import DB_PATH


def import_csv(csv_path: str) -> None:
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m services.history_import <csv_path>")
        sys.exit(1)
    import_csv(sys.argv[1])
