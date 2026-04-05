"use client";
import { useI18n } from "@/i18n/config";
import { MndReport } from "@/lib/types";

interface RecentEventsProps { reports: MndReport[]; }

function getBorderColor(count: number, avg: number): string {
  if (count > avg * 1.5) return "#cf222e";
  if (count > avg * 1.2) return "#bf5815";
  return "#1a7f37";
}

export default function RecentEvents({ reports }: RecentEventsProps) {
  const { t } = useI18n();
  const avg = reports.length > 0 ? reports.reduce((s, r) => s + r.aircraft_count, 0) / reports.length : 10;
  return (
    <div>
      <div className="text-xs text-gray-500 uppercase font-semibold mb-2">{t("recent_events")}</div>
      {reports.slice(0, 5).map((report) => (
        <div key={report.date} className="bg-white rounded-md p-2.5 mb-2 border border-gray-300 text-sm" style={{ borderLeftWidth: 4, borderLeftColor: getBorderColor(report.aircraft_count, avg) }}>
          <div className="text-xs text-gray-500">{report.date}</div>
          <div className="text-gray-800 mt-1">MND: {report.aircraft_count} aircraft, {report.vessel_count} vessels</div>
        </div>
      ))}
    </div>
  );
}
