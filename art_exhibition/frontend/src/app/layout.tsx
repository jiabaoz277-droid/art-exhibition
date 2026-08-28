import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "高校艺术赛事投稿助手",
  description: "面向高校画展 / 毕业展 / 艺术赛事的一站式征集平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={geistSans.variable}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
