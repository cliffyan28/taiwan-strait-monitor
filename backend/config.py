from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "strait_monitor.db"

# Taiwan Strait bounding box
STRAIT_BBOX = {
    "lamin": 22.0,
    "lamax": 27.0,
    "lomin": 117.0,
    "lomax": 123.0,
}

# OpenSky API
OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
OPENSKY_POLL_INTERVAL_MINUTES = 10

# MND
MND_URL = "https://www.mnd.gov.tw"
MND_SCRAPE_HOUR = 6
MND_SCRAPE_MINUTE = 30

# News RSS feeds
NEWS_FEEDS = [
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews", "lang": "en"},
    {"name": "Taipei Times", "url": "https://www.taipeitimes.com/xml/index.rss", "lang": "en"},
]
NEWS_FETCH_INTERVAL_MINUTES = 60

# NLP keyword tiers
KEYWORD_TIERS = {
    "low": {
        "score_range": (2, 5),
        "keywords_en": ["patrol", "training", "routine", "surveillance"],
        "keywords_zh": ["巡逻", "训练", "例行", "侦察"],
    },
    "medium": {
        "score_range": (8, 12),
        "keywords_en": ["exercise", "live-fire", "adiz entry", "drill", "maneuver"],
        "keywords_zh": ["演习", "实弹", "进入ADIZ", "演练", "机动"],
    },
    "high": {
        "score_range": (15, 20),
        "keywords_en": ["blockade", "combat readiness", "mobilization", "simulated attack", "war", "invasion"],
        "keywords_zh": ["封锁", "战备", "动员", "模拟攻击", "战争", "入侵"],
    },
}

# Threat index weights
THREAT_WEIGHTS = {
    "aircraft_anomaly_max": 25,
    "centerline_ratio_max": 20,
    "vessel_anomaly_max": 15,
    "activity_pattern_max": 10,
    "news_keyword_max": 20,
    "news_multi_source_max": 10,
}
