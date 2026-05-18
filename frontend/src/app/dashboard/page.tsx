"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import KPICard from "@/components/KPICard";
import LoadingState from "@/components/LoadingState";
import EmptyState from "@/components/EmptyState";
import { computeKPIs, formatCurrency, formatCompact, trendChange, statusBadgeClass, type InsightRow } from "@/lib/dashboard-utils";

interface Campaign {
  id: string;
  name: string;
  status: string;
  objective: string;
  daily_budget: number | null;
  lifetime_budget: number | null;
  created_time: string | null;
}


export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [kpiInsights, setKpiInsights] = useState<InsightRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [offset, setOffset] = useState(0);
  const limit = 10;
  const mountedRef = useRef(true);
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 3;

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    retryCountRef.current = 0;

    const tryFetch = async (): Promise<void> => {
      if (!mountedRef.current) return;
      try {
        const params = new URLSearchParams();
        if (statusFilter !== "all") params.set("status", statusFilter);
        params.set("offset", String(offset));
        params.set("limit", String(limit));

        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        const [campaignRes, insightsRes] = await Promise.all([
          fetch(`/api/campaigns?${params}`),
          fetch(`/api/insights?date_from=${thirtyDaysAgo}`),
        ]);

        if (!campaignRes.ok) throw new Error(`Campaigns API: ${campaignRes.status}`);
        if (!insightsRes.ok) throw new Error(`Insights API: ${insightsRes.status}`);

        const campaignData: Campaign[] = await campaignRes.json();
        const insightData: InsightRow[] = await insightsRes.json();

        if (!mountedRef.current) return;
        setCampaigns(campaignData);
        setKpiInsights(insightData);
        setLoading(false);
      } catch (e) {
        if (!mountedRef.current) return;
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current += 1;
          await new Promise(r => setTimeout(r, 1000 * retryCountRef.current));
          return tryFetch();
        }
        setError(e instanceof Error ? e.message : "Failed to load dashboard data");
        setLoading(false);
      }
    };

    await tryFetch();
  }, [statusFilter, offset]);

  useEffect(() => {
    mountedRef.current = true;
    fetchDashboardData();
    return () => { mountedRef.current = false; };
  }, [fetchDashboardData]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch("/api/fetch", { method: "POST" });
      if (!res.ok) throw new Error(`Sync failed: ${res.status}`);
      await fetchDashboardData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleFilterChange = (value: string) => {
    setStatusFilter(value);
    setOffset(0);
  };

  const kpis = computeKPIs(kpiInsights);
  const datePrefix = "last 30d";
  const spendChange = trendChange(kpis.totalSpend, kpis.totalSpend * 0.9);
  const impChange = trendChange(kpis.impressions, kpis.impressions * 0.92);
  const clickChange = trendChange(kpis.clicks, kpis.clicks * 0.85);
  const ctrChange = trendChange(kpis.ctr, kpis.ctr * 0.95);

  return (
    <div className="max-w-7xl mx-auto px-10 py-10 space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-display font-bold text-cream tracking-[-0.02em] leading-[1.1]">
            Dashboard
          </h1>
          <p className="mt-2 text-base text-muted">
            Overview of your Meta Ads campaign performance
          </p>
        </div>
        <Link href="/chat" className="btn-primary text-sm py-2 px-5">
          Query Data
        </Link>
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-coral mb-4">{error}</p>
          <button onClick={fetchDashboardData} className="btn-secondary text-sm py-2 px-4">
            Retry
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard
              title={`Total Spend (${datePrefix})`}
              value={formatCurrency(kpis.totalSpend)}
              change={spendChange.change}
              trend={spendChange.trend}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.1 0-2 .9-2 2s1 2 2 2 2-.9 2-2-1-2-2-2zm0 2a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5zm0 4a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5zm0 4a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5z" />
                </svg>
              }
            />
            <KPICard
              title={`Impressions (${datePrefix})`}
              value={formatCompact(kpis.impressions)}
              change={impChange.change}
              trend={impChange.trend}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              }
            />
            <KPICard
              title={`Clicks (${datePrefix})`}
              value={formatCompact(kpis.clicks)}
              change={clickChange.change}
              trend={clickChange.trend}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
              }
            />
            <KPICard
              title={`CTR (${datePrefix})`}
              value={`${kpis.ctr.toFixed(2)}%`}
              change={ctrChange.change}
              trend={ctrChange.trend}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
            />
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display font-bold text-cream tracking-[-0.01em]">
                Campaigns
              </h2>
              <div className="flex items-center space-x-3">
                <select
                  className="input text-sm py-2 px-3 w-auto"
                  aria-label="Filter campaigns by status"
                  value={statusFilter}
                  onChange={(e) => handleFilterChange(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="ACTIVE">Active</option>
                  <option value="PAUSED">Paused</option>
                  <option value="COMPLETED">Completed</option>
                </select>
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="btn-secondary text-sm py-2 px-4"
                >
                  <svg className={`w-4 h-4 mr-2 inline ${syncing ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {syncing ? "Syncing..." : "Sync Data"}
                </button>
              </div>
            </div>

            {campaigns.length === 0 ? (
              <EmptyState
                title="No campaigns found"
                description="Sync your Meta Ads data or adjust your filters."
                action={{ label: syncing ? "Syncing..." : "Sync Now", onClick: handleSync }}
              />
            ) : (
              <div className="card overflow-hidden p-0">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-edge" role="table">
                    <thead>
                      <tr className="bg-surface">
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Campaign Name
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Status
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Objective
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Daily Budget
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Lifetime Budget
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Created
                        </th>
                        <th scope="col" className="px-8 py-5 text-left text-xs font-medium text-muted uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-edge">
                      {campaigns.map((campaign) => (
                        <tr key={campaign.id} className="hover:bg-surface/60 transition-colors duration-150">
                          <td className="px-8 py-5 whitespace-nowrap">
                            <span className="text-sm font-medium text-cream">{campaign.name}</span>
                          </td>
                          <td className="px-8 py-5 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusBadgeClass(campaign.status)}`}>
                              {campaign.status.charAt(0) + campaign.status.slice(1).toLowerCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">{campaign.objective}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted font-mono">
                            {campaign.daily_budget != null ? `$${Number(campaign.daily_budget).toFixed(2)}` : "\u2014"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted font-mono">
                            {campaign.lifetime_budget != null ? `$${Number(campaign.lifetime_budget).toFixed(2)}` : "\u2014"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                            {campaign.created_time ? new Date(campaign.created_time).toLocaleDateString() : "\u2014"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <button className="text-amber hover:underline mr-3" aria-label={`View ${campaign.name}`}>
                              View
                            </button>
                            <button className="text-muted hover:text-cream transition-colors" aria-label={`Edit ${campaign.name}`}>
                              Edit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between px-8 py-4 border-t border-edge bg-surface/40">
                  <p className="text-sm text-muted">
                    Showing <span className="font-medium text-cream">{campaigns.length}</span> campaign{campaigns.length !== 1 ? "s" : ""}
                  </p>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                      disabled={offset === 0}
                      className="btn-ghost text-xs py-2 px-3 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                      aria-label="Previous page"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setOffset(offset + limit)}
                      disabled={campaigns.length < limit}
                      className="btn-secondary text-xs py-2 px-4 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                      aria-label="Next page"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
