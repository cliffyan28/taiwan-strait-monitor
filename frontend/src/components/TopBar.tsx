"use client";
import { useI18n } from "@/i18n/config";
import LanguageToggle from "./LanguageToggle";

interface TopBarProps { lastUpdated: string; }

export default function TopBar({ lastUpdated }: TopBarProps) {
  const { t } = useI18n();
  return (
    <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-300">
      <div className="flex items-center gap-4">
        <span className="text-base font-semibold text-gray-900">{t("site_title")}</span>
        <span className="text-gray-300">|</span>
        <span className="text-sm text-gray-500">{t("last_updated")}: {lastUpdated || "—"}</span>
      </div>
      <LanguageToggle />
    </div>
  );
}
