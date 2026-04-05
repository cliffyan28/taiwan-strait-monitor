import asyncio
import json
import statistics
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, get_db
from config import DB_PATH, OPENSKY_POLL_INTERVAL_MINUTES, NEWS_FETCH_INTERVAL_MINUTES
from routers import threat, mnd, aircraft, news, status

scheduler = AsyncIOScheduler()


async def run_mnd_scraper():
    from scrapers.mnd_scraper import fetch_mnd_report, save_mnd_report
    report = await fetch_mnd_report()
    if report:
        conn = get_db(str(DB_PATH))
        save_mnd_report(conn, report)
        conn.close()
        await update_threat_index()
    print(f"MND scraper completed: {report is not None}")


async def run_opensky_poller():
    from scrapers.opensky_poller import poll_opensky, save_opensky_snapshot
    aircraft_list = await poll_opensky()
    if aircraft_list:
        conn = get_db(str(DB_PATH))
        save_opensky_snapshot(conn, aircraft_list)
        conn.close()
    print(f"OpenSky poller: {len(aircraft_list)} aircraft")


async def run_news_fetcher():
    from scrapers.news_fetcher import fetch_news, save_news_events
    events = await fetch_news()
    conn = get_db(str(DB_PATH))
    save_news_events(conn, events)
    conn.close()
    await update_threat_index()
    print(f"News fetcher: {len(events)} relevant events")


async def update_threat_index():
    from services.threat_index import calculate_threat_index, save_threat_index

    conn = get_db(str(DB_PATH))
    rows = conn.execute(
        "SELECT aircraft_count, vessel_count FROM mnd_reports ORDER BY date DESC LIMIT 30"
    ).fetchall()

    if not rows:
        conn.close()
        return

    aircraft_counts = [r["aircraft_count"] for r in rows]
    vessel_counts = [r["vessel_count"] for r in rows]

    aircraft_mean = statistics.mean(aircraft_counts)
    aircraft_std = statistics.stdev(aircraft_counts) if len(aircraft_counts) > 1 else 0
    vessel_mean = statistics.mean(vessel_counts)
    vessel_std = statistics.stdev(vessel_counts) if len(vessel_counts) > 1 else 0

    latest = conn.execute("SELECT * FROM mnd_reports ORDER BY date DESC LIMIT 1").fetchone()

    news_rows = conn.execute(
        "SELECT keyword_level, source FROM news_events WHERE timestamp >= datetime('now', '-1 day')"
    ).fetchall()

    level_priority = {"none": 0, "low": 1, "medium": 2, "high": 3}
    highest_news_level = "none"
    sources = set()
    for nr in news_rows:
        if level_priority.get(nr["keyword_level"], 0) > level_priority.get(highest_news_level, 0):
            highest_news_level = nr["keyword_level"]
        sources.add(nr["source"])

    index_data = calculate_threat_index(
        aircraft_count=latest["aircraft_count"],
        aircraft_mean=aircraft_mean,
        aircraft_std=aircraft_std,
        vessel_count=latest["vessel_count"],
        vessel_mean=vessel_mean,
        vessel_std=vessel_std,
        centerline_crossings=latest["centerline_crossings"],
        circumnavigation=bool(latest["circumnavigation"]),
        night_activity=bool(latest["night_activity"]),
        multi_branch=False,
        news_keyword_level=highest_news_level,
        news_source_count=len(sources),
    )

    save_threat_index(conn, index_data)
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(str(DB_PATH))
    scheduler.add_job(run_mnd_scraper, "cron", hour=6, minute=30, timezone="Asia/Taipei")
    scheduler.add_job(run_opensky_poller, "interval", minutes=OPENSKY_POLL_INTERVAL_MINUTES)
    scheduler.add_job(run_news_fetcher, "interval", minutes=NEWS_FETCH_INTERVAL_MINUTES)
    scheduler.start()
    asyncio.create_task(run_opensky_poller())
    asyncio.create_task(run_news_fetcher())
    yield
    scheduler.shutdown()


app = FastAPI(title="Taiwan Strait Monitor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threat.router)
app.include_router(mnd.router)
app.include_router(aircraft.router)
app.include_router(news.router)
app.include_router(status.router)
