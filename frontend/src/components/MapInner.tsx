"use client";

import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Aircraft } from "@/lib/types";

const CENTER: [number, number] = [24.5, 120.0];

const MEDIAN_LINE: [number, number][] = [
  [27.0, 120.5],
  [24.5, 119.5],
  [22.0, 118.5],
];

function createIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<span style="color:${color};font-size:18px">✈</span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

const ICONS = {
  military: createIcon("#cf222e"),
  civil: createIcon("#0969da"),
  unknown: createIcon("#656d76"),
};

interface MapInnerProps {
  aircraft: Aircraft[];
}

export default function MapInner({ aircraft }: MapInnerProps) {
  return (
    <MapContainer center={CENTER} zoom={6} style={{ height: "100%", width: "100%" }} minZoom={5}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Polyline positions={MEDIAN_LINE} pathOptions={{ color: "#bf5815", dashArray: "8 6", weight: 2, opacity: 0.6 }} />
      {aircraft
        .filter((a) => a.latitude != null && a.longitude != null)
        .map((a) => (
          <Marker
            key={a.icao24}
            position={[a.latitude!, a.longitude!]}
            icon={ICONS[a.category as keyof typeof ICONS] || ICONS.unknown}
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
        ))}
    </MapContainer>
  );
}
