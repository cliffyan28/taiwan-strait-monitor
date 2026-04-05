"use client";
import { useI18n } from "@/i18n/config";
import { MndReport } from "@/lib/types";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from "recharts";

interface AircraftTrendProps { reports: MndReport[]; }

export default function AircraftTrend({ reports }: AircraftTrendProps) {
  const { t } = useI18n();
  const sorted = [...reports].sort((a, b) => a.date.localeCompare(b.date));
  const avg = sorted.length > 0 ? sorted.reduce((s, r) => s + r.aircraft_count, 0) / sorted.length : 0;
  const data = sorted.map((r) => ({
    date: r.date.slice(5),
    count: r.aircraft_count,
    fill: r.aircraft_count > avg * 2 ? "#cf222e" : r.aircraft_count > avg * 1.5 ? "#bf5815" : "#1a7f37",
  }));

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-300">
      <div className="text-sm font-semibold text-gray-800 mb-1">{t("aircraft_trend")}</div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="date" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9 }} width={30} />
            <Tooltip />
            <ReferenceLine y={avg} stroke="#656d76" strokeDasharray="4 4" />
            <Bar dataKey="count" radius={[2, 2, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
