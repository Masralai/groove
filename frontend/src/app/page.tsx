import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 px-10">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-midnight-ink tracking-[-2px] md:tracking-[-3px] leading-[1.05] mb-6">
            Unlock your{" "}
            <span className="bg-gradient-to-r from-[#19a05f] to-[#0d7f8c] bg-clip-text text-transparent">
              Meta Ads
            </span>{" "}
            data
          </h1>
          <p className="text-lg md:text-xl text-slate-text max-w-2xl mx-auto mb-10 leading-relaxed">
            Ask questions about your campaign performance in plain English.
            Groove transforms complex ad data into actionable insights.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/chat" className="btn-primary text-base px-8 py-3.5 min-w-[200px]">
              Start Chatting
            </Link>
            <Link href="/dashboard" className="btn-secondary text-base px-8 py-3.5 min-w-[200px]">
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-10 bg-cloud-gray/40">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-midnight-ink text-center mb-16 tracking-[-1px]">
            How Groove Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="card text-center p-8 hover:shadow-lg transition-shadow duration-200">
              <div className="w-14 h-14 bg-gradient-to-br from-[#19a05f]/20 to-[#0d7f8c]/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-7 h-7 text-[#19a05f]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-midnight-ink mb-3">Data Pipeline</h3>
              <p className="text-base text-slate-text leading-relaxed">
                Automatically sync your Meta Ads campaigns, ad sets, and insights into a unified analytics database.
              </p>
            </div>
            <div className="card text-center p-8 hover:shadow-lg transition-shadow duration-200">
              <div className="w-14 h-14 bg-gradient-to-br from-[#19a05f]/20 to-[#0d7f8c]/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-7 h-7 text-[#19a05f]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-midnight-ink mb-3">Natural Language Queries</h3>
              <p className="text-base text-slate-text leading-relaxed">
                Ask questions like &ldquo;What was my top campaign last month?&rdquo; and get instant answers.
              </p>
            </div>
            <div className="card text-center p-8 hover:shadow-lg transition-shadow duration-200">
              <div className="w-14 h-14 bg-gradient-to-br from-[#19a05f]/20 to-[#0d7f8c]/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-7 h-7 text-[#19a05f]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-midnight-ink mb-3">Actionable Insights</h3>
              <p className="text-base text-slate-text leading-relaxed">
                Get data-driven recommendations to optimize your ad spend and maximize ROI.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-10">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-midnight-ink mb-4 tracking-[-1px]">
            Ready to get started?
          </h2>
          <p className="text-lg text-slate-text mb-8">
            Connect your Meta Ads account and start querying your data in minutes.
          </p>
          <Link href="/chat" className="btn-primary text-base px-10 py-3.5">
            Start Chatting with Your Data
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-cloud-border py-8 px-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <p className="text-sm text-slate-text">
            &copy; {new Date().getFullYear()} Groove. Built with Meta Marketing API.
          </p>
          <Link
            href="https://developers.facebook.com/docs/marketing-api"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-slate-text hover:text-midnight-ink transition-colors"
          >
            Meta Marketing API Docs
          </Link>
        </div>
      </footer>
    </div>
  );
}