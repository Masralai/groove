interface LoadingStateProps {
  rows?: number;
  type?: "card" | "table";
}

export function CardSkeleton() {
  return (
    <div className="card animate-pulse" aria-hidden="true">
      <div className="h-3 shimmer rounded w-20 mb-4" />
      <div className="h-8 shimmer rounded w-28 mb-3" />
      <div className="h-3 shimmer rounded w-16" />
    </div>
  );
}

export function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="card overflow-hidden p-0 animate-pulse" aria-hidden="true">
      <div className="px-6 py-4 bg-surface">
        <div className="h-3 shimmer rounded w-full" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="px-6 py-4 border-t border-edge">
          <div className="h-4 shimmer rounded w-3/4 mb-2" />
          <div className="h-3 shimmer rounded w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function LoadingState({
  type = "card",
  rows = 3,
}: LoadingStateProps) {
  return (
    <div className="space-y-6" role="status" aria-label="Loading content">
      {type === "card" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: rows }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <TableSkeleton rows={rows} />
      )}
    </div>
  );
}
