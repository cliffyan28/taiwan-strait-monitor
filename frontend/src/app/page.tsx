"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { ThreatIndex, ThreatHistoryEntry, MndReport, Aircraft, NewsEvent } from "@/lib/types";
import TopBar from "@/components/TopBar";
import ThreatGauge from "@/components/ThreatGauge";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import RecentEvents from "@/components/RecentEvents";
import StraitMap from "@/components/StraitMap";
import AircraftTrend from "@/components/AircraftTrend";
import CenterlineTrend from "@/components/CenterlineTrend";
import VesselsTrend from "@/components/VesselsTrend";
import ThreatHistory from "@/components/ThreatHistory";
import NewsFeed from "@/components/NewsFeed";

const REFRESH_INTERVAL = 10 * 60 * 1000;

export default function Dashboard() {
  const [threat, setThreat] = useState<ThreatIndex | null>(null);
  const [threatHistory, setThreatHistory] = useState<ThreatHistoryEntry[]>([]);
  const [mndHistory, setMndHistory] = useState<MndReport[]>([]);
  const [aircraft, setAircraft] = useState<Aircraft[]>([]);
  const [aircraftTimestamp, setAircraftTimestamp] = useState("");
  const [news, setNews] = useState<NewsEvent[]>([]);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchAll = useCallback(async () => {
    try {
      const [ti, th, mh, ac, nw] = await Promise.all([
        api.getThreatIndex(),
        api.getThreatHistory(30),
        api.getMndHistory(),
        api.getLiveAircraft(),
        api.getNews(1, 6),
      ]);
      setThreat(ti);
      setThreatHistory(th);
      setMndHistory(mh);
      setAircraft(ac.aircraft);
      setAircraftTimestamp(ac.timestamp);
      setNews(nw.events);
      setLastUpdated(new Date().toLocaleString());
    } catch (e) {
      console.error("Failed to fetch data:", e);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <div className="min-h-screen bg-white">
      <TopBar lastUpdated={lastUpdated} />
      <div className="grid grid-cols-[280px_1fr] min-h-[calc(100vh-52px)]">
        <div className="bg-gray-50 border-r border-gray-300 p-5 space-y-4 overflow-y-auto">
          {threat && (
            <>
              <ThreatGauge score={threat.total_score} level={threat.level} />
              <ScoreBreakdown breakdown={threat.breakdown} />
            </>
          )}
          <div className="border-t border-gray-300 pt-4">
            <RecentEvents reports={mndHistory.slice(0, 5)} />
          </div>
        </div>
        <div className="p-4 space-y-4 overflow-y-auto">
          <div className="grid grid-cols-3 gap-4" style={{ height: 420 }}>
            <ThreatHistory history={threatHistory} />
            <div className="col-span-2">
              <StraitMap aircraft={aircraft} timestamp={aircraftTimestamp} />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4" style={{ height: 280 }}>
            <AircraftTrend reports={mndHistory.slice(0, 30)} />
            <CenterlineTrend reports={mndHistory.slice(0, 30)} />
            <VesselsTrend reports={mndHistory.slice(0, 30)} />
          </div>
          <div style={{ height: 280 }}>
            <NewsFeed events={news} />
          </div>
        </div>
      </div>
    </div>
  );
}
