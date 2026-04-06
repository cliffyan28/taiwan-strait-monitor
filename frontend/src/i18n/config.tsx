"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import en from "./en.json";
import zhCN from "./zh-CN.json";

type Locale = "en" | "zh-CN";
const messages: Record<Locale, Record<string, unknown>> = { en, "zh-CN": zhCN };

interface I18nContextType {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

function getNestedValue(obj: unknown, path: string): string {
  const result = path.split(".").reduce((o: unknown, k: string) => {
    if (o !== null && typeof o === "object") {
      return (o as Record<string, unknown>)[k];
    }
    return undefined;
  }, obj);
  return typeof result === "string" ? result : path;
}

export const I18nContext = createContext<I18nContextType>({
  locale: "en",
  setLocale: () => {},
  t: (k) => k,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const saved = localStorage.getItem("locale") as Locale;
    if (saved && saved !== locale) setLocaleState(saved);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") localStorage.setItem("locale", l);
  }, []);

  const t = useCallback(
    (key: string) => getNestedValue(messages[locale], key),
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
