import os
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
    {"name": "Taipei Times", "url": "https://www.taipeitimes.com/xml/index.rss", "lang": "en"},
    {"name": "SCMP China", "url": "https://www.scmp.com/rss/91/feed/", "lang": "en"},
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml", "lang": "en"},
    {"name": "BBC Asia", "url": "https://feeds.bbci.co.uk/news/world/asia/rss.xml", "lang": "en"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en"},
    {"name": "The Guardian Asia", "url": "https://www.theguardian.com/world/asia-pacific/rss", "lang": "en"},
    {"name": "Japan Times", "url": "https://www.japantimes.co.jp/feed/", "lang": "en"},
    {"name": "环球时报", "url": "https://rss.huanqiu.com/rss/mil", "lang": "zh"},
    {"name": "联合新闻网", "url": "https://udn.com/rssfeed/news/2/6638", "lang": "zh"},
]
NEWS_FETCH_INTERVAL_MINUTES = 60

# NLP keyword filtering: two-layer system
# Layer 1: Context filter — article must match at least one to be considered relevant
CONTEXT_KEYWORDS = [
    # Taiwan Strait core
    "taiwan strait", "taiwan defense", "taiwan military", "taiwan adiz",
    "cross-strait", "taiwan ministry of defense", "taipei defense",
    "taiwan china", "china taiwan", "beijing taipei",
    "civil defense drill", "civil resilience", "taiwan drill",
    "taiwan security", "taiwan armed forces", "taiwan navy",
    "taiwan air force", "taiwan coast guard",
    "taiwan fleet", "taiwan opposition", "taiwan politics",
    # Cross-strait politics
    "kmt china", "kmt beijing", "china visit",
    # PLA / China military
    "people's liberation army", "chinese military", "chinese navy",
    "chinese air force", "china drone", "china military",
    # Stakeholders in Asia-Pacific military
    "indo-pacific", "south china sea", "east china sea",
    "first island chain", "us-taiwan", "us-china military",
    "japan defense", "japan military", "japan drill",
    "philippines military", "philippines drill",
    "quad alliance", "aukus", "us pacific fleet", "seventh fleet",
    # Chinese
    "台海", "台湾海峡", "台湾防务", "解放军", "共军",
    "两岸关系", "东海", "南海", "印太", "第一岛链",
    "国台办", "国防部", "台湾", "军演",
]

# Layer 2: Signal tiers — scored by threat level
KEYWORD_TIERS = {
    "low": {
        "score_range": (2, 5),
        "keywords_en": ["patrol", "training", "surveillance", "reconnaissance",
                        "transit", "deployment", "military aid", "arms sale",
                        "defense budget", "freedom of navigation"],
        "keywords_zh": ["巡逻", "训练", "侦察", "巡航", "部署", "军售", "航行自由"],
    },
    "medium": {
        "score_range": (8, 12),
        "keywords_en": ["exercise", "live-fire", "adiz incursion", "drill",
                        "median line", "carrier strike group", "military buildup",
                        "missile test", "joint exercise", "combat drill"],
        "keywords_zh": ["演习", "实弹", "越中线", "演练", "航母编队",
                        "军事集结", "导弹试射", "联合军演", "战斗演练"],
    },
    "high": {
        "score_range": (15, 20),
        "keywords_en": ["blockade", "combat readiness", "mobilization",
                        "simulated attack", "taiwan invasion", "amphibious assault",
                        "taiwan war", "nuclear threat", "reunification by force",
                        "taiwan conflict"],
        "keywords_zh": ["封锁", "战备", "动员", "模拟攻击", "武统",
                        "攻台", "两栖登陆", "核威胁"],
    },
}

# Threat index weights
THREAT_WEIGHTS = {
    "aircraft_anomaly_max": 25,
    "centerline_ratio_max": 20,
    "vessel_anomaly_max": 15,
    "activity_pattern_max": 10,
    "port_surge_max": 15,
    "port_departure_max": 15,
}

# Sentinel-1 SAR port monitoring
SAR_PORTS = [
    # East Sea Fleet (东部战区海军)
    {"name": "ningbo",          "lat": 29.90, "lon": 121.96, "radius_km": 3},
    {"name": "xiangshan",       "lat": 29.52, "lon": 121.68, "radius_km": 3},
    {"name": "zhoushan",        "lat": 30.02, "lon": 122.10, "radius_km": 3},
    {"name": "sandu_ao",        "lat": 26.66, "lon": 119.63, "radius_km": 3},
    {"name": "xiamen",          "lat": 24.45, "lon": 118.07, "radius_km": 2},
    {"name": "shantou",         "lat": 23.35, "lon": 116.73, "radius_km": 2},
    # South Sea Fleet (南部战区海军)
    {"name": "zhanjiang",       "lat": 21.22, "lon": 110.44, "radius_km": 3},
    {"name": "yulin_west",      "lat": 18.22, "lon": 109.50, "radius_km": 3},
]

# Port roles and weights for threat scoring
# Deployment ports: ships leave during exercises (drop = deployment signal)
# Forward ports: ships arrive during exercises (surge = staging signal)
# Buildup ports: ships accumulate before exercises (pre-exercise indicator)
PORT_ROLES = {
    "yulin_west": {"role": "deployment", "weight": 2.0},
    "zhanjiang":  {"role": "deployment", "weight": 1.5},
    "ningbo":     {"role": "deployment", "weight": 1.0},
    "shantou":    {"role": "deployment", "weight": 1.0},
    "xiamen":     {"role": "forward",    "weight": 1.5},
    "sandu_ao":   {"role": "forward",    "weight": 1.5},
    "zhoushan":   {"role": "buildup",    "weight": 1.2},
    "xiangshan":  {"role": "buildup",    "weight": 1.0},
}

AISSTREAM_API_KEY = os.environ.get("AISSTREAM_API_KEY", "")
AIS_SNAPSHOT_INTERVAL_MINUTES = 5
SAR_CHECK_INTERVAL_HOURS = 12
SAR_CFAR_GUARD_CELLS = 4
SAR_CFAR_BG_CELLS = 16
SAR_CFAR_PFA = 1e-6
SAR_MIN_VESSEL_PIXELS = 10
SAR_COAST_BUFFER_PIXELS = 10
