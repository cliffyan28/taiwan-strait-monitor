"use client";
import { useI18n } from "@/i18n/config";
import { SatellitePortData } from "@/lib/types";
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

interface PortVesselChartProps {
  ports: SatellitePortData[];
}

function PortMiniChart({
  port,
  label,
}: {
  port: SatellitePortData;
  label: string;
}) {
  const avg = port.baseline_avg;
  const std = port.baseline_std;
  const sigma1 = avg + std;
  const sigma2 = avg + std * 2;

  const allPoints = [
    ...port.history.map((h) => ({
      sortKey: h.timestamp.slice(0, 10),
      date: h.timestamp.slice(2, 10),
      count: h.vessel_count,
    })),
    {
      sortKey: port.latest.timestamp.slice(0, 10),
      date: port.latest.timestamp.slice(2, 10),
      count: port.latest.vessel_count,
    },
  ].sort((a, b) => a.sortKey.localeCompare(b.sortKey));

  const latest = port.latest.vessel_count;
  const hasMilitary = port.latest.military_estimate != null;

  // Determine the latest point's sigma level for the header color
  const latestSigma = std > 0 ? (latest - avg) / std : 0;
  const headerColor = latestSigma >= 2 ? "#cf222e" : latestSigma >= 1 ? "#d97706" : "#1a7f37";

  // Y domain: ensure we show at least up to sigma2 for context
  const maxCount = Math.max(...allPoints.map((p) => p.count), sigma2);
  const yMax = Math.ceil(maxCount * 1.15);
  const yMin = 0;

  // Build background zone data (green/orange/red bands)
  const zoneData = allPoints.map((p) => ({
    ...p,
    greenZone: Math.min(sigma1, yMax),
    orangeZone: std > 0 ? Math.min(sigma2, yMax) - sigma1 : 0,
    redZone: std > 0 ? Math.max(0, yMax - sigma2) : 0,
  }));

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 flex flex-col">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-gray-700 truncate">{label}</span>
        <span className="text-sm font-bold" style={{ color: headerColor }}>
          {hasMilitary ? port.latest.military_estimate : latest}
        </span>
      </div>
      <div style={{ width: "100%", height: 60 }}>
        {allPoints.length > 1 ? (
          <ResponsiveContainer width="100%" height={60}>
            <ComposedChart data={zoneData} margin={{ top: 0, right: 2, bottom: 0, left: 2 }}>
              <XAxis dataKey="date" hide />
              <YAxis hide domain={[yMin, yMax]} />
              {/* Background color bands */}
              <Area
                type="step"
                dataKey="greenZone"
                stackId="zone"
                fill="rgba(26,127,55,0.10)"
                stroke="none"
                isAnimationActive={false}
              />
              {std > 0 && (
                <Area
                  type="step"
                  dataKey="orangeZone"
                  stackId="zone"
                  fill="rgba(217,119,6,0.10)"
                  stroke="none"
                  isAnimationActive={false}
                />
              )}
              {std > 0 && (
                <Area
                  type="step"
                  dataKey="redZone"
                  stackId="zone"
                  fill="rgba(207,34,46,0.10)"
                  stroke="none"
                  isAnimationActive={false}
                />
              )}
              {/* Baseline reference */}
              <ReferenceLine
                y={avg}
                stroke="#9ca3af"
                strokeDasharray="3 3"
                strokeWidth={1}
              />
              {/* Data line */}
              <Tooltip
                contentStyle={{ fontSize: 11, padding: "4px 8px" }}
                formatter={(value, name) =>
                  name === "count" ? [String(value), "vessels"] : null
                }
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#374151"
                strokeWidth={2}
                dot={{ r: 2.5, fill: "#374151", stroke: "#fff", strokeWidth: 1 }}
                activeDot={{ r: 4 }}
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-xs">
            {latest}
          </div>
        )}
      </div>
      <div className="flex items-center justify-between mt-1">
        <span className="text-[10px] text-gray-400">
          avg {port.baseline_avg}
        </span>
        <span className="text-[10px] text-gray-400">
          &plusmn;{port.baseline_std}
        </span>
      </div>
    </div>
  );
}

export default function PortVesselChart({ ports }: PortVesselChartProps) {
  const { t } = useI18n();

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-300">
      <div className="text-sm font-semibold text-gray-800 mb-3">
        {t("satellite.vessel_history")}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {ports.map((port) => (
          <PortMiniChart
            key={port.port_name}
            port={port}
            label={t(`satellite.ports.${port.port_name}`) || port.port_name}
          />
        ))}
      </div>
    </div>
  );
}
