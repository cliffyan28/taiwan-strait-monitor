"use client";

import { useI18n } from "@/i18n/config";
import { Aircraft } from "@/lib/types";
import dynamic from "next/dynamic";

const MapInner = dynamic(() => import("./MapInner"), { ssr: false });

interface StraitMapProps {
  aircraft: Aircraft[];
  timestamp: string;
}

export default function StraitMap({ aircraft, timestamp }: StraitMapProps) {
  const { t } = useI18n();
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm text-gray-500 font-semibold">{t("live_map")}</div>
        <div className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">22°N–27°N, 117°E–123°E</div>
      </div>
      <div className="rounded-lg overflow-hidden border border-gray-300" style={{ height: 300 }}>
        <MapInner aircraft={aircraft} />
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-600">
        <span><span className="text-red-600">✈</span> {t("map.pla")}</span>
        <span><span className="text-blue-600">✈</span> {t("map.civil")}</span>
        <span><span className="text-orange-600">⚓</span> {t("map.naval")}</span>
      </div>
    </div>
  );
}
