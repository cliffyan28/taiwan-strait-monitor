const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

import type { ThreatIndex, ThreatHistoryEntry, MndReport, Aircraft, NewsEvent, SatellitePortsResponse } from "./types";

export const api = {
  getThreatIndex: () => fetchJSON<ThreatIndex>("/threat-index"),
  getThreatHistory: (days = 30) => fetchJSON<ThreatHistoryEntry[]>(`/threat-index/history?days=${days}`),
  getLatestMnd: () => fetchJSON<MndReport | null>("/mnd/latest"),
  getMndHistory: (from?: string, to?: string) => {
    const params = new URLSearchParams();
    if (from) params.set("from_date", from);
    if (to) params.set("to_date", to);
    return fetchJSON<MndReport[]>(`/mnd/history?${params}`);
  },
  getLiveAircraft: () => fetchJSON<{ timestamp: string; aircraft: Aircraft[] }>("/aircraft/live"),
  getNews: (page = 1, limit = 20) =>
    fetchJSON<{ total: number; events: NewsEvent[] }>(`/news?page=${page}&limit=${limit}`),
  getSatellitePorts: (days = 365) =>
    fetchJSON<SatellitePortsResponse>(`/satellite/ports?days=${days}`),
};
