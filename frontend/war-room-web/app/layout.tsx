import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "J-GOD War Room v6",
  description: "Multi-AI War Room Console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}

