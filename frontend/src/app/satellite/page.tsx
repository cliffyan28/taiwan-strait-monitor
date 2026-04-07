"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { SatellitePortData, SatellitePortHistory } from "@/lib/types";
import TopBar from "@/components/TopBar";
import PortOverviewCards from "@/components/satellite/PortOverviewCards";
import PortVesselChart from "@/components/satellite/PortVesselChart";
import PortMap from "@/components/satellite/PortMap";

const REFRESH_INTERVAL = 10 * 60 * 1000;

/** Merge yulin_west + yulin_east into a single "yulin" entry for display. */
function mergeYulinPorts(ports: SatellitePortData[]): SatellitePortData[] {
  const west = ports.find((p) => p.port_name === "yulin_west");
  const east = ports.find((p) => p.port_name === "yulin_east");
  const others = ports.filter(
    (p) => p.port_name !== "yulin_west" && p.port_name !== "yulin_east"
  );

  if (!west && !east) return ports;
  if (!west) return [...others, { ...east!, port_name: "yulin" }];
  if (!east) return [...others, { ...west!, port_name: "yulin" }];

  const addNullable = (a: number | null, b: number | null): number | null =>
    a != null && b != null ? a + b : a ?? b;

  // Merge history by timestamp
  const historyMap = new Map<string, SatellitePortHistory>();
  for (const h of [...west.history, ...east.history]) {
    const key = h.timestamp.slice(0, 10);
    const existing = historyMap.get(key);
    if (existing) {
      existing.vessel_count += h.vessel_count;
      existing.ais_vessel_count = addNullable(existing.ais_vessel_count, h.ais_vessel_count);
      existing.military_estimate = addNullable(existing.military_estimate, h.military_estimate);
    } else {
      historyMap.set(key, { ...h });
    }
  }

  const merged: SatellitePortData = {
    port_name: "yulin",
    latest: {
      timestamp: west.latest.timestamp > east.latest.timestamp ? west.latest.timestamp : east.latest.timestamp,
      vessel_count: west.latest.vessel_count + east.latest.vessel_count,
      mean_background_db: Math.min(west.latest.mean_background_db, east.latest.mean_background_db),
      ais_vessel_count: addNullable(west.latest.ais_vessel_count, east.latest.ais_vessel_count),
      military_estimate: addNullable(west.latest.military_estimate, east.latest.military_estimate),
    },
    history: Array.from(historyMap.values()).sort(
      (a, b) => a.timestamp.localeCompare(b.timestamp)
    ),
    baseline_avg: Math.round((west.baseline_avg + east.baseline_avg) * 10) / 10,
    baseline_std: Math.round(Math.sqrt(west.baseline_std ** 2 + east.baseline_std ** 2) * 10) / 10,
    anomaly_sigma: Math.max(west.anomaly_sigma, east.anomaly_sigma),
  };

  return [...others, merged];
}

export default function SatellitePage() {
  const [ports, setPorts] = useState<SatellitePortData[]>([]);
  const [lastUpdated, setLastUpdated] = useState("");

  const fetchAll = useCallback(async () => {
    try {
      const data = await api.getSatellitePorts();
      setPorts(mergeYulinPorts(data.ports));
      setLastUpdated(new Date().toLocaleString());
    } catch (e) {
      console.error("Failed to fetch satellite data:", e);
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
      <div className="p-4 space-y-4 overflow-y-auto" style={{ height: "calc(100vh - 52px)" }}>
        <PortOverviewCards ports={ports} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" style={{ height: 420 }}>
          <PortVesselChart ports={ports} />
          <PortMap ports={ports} />
        </div>
      </div>
    </div>
  );
}
