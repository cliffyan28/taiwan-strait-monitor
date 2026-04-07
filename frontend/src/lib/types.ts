export interface ThreatBreakdown {
  aircraft: number;
  centerline: number;
  vessels: number;
  pattern: number;
  port_surge: number;
  port_departure: number;
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
  title_zh: string;
  source: string;
  url: string;
  matched_keywords: string[];
  keyword_level: string;
  language: string;
}

// Satellite SAR port monitoring
export interface SatellitePortSnapshot {
  timestamp: string;
  vessel_count: number;
  mean_background_db: number;
  ais_vessel_count: number | null;
  military_estimate: number | null;
}

export interface SatellitePortHistory {
  timestamp: string;
  vessel_count: number;
  ais_vessel_count: number | null;
  military_estimate: number | null;
}

export interface SatellitePortData {
  port_name: string;
  latest: SatellitePortSnapshot;
  history: SatellitePortHistory[];
  baseline_avg: number;
  baseline_std: number;
  anomaly_sigma: number;
}

export interface SatellitePortsResponse {
  ports: SatellitePortData[];
}
