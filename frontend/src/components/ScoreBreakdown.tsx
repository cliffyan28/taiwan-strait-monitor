"use client";
import { useI18n } from "@/i18n/config";
import { ThreatBreakdown } from "@/lib/types";

interface ScoreBreakdownProps { breakdown: ThreatBreakdown; }

const MAX_SCORES: Record<keyof ThreatBreakdown, number> = {
  aircraft: 25, centerline: 20, vessels: 15, pattern: 10, news_nlp: 20, multi_source: 10,
};

function getBarColor(value: number, max: number): string {
  const ratio = value / max;
  if (ratio > 0.6) return "#cf222e";
  if (ratio > 0.3) return "#bf5815";
  return "#1a7f37";
}

export default function ScoreBreakdown({ breakdown }: ScoreBreakdownProps) {
  const { t } = useI18n();
  const keys = Object.keys(MAX_SCORES) as (keyof ThreatBreakdown)[];
  return (
    <div className="bg-white rounded-lg p-4 border border-gray-300">
      <div className="text-xs text-gray-500 uppercase font-semibold mb-3">{t("score_breakdown")}</div>
      {keys.map((key) => {
        const value = breakdown[key];
        const max = MAX_SCORES[key];
        const color = getBarColor(value, max);
        return (
          <div key={key} className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-700">{t(`scores.${key}`)}</span>
              <span className="font-semibold" style={{ color }}>{value}/{max}</span>
            </div>
            <div className="h-1.5 bg-gray-200 rounded-full">
              <div className="h-full rounded-full transition-all" style={{ width: `${(value / max) * 100}%`, backgroundColor: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
