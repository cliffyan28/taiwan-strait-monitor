"use client";

import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Aircraft } from "@/lib/types";
import { useI18n } from "@/i18n/config";

const CENTER: [number, number] = [24.5, 120.0];

// Taiwan MND official 3-point coordinates (GlobalSecurity.org, corrected 2004 release)
const MEDIAN_LINE: [number, number][] = [
  [26.5000, 121.3833],  // North: 26°30'N, 121°23'E
  [24.8333, 119.9833],  // Mid:   24°50'N, 119°59'E
  [23.2833, 117.8500],  // South: 23°17'N, 117°51'E
];

// Taiwan ADIZ boundary — AIP Taipei FIR ENR 1.12-1 (CAA, ROC, 7 May 2020)
const TAIWAN_ADIZ: [number, number][] = [
  [21.0, 117.5],   // SW corner
  [21.0, 121.5],   // SE corner
  [22.5, 123.0],   // E notch (angled)
  [29.0, 123.0],   // NE corner
  [29.0, 117.5],   // NW corner
  [21.0, 117.5],   // close polygon
];

function createIcon(color: string, heading: number | null) {
  const deg = heading ?? 0;
  return L.divIcon({
    className: "",
    html: `<div style="transform:rotate(${deg}deg);width:20px;height:20px;display:flex;align-items:center;justify-content:center"><span style="font-size:18px;color:${color}">✈</span></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

interface MapInnerProps {
  aircraft: Aircraft[];
}

export default function MapInner({ aircraft }: MapInnerProps) {
  const { t } = useI18n();
  return (
    <div style={{ position: "relative", height: "100%", width: "100%" }}>
      <MapContainer center={CENTER} zoom={6} style={{ height: "100%", width: "100%" }} minZoom={5}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polygon positions={TAIWAN_ADIZ} pathOptions={{ color: "#0969da", dashArray: "10 6", weight: 2, opacity: 0.4, fillOpacity: 0.05, fillColor: "#0969da" }} />
        <Polyline positions={MEDIAN_LINE} pathOptions={{ color: "#bf5815", dashArray: "8 6", weight: 2, opacity: 0.6 }} />
        {aircraft
          .filter((a) => a.latitude != null && a.longitude != null)
          .map((a) => {
            const color = a.category === "military" ? "#cf222e" : a.category === "civil" ? "#0969da" : "#656d76";
            return (
            <Marker
              key={a.icao24}
              position={[a.latitude!, a.longitude!]}
              icon={createIcon(color, a.heading)}
            >
              <Popup>
                <div className="text-xs">
                  <strong>{a.callsign || a.icao24}</strong><br />
                  Category: {a.category}<br />
                  Altitude: {a.altitude ? `${Math.round(a.altitude)}m` : "N/A"}<br />
                  Speed: {a.velocity ? `${Math.round(a.velocity)} m/s` : "N/A"}
                </div>
              </Popup>
            </Marker>
          );
          })}
      </MapContainer>

      {/* Map Legend */}
      <div style={{
        position: "absolute", bottom: 24, left: 10, zIndex: 1000,
        background: "rgba(255,255,255,0.92)", borderRadius: 6, padding: "8px 12px",
        fontSize: 11, lineHeight: 1.8, border: "1px solid #d0d7de", boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="#bf5815" strokeWidth="2" strokeDasharray="4 3" /></svg>
          <span style={{ color: "#555" }}>{t("map.median_line")} (MND 2004)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width="20" height="12"><rect x="1" y="1" width="18" height="10" fill="rgba(9,105,218,0.08)" stroke="#0969da" strokeWidth="1.5" strokeDasharray="3 2" rx="1" /></svg>
          <span style={{ color: "#555" }}>{t("map.adiz")} (AIP 2020)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: "#cf222e", fontSize: 14 }}>✈</span>
          <span style={{ color: "#555" }}>{t("map.pla")}</span>
        </div>
        <div style={{ paddingLeft: 26, color: "#999", fontSize: 9, lineHeight: 1.3, marginTop: -4 }}>{t("map.transponder_note")}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: "#0969da", fontSize: 14 }}>✈</span>
          <span style={{ color: "#555" }}>{t("map.civil")}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ color: "#656d76", fontSize: 14 }}>✈</span>
          <span style={{ color: "#555" }}>{t("map.unknown")}</span>
        </div>
      </div>
    </div>
  );
}
