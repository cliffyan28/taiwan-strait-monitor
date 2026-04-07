"use client";
import { useI18n } from "@/i18n/config";
import { SatellitePortData } from "@/lib/types";
import dynamic from "next/dynamic";

const PortMapInner = dynamic(() => import("./PortMapInner"), { ssr: false });

interface PortMapProps {
  ports: SatellitePortData[];
}

export default function PortMap({ ports }: PortMapProps) {
  const { t } = useI18n();
  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm font-semibold text-gray-800">
          {t("satellite.port_map")}
        </div>
        <div className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
          SAR Sentinel-1
        </div>
      </div>
      <div className="rounded-lg overflow-hidden border border-gray-300 flex-1 min-h-0">
        <PortMapInner ports={ports} />
      </div>
    </div>
  );
}
