"use client";
import { useI18n } from "@/i18n/config";

export default function LanguageToggle() {
  const { locale, setLocale } = useI18n();
  return (
    <div className="flex gap-2">
      <button onClick={() => setLocale("en")} className={`px-3 py-1 rounded text-xs font-medium ${locale === "en" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"}`}>EN</button>
      <button onClick={() => setLocale("zh-CN")} className={`px-3 py-1 rounded text-xs font-medium ${locale === "zh-CN" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"}`}>中文</button>
    </div>
  );
}
