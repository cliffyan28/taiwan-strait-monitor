"use client";
import { useI18n } from "@/i18n/config";
import { NewsEvent } from "@/lib/types";

interface NewsFeedProps { events: NewsEvent[]; }

const LEVEL_STYLES: Record<string, { border: string; bg: string; text: string }> = {
  high: { border: "#cf222e", bg: "#FFEBE9", text: "#cf222e" },
  medium: { border: "#bf5815", bg: "#FFF1E5", text: "#bf5815" },
  low: { border: "#1a7f37", bg: "#DAFBE1", text: "#1a7f37" },
};

function timeAgo(timestamp: string, t: (key: string) => string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return t("time_ago_minutes");
  if (hours < 24) return t("time_ago_hours").replace("{hours}", String(hours));
  return t("time_ago_days").replace("{days}", String(Math.floor(hours / 24)));
}

export default function NewsFeed({ events }: NewsFeedProps) {
  const { t, locale } = useI18n();
  const style = (level: string) => LEVEL_STYLES[level] || LEVEL_STYLES.low;
  const displayTitle = (event: NewsEvent) =>
    locale === "zh-CN" && event.title_zh ? event.title_zh : event.title;
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-300 h-full">
      <div className="mb-3">
        <div className="text-sm font-semibold text-gray-800">{t("latest_intel")}</div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {events.slice(0, 6).map((event, i) => {
          const s = style(event.keyword_level);
          return (
            <a key={i} href={event.url} target="_blank" rel="noopener noreferrer"
              className="bg-white rounded-md p-3 border border-gray-300 hover:shadow-sm transition-shadow"
              style={{ borderLeftWidth: 4, borderLeftColor: s.border }}>
              <div className="text-xs text-gray-500">{event.source} · {timeAgo(event.timestamp, t)}</div>
              <div className="text-sm text-gray-800 mt-1 line-clamp-2">{displayTitle(event)}</div>
              <div className="mt-2">
                {event.matched_keywords.slice(0, 2).map((kw) => (
                  <span key={kw} className="inline-block text-xs px-2 py-0.5 rounded mr-1"
                    style={{ backgroundColor: s.bg, color: s.text }}>{kw}</span>
                ))}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
