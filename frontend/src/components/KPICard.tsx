interface KPICardProps {
  title: string;
  value: string;
  change: string;
  trend: "up" | "down";
  icon: React.ReactNode;
  iconColor: string;
}

export default function KPICard({
  title,
  value,
  change,
  trend,
  icon,
  iconColor,
}: KPICardProps) {
  return (
    <div className="card hover-lift">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-slate-text uppercase tracking-wider">
          {title}
        </h3>
        <div className={`shrink-0 ${iconColor}`}>{icon}</div>
      </div>
      <p className="text-3xl font-bold text-midnight-ink tabular-nums">{value}</p>
      <div className="flex items-center mt-2">
        <span
          className={`text-sm font-medium px-2 py-0.5 rounded ${
            trend === "up"
              ? "text-green-600 bg-green-500/10"
              : "text-red-600 bg-red-500/10"
          }`}
        >
          {trend === "up" ? "↑" : "↓"} {change}
        </span>
        <span className="text-xs text-slate-text ml-2">vs last month</span>
      </div>
    </div>
  );
}