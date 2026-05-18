"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isMenuOpen]);

  return (
    <header className="sticky top-0 z-50 bg-deep/80 backdrop-blur-lg border-b border-edge">
      <div className="max-w-7xl mx-auto px-10 h-18 flex items-center justify-between">
        <div className="flex items-center space-x-10">
          <Link href="/" className="flex items-center space-x-3 group">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" className="transition-all duration-300 drop-shadow-[0_0_8px_rgba(245,158,11,0.3)] group-hover:drop-shadow-[0_0_16px_rgba(245,158,11,0.5)]">
              <rect width="28" height="28" rx="6" fill="#f59e0b" />
              <path d="M8 14L12 10L16 14L20 10" stroke="#0d0d0c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 18L12 14L16 18L20 14" stroke="#0d0d0c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.6"/>
            </svg>
            <span className="text-xl font-display font-bold text-cream tracking-[-0.5px]">
              Groove
            </span>
          </Link>
          <nav className="hidden md:flex items-center space-x-8">
            <Link href="/dashboard" className="nav-link text-sm">
              Dashboard
            </Link>
            <Link href="/chat" className="nav-link text-sm">
              Chat
            </Link>
          </nav>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/chat" className="btn-primary text-sm py-2.5 px-5 hidden md:inline-flex">
            Query Your Data
          </Link>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-md text-cream hover:bg-surface transition-colors"
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-deep/60 backdrop-blur-sm"
            onClick={() => setIsMenuOpen(false)}
          />
          <div className="absolute top-16 inset-x-0 bg-surface border-b border-edge shadow-2xl">
            <nav className="flex flex-col py-4 px-6 space-y-1">
              <Link
                href="/dashboard"
                onClick={() => setIsMenuOpen(false)}
                className="px-4 py-3 text-base font-medium text-cream rounded-md hover:bg-elevated transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/chat"
                onClick={() => setIsMenuOpen(false)}
                className="px-4 py-3 text-base font-medium text-cream rounded-md hover:bg-elevated transition-colors"
              >
                Chat
              </Link>
              <Link
                href="/chat"
                onClick={() => setIsMenuOpen(false)}
                className="btn-primary text-sm py-3 px-4 mt-2"
              >
                Query Your Data
              </Link>
            </nav>
          </div>
        </div>
      )}
    </header>
  );
}
