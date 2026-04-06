"use client";
import { useI18n } from "@/i18n/config";

interface ThreatGaugeProps {
  score: number;
  level: string;
}

function scoreToColor(score: number): string {
  if (score <= 25) return "#1a7f37";
  if (score <= 50) return "#e3b341";
  if (score <= 75) return "#d97706";
  return "#cf222e";
}

const ZONES = [
  { start: 0, end: 25, color: "#1a7f37" },   // Green
  { start: 25, end: 50, color: "#e3b341" },   // Yellow
  { start: 50, end: 75, color: "#d97706" },   // Orange
  { start: 75, end: 100, color: "#cf222e" },   // Red
];

const CX = 130;
const CY = 115;
const RADIUS = 90;
const ARC_WIDTH = 14;

function scoreToAngle(score: number): number {
  return Math.PI - (Math.max(0, Math.min(100, score)) / 100) * Math.PI;
}

function polarToXY(angle: number, r: number): { x: number; y: number } {
  return { x: CX + r * Math.cos(angle), y: CY - r * Math.sin(angle) };
}

function arcPath(startScore: number, endScore: number, r: number): string {
  const a1 = scoreToAngle(startScore);
  const a2 = scoreToAngle(endScore);
  const p1 = polarToXY(a1, r);
  const p2 = polarToXY(a2, r);
  return `M ${p1.x} ${p1.y} A ${r} ${r} 0 0 1 ${p2.x} ${p2.y}`;
}

export default function ThreatGauge({ score, level }: ThreatGaugeProps) {
  const { t } = useI18n();
  const clamped = Math.max(0, Math.min(100, score));
  const color = scoreToColor(clamped);
  const needleAngle = scoreToAngle(clamped);
  const needleTip = polarToXY(needleAngle, RADIUS - ARC_WIDTH / 2 - 4);
  const needleEnd = polarToXY(needleAngle + Math.PI, 18);

  return (
    <div className="text-center mb-5">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
        {t("threat_level")}
      </div>

      <div className="mx-auto bg-white rounded-xl shadow-sm" style={{ width: 260, padding: "16px 0 12px 0" }}>
        <svg viewBox="0 0 260 130" width="260" height="130">
          {/* Background track */}
          <path d={arcPath(0, 100, RADIUS)} fill="none" stroke="#eee" strokeWidth={ARC_WIDTH} strokeLinecap="round" />

          {/* Zone arcs with small gaps */}
          {ZONES.map((zone) => (
            <path
              key={zone.start}
              d={arcPath(zone.start + 0.5, zone.end - 0.5, RADIUS)}
              fill="none"
              stroke={zone.color}
              strokeWidth={ARC_WIDTH}
              strokeLinecap="round"
              opacity={0.85}
            />
          ))}

          {/* Tick labels — positioned outside the arc */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = scoreToAngle(tick);
            const pt = polarToXY(angle, RADIUS + ARC_WIDTH / 2 + 10);
            return (
              <text
                key={tick}
                x={pt.x}
                y={pt.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="9"
                fill="#aaa"
                fontFamily="system-ui, sans-serif"
              >
                {tick}
              </text>
            );
          })}

          {/* Needle — thin line style */}
          <line
            x1={needleEnd.x}
            y1={needleEnd.y}
            x2={needleTip.x}
            y2={needleTip.y}
            stroke={color}
            strokeWidth={2.5}
            strokeLinecap="round"
          />

          {/* Center dot */}
          <circle cx={CX} cy={CY} r={5} fill={color} />
          <circle cx={CX} cy={CY} r={2.5} fill="white" />
        </svg>

        {/* Score and level */}
        <div style={{ marginTop: -8 }}>
          <div className="font-bold" style={{ fontSize: 32, lineHeight: 1, color }}>
            {Math.round(clamped)}
          </div>
          <div className="font-semibold uppercase tracking-wide" style={{ fontSize: 11, color, marginTop: 2 }}>
            {t(`levels.${level}`)}
          </div>
        </div>
      </div>
    </div>
  );
}
