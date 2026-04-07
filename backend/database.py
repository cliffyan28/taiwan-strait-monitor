# backend/database.py
import sqlite3
from pathlib import Path

def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mnd_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            aircraft_count INTEGER NOT NULL DEFAULT 0,
            vessel_count INTEGER NOT NULL DEFAULT 0,
            centerline_crossings INTEGER NOT NULL DEFAULT 0,
            aircraft_types TEXT DEFAULT '{}',
            circumnavigation BOOLEAN DEFAULT 0,
            night_activity BOOLEAN DEFAULT 0,
            raw_html TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS opensky_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            icao24 TEXT NOT NULL,
            callsign TEXT,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            velocity REAL,
            heading REAL,
            on_ground BOOLEAN DEFAULT 0,
            category TEXT DEFAULT 'unknown'
        );

        CREATE TABLE IF NOT EXISTS news_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            title TEXT NOT NULL,
            title_zh TEXT,
            source TEXT,
            url TEXT,
            matched_keywords TEXT DEFAULT '[]',
            keyword_level TEXT DEFAULT 'low',
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS threat_index_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            total_score REAL NOT NULL DEFAULT 0,
            breakdown TEXT DEFAULT '{}',
            level TEXT DEFAULT 'normal'
        );

        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS sar_port_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            vessel_count INTEGER NOT NULL,
            mean_background_db REAL,
            product_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ais_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            vessel_count INTEGER NOT NULL,
            mmsi_list TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_mnd_date ON mnd_reports(date);
        CREATE INDEX IF NOT EXISTS idx_opensky_ts ON opensky_snapshots(timestamp);
        CREATE INDEX IF NOT EXISTS idx_news_ts ON news_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_threat_ts ON threat_index_history(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sar_port ON sar_port_snapshots(port_name, timestamp);
        CREATE INDEX IF NOT EXISTS idx_ais_port_ts ON ais_snapshots(port_name, timestamp);
    """)

    # Migration: add AIS columns to sar_port_snapshots
    for col_sql in [
        "ALTER TABLE sar_port_snapshots ADD COLUMN ais_vessel_count INTEGER DEFAULT NULL",
        "ALTER TABLE sar_port_snapshots ADD COLUMN military_estimate INTEGER DEFAULT NULL",
    ]:
        try:
            conn.execute(col_sql)
        except sqlite3.OperationalError:
            pass  # Column already exists

    conn.close()

def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
