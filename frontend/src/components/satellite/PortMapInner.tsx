"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { SatellitePortData } from "@/lib/types";
import { useI18n } from "@/i18n/config";

const PORT_COORDS: Record<string, [number, number]> = {
  ningbo:          [29.90, 121.96],
  xiangshan:       [29.52, 121.68],
  zhoushan:        [30.02, 122.10],
  shanghai_wusong: [31.39, 121.50],
  shanghai_yangpu: [31.27, 121.53],
  sandu_ao:        [26.66, 119.63],
  xiamen:          [24.45, 118.07],
  shantou:         [23.35, 116.73],
  zhanjiang:       [21.22, 110.44],
  yulin_west:      [18.22, 109.50],
  yulin_east:      [18.21, 109.69],
  yulin:           [18.22, 109.60],
};

const CENTER: [number, number] = [24.0, 116.0];

function sigmaToColor(sigma: number): string {
  if (sigma >= 2) return "#cf222e";
  if (sigma >= 1) return "#d97706";
  return "#1a7f37";
}

interface PortMapInnerProps {
  ports: SatellitePortData[];
}

export default function PortMapInner({ ports }: PortMapInnerProps) {
  const { t } = useI18n();

  return (
    <div style={{ position: "relative", height: "100%", width: "100%" }}>
      <MapContainer center={CENTER} zoom={5} style={{ height: "100%", width: "100%" }} minZoom={4}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {ports.map((port) => {
          const coords = PORT_COORDS[port.port_name];
          if (!coords) return null;
          const color = sigmaToColor(port.anomaly_sigma);
          const radius = Math.max(8, Math.min(25, port.latest.vessel_count / 2));
          return (
            <CircleMarker
              key={port.port_name}
              center={coords}
              radius={radius}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.4, weight: 2 }}
            >
              <Popup>
                <div style={{ fontSize: 12 }}>
                  <strong>{t(`satellite.ports.${port.port_name}`) || port.port_name}</strong><br />
                  {t("satellite.vessels_detected")}: {port.latest.vessel_count}<br />
                  {port.latest.ais_vessel_count != null && (
                    <>{t("satellite.ais_vessels")}: {port.latest.ais_vessel_count}<br /></>
                  )}
                  {port.latest.military_estimate != null && (
                    <><strong style={{ color: "#cf222e" }}>{t("satellite.military_estimate")}: {port.latest.military_estimate}</strong><br /></>
                  )}
                  {t("satellite.baseline")}: {port.baseline_avg}<br />
                  {t("satellite.anomaly_sigma_label")}: {port.anomaly_sigma.toFixed(1)}&sigma;<br />
                  {t("satellite.last_scan")}: {port.latest.timestamp.slice(0, 16).replace("T", " ")}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Legend */}
      <div style={{
        position: "absolute", bottom: 24, left: 10, zIndex: 1000,
        background: "rgba(255,255,255,0.92)", borderRadius: 6, padding: "8px 12px",
        fontSize: 11, lineHeight: 1.8, border: "1px solid #d0d7de",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", backgroundColor: "#1a7f37" }} />
          <span style={{ color: "#555" }}>{t("satellite.anomaly_normal")} (&lt;1&sigma;)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", backgroundColor: "#d97706" }} />
          <span style={{ color: "#555" }}>{t("satellite.anomaly_elevated")} (1-2&sigma;)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", backgroundColor: "#cf222e" }} />
          <span style={{ color: "#555" }}>{t("satellite.anomaly_high")} (&gt;2&sigma;)</span>
        </div>
      </div>
    </div>
  );
}
