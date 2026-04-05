import json
import feedparser
import httpx
from datetime import datetime
from config import NEWS_FEEDS, KEYWORD_TIERS


def analyze_keywords(text: str) -> dict:
    text_lower = text.lower()
    matched = []
    highest_level = "none"
    level_priority = {"none": 0, "low": 1, "medium": 2, "high": 3}

    for level, tier in KEYWORD_TIERS.items():
        for kw in tier["keywords_en"] + tier["keywords_zh"]:
            if kw.lower() in text_lower:
                matched.append(kw)
                if level_priority[level] > level_priority[highest_level]:
                    highest_level = level

    return {"level": highest_level, "matched_keywords": matched}


def calculate_multi_source_score(source_count: int) -> int:
    if source_count <= 1:
        return 0
    if source_count <= 2:
        return 2
    if source_count <= 4:
        return 5
    return 10


async def fetch_news() -> list:
    results = []
    for feed_config in NEWS_FEEDS:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(feed_config["url"])
                resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined_text = f"{title} {summary}"
                analysis = analyze_keywords(combined_text)
                if analysis["level"] == "none":
                    continue
                published = entry.get("published_parsed")
                ts = datetime(*published[:6]).isoformat() if published else datetime.utcnow().isoformat()
                results.append({
                    "timestamp": ts,
                    "title": title,
                    "source": feed_config["name"],
                    "url": entry.get("link", ""),
                    "matched_keywords": analysis["matched_keywords"],
                    "keyword_level": analysis["level"],
                    "language": feed_config["lang"],
                })
        except Exception as e:
            print(f"News fetch error ({feed_config['name']}): {e}")
    return results


def save_news_events(conn, events: list) -> None:
    for event in events:
        existing = conn.execute(
            "SELECT id FROM news_events WHERE url = ?", (event["url"],)
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """INSERT INTO news_events
               (timestamp, title, source, url, matched_keywords, keyword_level, language)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event["timestamp"], event["title"], event["source"],
             event["url"], json.dumps(event["matched_keywords"]),
             event["keyword_level"], event["language"]),
        )
    conn.commit()
