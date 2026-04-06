import json
import re
import feedparser
import httpx
from datetime import datetime
from deep_translator import GoogleTranslator
from config import NEWS_FEEDS, KEYWORD_TIERS, CONTEXT_KEYWORDS

# Keywords that are too short and might match common words — require word boundaries
_WORD_BOUNDARY_KEYWORDS = {"pla", "plan", "plaaf"}

def is_relevant(text: str) -> bool:
    """Layer 1: Check if article is related to Taiwan Strait / Asia-Pacific military."""
    text_lower = text.lower()
    for kw in CONTEXT_KEYWORDS:
        kw_lower = kw.lower()
        if kw_lower in _WORD_BOUNDARY_KEYWORDS:
            if re.search(r'\b' + re.escape(kw_lower) + r'\b', text_lower):
                return True
        else:
            if kw_lower in text_lower:
                return True
    return False


def analyze_keywords(text: str) -> dict:
    """Layer 2: Score by threat signal tier. Only called after is_relevant passes."""
    text_lower = text.lower()
    matched = []
    highest_level = "low"  # Default to low if context-relevant but no signal keywords
    level_priority = {"low": 1, "medium": 2, "high": 3}

    for level, tier in KEYWORD_TIERS.items():
        for kw in tier["keywords_en"] + tier["keywords_zh"]:
            if kw.lower() in text_lower:
                matched.append(kw)
                if level_priority.get(level, 0) > level_priority.get(highest_level, 0):
                    highest_level = level

    return {"level": highest_level, "matched_keywords": matched if matched else ["taiwan-strait-related"]}


def translate_to_zh(text: str) -> str:
    """Translate English text to Chinese. Returns empty string on failure."""
    try:
        return GoogleTranslator(source='en', target='zh-CN').translate(text) or ""
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


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
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(feed_config["url"])
                resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined_text = f"{title} {summary}"

                # Layer 1: context relevance check
                if not is_relevant(combined_text):
                    continue

                # Layer 2: threat signal scoring
                analysis = analyze_keywords(combined_text)

                published = entry.get("published_parsed")
                ts = datetime(*published[:6]).isoformat() if published else datetime.utcnow().isoformat()

                # Translate English titles to Chinese
                title_zh = ""
                if feed_config["lang"] == "en":
                    title_zh = translate_to_zh(title)

                results.append({
                    "timestamp": ts,
                    "title": title,
                    "title_zh": title_zh,
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
               (timestamp, title, title_zh, source, url, matched_keywords, keyword_level, language)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event["timestamp"], event["title"], event.get("title_zh", ""),
             event["source"], event["url"], json.dumps(event["matched_keywords"]),
             event["keyword_level"], event["language"]),
        )
    conn.commit()
