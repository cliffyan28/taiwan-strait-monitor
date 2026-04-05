export interface ThreatBreakdown {
  aircraft: number;
  centerline: number;
  vessels: number;
  pattern: number;
  news_nlp: number;
  multi_source: number;
}

export interface ThreatIndex {
  total_score: number;
  level: string;
  breakdown: ThreatBreakdown;
  timestamp: string;
}

export interface MndReport {
  date: string;
  aircraft_count: number;
  vessel_count: number;
  centerline_crossings: number;
  aircraft_types: Record<string, number>;
  circumnavigation: boolean;
  night_activity: boolean;
}

export interface Aircraft {
  icao24: string;
  callsign: string;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  velocity: number | null;
  heading: number | null;
  on_ground: boolean;
  category: string;
}

export interface ThreatHistoryEntry {
  timestamp: string;
  total_score: number;
  level: string;
}

export interface NewsEvent {
  timestamp: string;
  title: string;
  source: string;
  url: string;
  matched_keywords: string[];
  keyword_level: string;
  language: string;
}
