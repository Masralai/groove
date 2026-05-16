import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard - Groove",
  description: "Meta Ads campaign performance overview with KPI metrics and campaign management.",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}