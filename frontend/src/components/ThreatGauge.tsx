"use client";
import { useI18n } from "@/i18n/config";

interface ThreatGaugeProps { score: number; level: string; }

const LEVEL_COLORS: Record<string, string> = {
  normal: "#1a7f37", elevated: "#0969da", tense: "#bf5815", high_alert: "#cf4e13", crisis: "#cf222e",
};

export default function ThreatGauge({ score, level }: ThreatGaugeProps) {
  const { t } = useI18n();
  const color = LEVEL_COLORS[level] || LEVEL_COLORS.normal;
  return (
    <div className="text-center mb-5">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t("threat_level")}</div>
      <div className="w-32 h-32 rounded-full mx-auto flex flex-col items-center justify-center bg-white shadow-sm" style={{ border: `6px solid ${color}` }}>
        <div className="text-4xl font-bold" style={{ color }}>{Math.round(score)}</div>
        <div className="text-xs font-semibold" style={{ color }}>{t(`levels.${level}`)}</div>
      </div>
    </div>
  );
}
