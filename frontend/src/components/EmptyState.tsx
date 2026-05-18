import { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  variant?: "default" | "chat";
  icon?: ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({
  title,
  description,
  variant = "default",
  icon,
  action,
}: EmptyStateProps) {
  if (variant === "chat") {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
        {icon || (
          <div className="w-16 h-16 bg-amber/10 rounded-2xl flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
        )}
        <h2 className="text-2xl font-display font-bold text-cream mb-2">{title}</h2>
        <p className="text-base text-muted max-w-md">{description}</p>
      </div>
    );
  }

  return (
    <div className="text-center py-16 px-6">
      {icon || (
        <svg
          className="w-16 h-16 mx-auto text-edge mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1"
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      )}
      <h3 className="text-xl font-display font-bold text-cream mb-2">{title}</h3>
      <p className="text-muted mb-6">{description}</p>
      {action && (
        <button onClick={action.onClick} className="btn-primary">
          {action.label}
        </button>
      )}
    </div>
  );
}
