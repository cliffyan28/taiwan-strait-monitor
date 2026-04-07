from typing import Optional, List
from pydantic import BaseModel


class ThreatBreakdown(BaseModel):
    aircraft: float = 0
    centerline: float = 0
    vessels: float = 0
    pattern: float = 0
    port_surge: float = 0
    port_departure: float = 0
    # Legacy fields for backwards compat with old DB records
    news_nlp: float = 0
    multi_source: float = 0


class ThreatIndexResponse(BaseModel):
    total_score: float
    level: str
    breakdown: ThreatBreakdown
    timestamp: str


class MndReport(BaseModel):
    date: str
    aircraft_count: int
    vessel_count: int
    centerline_crossings: int
    aircraft_types: dict
    circumnavigation: bool
    night_activity: bool


class AircraftPosition(BaseModel):
    icao24: str
    callsign: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]
    on_ground: bool
    category: str


class NewsEvent(BaseModel):
    timestamp: str
    title: str
    source: str
    url: str
    matched_keywords: List[str]
    keyword_level: str
    language: str


class SystemStatus(BaseModel):
    mnd_last_run: Optional[str]
    opensky_last_run: Optional[str]
    news_last_run: Optional[str]
    db_size_mb: float
    total_mnd_records: int
    total_news_events: int
