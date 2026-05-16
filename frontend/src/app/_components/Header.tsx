import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-canvas-white border-b border-cloud-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <Link href="/" className="flex items-center space-x-2">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="28" height="28" rx="6" fill="url(#groove-logo-gradient)" />
              <path d="M8 14L12 10L16 14L20 10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 18L12 14L16 18L20 14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.6"/>
              <defs>
                <linearGradient id="groove-logo-gradient" x1="0" y1="0" x2="28" y2="28">
                  <stop offset="0%" stopColor="#19a05f" />
                  <stop offset="100%" stopColor="#0d7f8c" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-xl font-bold text-midnight-ink tracking-[-0.5px]">
              Groove
            </span>
          </Link>
          <nav className="hidden md:flex items-center space-x-6">
            <Link href="/dashboard" className="nav-link">
              Dashboard
            </Link>
            <Link href="/chat" className="nav-link">
              Chat
            </Link>
          </nav>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/chat" className="btn-primary text-sm py-2 px-4">
            Query Your Data
          </Link>
        </div>
      </div>
    </header>
  );
}