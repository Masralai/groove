import { describe, it, expect } from "vitest";
import {
  computeKPIs,
  formatCurrency,
  formatCompact,
  trendChange,
  statusBadgeClass,
  type InsightRow,
} from "@/lib/dashboard-utils";

describe("computeKPIs", () => {
  it("aggregates spend, impressions, clicks and ctr", () => {
    const rows: InsightRow[] = [
      { spend: 100, impressions: 1000, clicks: 50 },
      { spend: 200, impressions: 2000, clicks: 100 },
    ];
    const result = computeKPIs(rows);
    expect(result.totalSpend).toBe(300);
    expect(result.impressions).toBe(3000);
    expect(result.clicks).toBe(150);
    expect(result.ctr).toBe(5);
  });

  it("handles empty array", () => {
    const result = computeKPIs([]);
    expect(result.totalSpend).toBe(0);
    expect(result.ctr).toBe(0);
  });
});

describe("formatCurrency", () => {
  it("formats millions", () => {
    expect(formatCurrency(1_500_000)).toBe("$1.5M");
  });

  it("formats thousands", () => {
    expect(formatCurrency(2_300)).toBe("$2.3K");
  });

  it("formats small numbers", () => {
    expect(formatCurrency(49.99)).toBe("$49.99");
  });
});

describe("formatCompact", () => {
  it("formats millions", () => {
    expect(formatCompact(2_100_000)).toBe("2.1M");
  });

  it("formats thousands", () => {
    expect(formatCompact(5_500)).toBe("5.5K");
  });

  it("formats small numbers with locale", () => {
    expect(formatCompact(999)).toBe("999");
  });
});

describe("trendChange", () => {
  it("returns up trend for positive change", () => {
    expect(trendChange(120, 100)).toEqual({ change: "+20.0%", trend: "up" });
  });

  it("returns down trend for negative change", () => {
    expect(trendChange(80, 100)).toEqual({ change: "-20.0%", trend: "down" });
  });

  it("handles zero previous", () => {
    expect(trendChange(100, 0)).toEqual({ change: "\u2014", trend: "up" });
  });
});

describe("statusBadgeClass", () => {
  it("returns active class for ACTIVE", () => {
    expect(statusBadgeClass("ACTIVE")).toBe("badge-status-active");
  });

  it("returns paused class for PAUSED", () => {
    expect(statusBadgeClass("PAUSED")).toBe("badge-status-paused");
  });

  it("returns completed class for COMPLETED", () => {
    expect(statusBadgeClass("COMPLETED")).toBe("badge-status-completed");
  });

  it("defaults to paused for unknown status", () => {
    expect(statusBadgeClass("UNKNOWN")).toBe("badge-status-paused");
  });
});
