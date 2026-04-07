"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/i18n/config";
import LanguageToggle from "./LanguageToggle";

interface TopBarProps { lastUpdated: string; }

export default function TopBar({ lastUpdated }: TopBarProps) {
  const { t } = useI18n();
  const pathname = usePathname();

  return (
    <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-300">
      <div className="flex items-center gap-4">
        <span className="text-base font-semibold text-gray-900">{t("site_title")}</span>
        <span className="text-gray-300">|</span>
        <nav className="flex gap-1">
          <Link
            href="/"
            className={`px-3 py-1 rounded text-xs font-medium ${
              pathname === "/" ? "bg-gray-200 text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t("nav.dashboard")}
          </Link>
          <Link
            href="/satellite"
            className={`px-3 py-1 rounded text-xs font-medium ${
              pathname === "/satellite" ? "bg-gray-200 text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t("nav.satellite")}
          </Link>
        </nav>
        <span className="text-gray-300">|</span>
        <span className="text-sm text-gray-500">{t("last_updated")}: {lastUpdated || "—"}</span>
      </div>
      <LanguageToggle />
    </div>
  );
}
