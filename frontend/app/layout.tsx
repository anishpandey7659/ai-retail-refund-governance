import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { AppProvider } from "@/context/app-context";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Marlow & Co. | Retail Refund Governance",
  description: "Minimalist retail refund dashboard for order and refund management.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[#F8F7F4] text-[#252525]">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
