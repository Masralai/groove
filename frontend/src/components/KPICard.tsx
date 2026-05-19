interface KPICardProps {
  title: string;
  value: string;
  change?: string;
  trend?: "up" | "down";
  icon: React.ReactNode;
}

export default function KPICard({
  title,
  value,
  change,
  trend,
  icon,
}: KPICardProps) {
  return (
    <div className="card card-glow">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-xs font-medium text-muted uppercase tracking-[0.08em]">
          {title}
        </h3>
        <div className="shrink-0 text-amber">{icon}</div>
      </div>
      <p className="text-3xl font-bold text-cream font-mono tracking-[-0.02em]">{value}</p>
      {change && trend && (
        <div className="flex items-center mt-3">
          <span
            className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded ${
              trend === "up"
                ? "text-green-400 bg-green-500/10"
                : "text-coral bg-coral/10"
            }`}
          >
            <svg
              className={`w-3 h-3 mr-1 ${trend === "up" ? "" : "rotate-180"}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
            {change}
          </span>
          <span className="text-xs text-dim ml-2">vs last month</span>
        </div>
      )}
    </div>
  );
}
