"use client";
import { useI18n } from "@/i18n/config";
import { MndReport } from "@/lib/types";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface CenterlineTrendProps { reports: MndReport[]; }

export default function CenterlineTrend({ reports }: CenterlineTrendProps) {
  const { t } = useI18n();
  const sorted = [...reports].sort((a, b) => a.date.localeCompare(b.date));
  const data = sorted.map((r) => ({
    date: r.date.slice(5),
    count: r.centerline_crossings,
    fill: r.centerline_crossings > 10 ? "#cf222e" : r.centerline_crossings > 3 ? "#bf5815" : "#1a7f37",
  }));

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-300 h-full flex flex-col">
      <div className="text-sm font-semibold text-gray-800 mb-1">{t("centerline_trend")}</div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="date" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9 }} width={30} />
            <Tooltip />
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
