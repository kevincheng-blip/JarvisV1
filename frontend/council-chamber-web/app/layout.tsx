import type { Metadata } from "next";
import "../styles/globals.css";
import { ThemeScript } from "@/components/common/ThemeScript";

export const metadata: Metadata = {
  title: "J-GOD AI Council Chamber v6 PRO",
  description: "Professional Multi-AI AI Council Chamber Console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <head>
        <ThemeScript />
      </head>
      <body>{children}</body>
    </html>
  );
}

