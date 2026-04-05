import type { Metadata } from "next";
import "./globals.css";
import { I18nProvider } from "@/i18n/config";

export const metadata: Metadata = {
  title: "Taiwan Strait Monitor",
  description: "Real-time monitoring of Taiwan Strait military activity",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
