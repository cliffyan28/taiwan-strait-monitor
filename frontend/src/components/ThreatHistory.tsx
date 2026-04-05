"use client";
import { useI18n } from "@/i18n/config";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceArea, ReferenceLine } from "recharts";

interface ThreatHistoryProps {
  history: { timestamp: string; total_score: number; level: string }[];
}

export default function ThreatHistory({ history }: ThreatHistoryProps) {
  const { t } = useI18n();
  const data = history.map((h) => ({ date: h.timestamp.slice(5, 10), score: h.total_score }));
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-300">
      <div className="text-sm font-semibold text-gray-800 mb-1">{t("threat_history")}</div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <ReferenceArea y1={80} y2={100} fill="#cf222e" fillOpacity={0.06} />
            <ReferenceArea y1={60} y2={80} fill="#bf5815" fillOpacity={0.04} />
            <ReferenceArea y1={40} y2={60} fill="#d29922" fillOpacity={0.04} />
            <ReferenceArea y1={20} y2={40} fill="#0969da" fillOpacity={0.03} />
            <XAxis dataKey="date" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} width={30} />
            <Tooltip />
            <ReferenceLine y={20} stroke="#1a7f37" strokeDasharray="3 3" strokeOpacity={0.3} />
            <ReferenceLine y={40} stroke="#0969da" strokeDasharray="3 3" strokeOpacity={0.3} />
            <ReferenceLine y={60} stroke="#d29922" strokeDasharray="3 3" strokeOpacity={0.3} />
            <ReferenceLine y={80} stroke="#cf222e" strokeDasharray="3 3" strokeOpacity={0.3} />
            <Area type="monotone" dataKey="score" stroke="#bf5815" fill="#bf5815" fillOpacity={0.15} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
