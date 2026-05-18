"use client";

import Link from "next/link";

export default function ChatError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex-1 flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-midnight-ink mb-2">Chat temporarily unavailable</h1>
        <p className="text-base text-slate-text mb-8">
          {error.message || "Something went wrong with the chat. Please try again."}
        </p>
        <div className="flex items-center justify-center gap-4">
          <button onClick={reset} className="btn-primary">
            Try Again
          </button>
          <Link href="/dashboard" className="btn-secondary">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
