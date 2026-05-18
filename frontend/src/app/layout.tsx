import type { Metadata } from "next";
import { Bricolage_Grotesque, Sora, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Header from "./_components/Header";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["600", "700", "800"],
});

const body = Sora({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["300", "400", "500", "600"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Groove - Meta Ads Data Pipeline",
  description: "Natural language chatbot for querying Meta Ads data",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable} h-full`}>
      <body className="min-h-full flex flex-col font-body">
        <Header />
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
