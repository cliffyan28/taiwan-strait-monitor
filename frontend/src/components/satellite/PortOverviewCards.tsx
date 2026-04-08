"use client";
import { useI18n } from "@/i18n/config";
import { SatellitePortData } from "@/lib/types";

interface PortOverviewCardsProps {
  ports: SatellitePortData[];
}

function sigmaToColor(sigma: number): string {
  if (sigma >= 2) return "#cf222e";
  if (sigma >= 1) return "#d97706";
  return "#1a7f37";
}

function sigmaToLevel(sigma: number, t: (key: string) => string): string {
  if (sigma >= 2) return t("satellite.anomaly_high");
  if (sigma >= 1) return t("satellite.anomaly_elevated");
  return t("satellite.anomaly_normal");
}

export default function PortOverviewCards({ ports }: PortOverviewCardsProps) {
  const { t } = useI18n();

  if (ports.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 border border-gray-300 text-center text-sm text-gray-500">
        {t("satellite.no_data")}
      </div>
    );
  }

  return (
    <div>
      <div className="text-sm font-semibold text-gray-800 mb-2">
        {t("satellite.port_overview")}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {ports.map((port) => {
          const color = sigmaToColor(port.anomaly_sigma);
          const hasMilitary = port.latest.military_estimate != null;
          return (
            <div
              key={port.port_name}
              className="bg-gray-50 rounded-lg p-4 border border-gray-300"
              style={{ borderLeftWidth: 4, borderLeftColor: color }}
            >
              <div className="text-sm font-semibold text-gray-800">
                {t(`satellite.ports.${port.port_name}`) || port.port_name}
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                {hasMilitary ? (
                  <>
                    <span className="text-2xl font-bold text-red-700">
                      {port.latest.military_estimate}
                    </span>
                    <span className="text-xs text-gray-500">
                      {t("satellite.military_estimate")}
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-bold" style={{ color }}>
                      {port.latest.vessel_count}
                    </span>
                    <span className="text-xs text-gray-500">
                      {t("satellite.vessels_detected")}
                    </span>
                  </>
                )}
              </div>
              {hasMilitary && (
                <div className="mt-1 text-xs text-gray-500">
                  SAR: {port.latest.vessel_count} &middot; AIS: {port.latest.ais_vessel_count}
                </div>
              )}
              <div className="mt-1 text-xs text-gray-500">
                {t("satellite.baseline")}: {port.baseline_avg} (&plusmn;{port.baseline_std})
              </div>
              <div className="mt-1 flex items-center gap-1">
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs font-medium" style={{ color }}>
                  {sigmaToLevel(port.anomaly_sigma, t)} ({port.anomaly_sigma.toFixed(1)}&sigma;)
                </span>
              </div>
              <div className="mt-2 text-xs text-gray-400">
                {t("satellite.last_scan")}: {port.latest.timestamp.slice(0, 16).replace("T", " ")}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
