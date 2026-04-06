"use client";
import { useState } from "react";
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
  const [showMethodology, setShowMethodology] = useState(false);
  const keys = Object.keys(MAX_SCORES) as (keyof ThreatBreakdown)[];
  return (
    <div className="bg-white rounded-lg p-4 border border-gray-300">
      <div className="flex justify-between items-center mb-3">
        <div className="text-xs text-gray-500 uppercase font-semibold">{t("score_breakdown")}</div>
        <button
          onClick={() => setShowMethodology(true)}
          className="text-xs text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
        >
          {t("methodology")}
        </button>
      </div>
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

      {showMethodology && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]" onClick={() => setShowMethodology(false)}>
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center rounded-t-xl">
              <h2 className="text-lg font-bold text-gray-800">{t("methodology")}</h2>
              <button onClick={() => setShowMethodology(false)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>
            <div className="px-6 py-4 text-sm text-gray-700 space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 mb-1">{t("methodology_overview_title")}</h3>
                <p>{t("methodology_overview")}</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">{t("methodology_military_title")}</h3>
                <table className="w-full text-xs border-collapse">
                  <thead><tr className="border-b border-gray-200">
                    <th className="text-left py-1.5 text-gray-500">{t("methodology_indicator")}</th>
                    <th className="text-right py-1.5 text-gray-500">{t("methodology_max")}</th>
                    <th className="text-left py-1.5 pl-3 text-gray-500">{t("methodology_method")}</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-gray-100"><td className="py-1.5">{t("scores.aircraft")}</td><td className="text-right">25</td><td className="pl-3">{t("methodology_aircraft")}</td></tr>
                    <tr className="border-b border-gray-100"><td className="py-1.5">{t("scores.centerline")}</td><td className="text-right">20</td><td className="pl-3">{t("methodology_centerline")}</td></tr>
                    <tr className="border-b border-gray-100"><td className="py-1.5">{t("scores.vessels")}</td><td className="text-right">15</td><td className="pl-3">{t("methodology_vessels")}</td></tr>
                    <tr><td className="py-1.5">{t("scores.pattern")}</td><td className="text-right">10</td><td className="pl-3">{t("methodology_pattern")}</td></tr>
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">{t("methodology_nlp_title")}</h3>
                <table className="w-full text-xs border-collapse">
                  <thead><tr className="border-b border-gray-200">
                    <th className="text-left py-1.5 text-gray-500">{t("methodology_indicator")}</th>
                    <th className="text-right py-1.5 text-gray-500">{t("methodology_max")}</th>
                    <th className="text-left py-1.5 pl-3 text-gray-500">{t("methodology_method")}</th>
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-gray-100"><td className="py-1.5">{t("scores.news_nlp")}</td><td className="text-right">20</td><td className="pl-3">{t("methodology_news")}</td></tr>
                    <tr><td className="py-1.5">{t("scores.multi_source")}</td><td className="text-right">10</td><td className="pl-3">{t("methodology_multi")}</td></tr>
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-1">{t("methodology_levels_title")}</h3>
                <div className="flex gap-2 flex-wrap text-xs">
                  <span className="px-2 py-1 rounded" style={{ background: "#DAFBE1", color: "#1a7f37" }}>0–25 {t("levels.normal")}</span>
                  <span className="px-2 py-1 rounded" style={{ background: "#FFF8C5", color: "#9a6700" }}>25–50 {t("levels.elevated")}</span>
                  <span className="px-2 py-1 rounded" style={{ background: "#FFF1E5", color: "#d97706" }}>50–75 {t("levels.tense")}</span>
                  <span className="px-2 py-1 rounded" style={{ background: "#FFEBE9", color: "#cf222e" }}>75–100 {t("levels.crisis")}</span>
                </div>
              </div>
              <div className="text-xs text-gray-400 border-t border-gray-100 pt-3">
                {t("methodology_source")}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
