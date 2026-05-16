import Link from "next/link";
import KPICard from "@/components/KPICard";

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-midnight-ink tracking-[-1px] leading-[1.1]">
            Dashboard
          </h1>
          <p className="mt-2 text-base text-slate-text">
            Overview of your Meta Ads campaign performance
          </p>
        </div>
        <Link href="/chat" className="btn-primary text-sm py-2 px-4">
          Query Data
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Spend"
          value="$12,450"
          change="12.5%"
          trend="up"
          iconColor="text-plasma-teal-gradient"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.1 0-2 .9-2 2s1 2 2 2 2-.9 2-2-1-2-2-2zm0 2a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5zm0 4a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5zm0 4a.5.5 0 01.5-.5h1a.5.5 0 010 1h-1a.5.5 0 01-.5-.5z" />
            </svg>
          }
        />
        <KPICard
          title="Impressions"
          value="1.2M"
          change="8.3%"
          trend="up"
          iconColor="text-system-sky"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          }
        />
        <KPICard
          title="Clicks"
          value="45.2K"
          change="15.2%"
          trend="up"
          iconColor="text-midnight-ink"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
          }
        />
        <KPICard
          title="CTR"
          value="3.8%"
          change="2.1%"
          trend="up"
          iconColor="text-system-mint"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-midnight-ink tracking-[-0.5px]">
            Campaigns
          </h2>
          <div className="flex items-center space-x-3">
            <select
              className="input text-sm py-2 px-3 w-auto"
              aria-label="Filter campaigns by status"
              defaultValue="all"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
            </select>
            <button className="btn-secondary text-sm py-2 px-4">
              <svg className="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Sync Data
            </button>
          </div>
        </div>

        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-cloud-border" role="table">
              <thead>
                <tr className="bg-cloud-gray">
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Campaign Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Objective
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Daily Budget
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Lifetime Budget
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-text uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cloud-border">
                {[
                  { name: "Summer Sale Campaign", status: "active" as const, objective: "Conversions", daily: "$50.00", lifetime: "$1,500.00", created: "2024-05-01" },
                  { name: "Brand Awareness Campaign", status: "paused" as const, objective: "Brand Awareness", daily: "$75.00", lifetime: "$2,250.00", created: "2024-04-15" },
                  { name: "Retargeting Campaign", status: "active" as const, objective: "Traffic", daily: "$100.00", lifetime: "$3,500.00", created: "2024-03-20" },
                  { name: "Holiday Promotions", status: "completed" as const, objective: "Sales", daily: "$200.00", lifetime: "$8,000.00", created: "2023-12-01" },
                ].map((campaign) => (
                  <tr key={campaign.name} className="hover:bg-cloud-gray/30 transition-colors duration-150">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-midnight-ink">{campaign.name}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          campaign.status === "active"
                            ? "badge-status-active"
                            : campaign.status === "paused"
                            ? "badge-status-paused"
                            : "badge-status-completed"
                        }`}
                      >
                        {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-text">{campaign.objective}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-text tabular-nums">{campaign.daily}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-text tabular-nums">{campaign.lifetime}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-text">{campaign.created}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button className="text-plasma-teal-gradient hover:underline mr-3" aria-label={`View ${campaign.name}`}>
                        View
                      </button>
                      <button className="text-midnight-ink hover:underline" aria-label={`Edit ${campaign.name}`}>
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between px-6 py-3 border-t border-cloud-border bg-cloud-gray/30">
            <p className="text-sm text-slate-text">
              Showing <span className="font-medium text-midnight-ink">4</span> of{" "}
              <span className="font-medium text-midnight-ink">12</span> campaigns
            </p>
            <div className="flex items-center space-x-2">
              <button className="btn-ghost text-xs py-1 px-2 opacity-50 cursor-not-allowed" disabled aria-label="Previous page">
                Previous
              </button>
              <button className="btn-secondary text-xs py-1 px-3" aria-label="Next page">
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}