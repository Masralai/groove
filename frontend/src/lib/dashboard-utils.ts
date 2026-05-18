export interface InsightRow {
  impressions: number;
  clicks: number;
  spend: number | null;
}

export interface KPIResult {
  totalSpend: number;
  impressions: number;
  clicks: number;
  ctr: number;
}

export function computeKPIs(insights: InsightRow[]): KPIResult {
  const totalSpend = insights.reduce((s, r) => s + (r.spend || 0), 0);
  const impressions = insights.reduce((s, r) => s + (r.impressions || 0), 0);
  const clicks = insights.reduce((s, r) => s + (r.clicks || 0), 0);
  const ctr = impressions > 0 ? (clicks / impressions) * 100 : 0;
  return { totalSpend, impressions, clicks, ctr };
}

export function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

export function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function trendChange(current: number, previous: number): { change: string; trend: "up" | "down" } {
  if (previous === 0) return { change: "\u2014", trend: "up" };
  const pct = ((current - previous) / previous) * 100;
  return {
    change: `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`,
    trend: pct > 0 ? "up" : "down",
  };
}

export function statusBadgeClass(status: string): string {
  switch (status) {
    case "ACTIVE":
      return "badge-active";
    case "PAUSED":
      return "badge-paused";
    case "COMPLETED":
      return "badge-completed";
    default:
      return "badge-paused";
  }
}
