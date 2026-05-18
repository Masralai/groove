import Link from "next/link";
import ScrollReveal from "@/components/ScrollReveal";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/2 -translate-y-1/2 right-0 w-[45%] h-[80%] bg-gradient-radial from-amber/15 via-amber/5 to-transparent blur-3xl" />
          <div className="absolute top-1/4 right-[20%] w-96 h-96 rounded-full border border-amber/10" />
          <div className="absolute bottom-1/4 right-[10%] w-48 h-48 rounded-full bg-amber/5 blur-2xl" />
          <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(245,158,11,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(245,158,11,0.08) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        </div>

        <div className="relative w-full max-w-7xl mx-auto px-10 py-20 md:py-32">
          <div className="max-w-2xl lg:max-w-[55%]">
            <div className="animate-in">
              <h1 className="font-display font-bold text-cream text-5xl md:text-7xl lg:text-8xl tracking-[-0.03em] leading-[1.05] mb-6">
                Unlock your{" "}
                <span className="bg-gradient-to-r from-amber to-amber-deep bg-clip-text text-transparent">
                  Meta Ads
                </span>{" "}
                data
              </h1>
            </div>
            <div className="animate-in animate-in-d1">
              <p className="text-lg md:text-xl text-muted max-w-xl leading-relaxed mb-10">
                Ask questions about your campaign performance in plain English.
                Groove transforms complex ad data into actionable insights.
              </p>
            </div>
            <div className="animate-in animate-in-d2 flex flex-col sm:flex-row items-start gap-4">
              <Link href="/chat" className="btn-primary text-base px-8 py-3.5 min-w-[200px]">
                Start Chatting
              </Link>
              <Link href="/dashboard" className="btn-secondary text-base px-8 py-3.5 min-w-[200px]">
                View Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      <ScrollReveal>
        <section className="py-24 px-10 bg-surface/60 border-t border-edge">
          <div className="max-w-7xl mx-auto">
            <h2 className="font-display font-bold text-3xl md:text-4xl text-cream text-center mb-4 tracking-[-0.02em]">
              How Groove Works
            </h2>
            <p className="text-muted text-center mb-16 max-w-xl mx-auto">
              Three simple steps from raw data to real decisions
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 card card-glow p-8 lg:p-10">
                <div className="flex flex-col sm:flex-row sm:items-start gap-6">
                  <div className="w-14 h-14 shrink-0 bg-gradient-to-br from-amber/20 to-amber-deep/20 rounded-2xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-display font-bold text-cream mb-2">Data Pipeline</h3>
                    <p className="text-base text-muted leading-relaxed">
                      Automatically sync your Meta Ads campaigns, ad sets, and insights into a unified analytics database. No manual exports, no CSV wrangling.
                    </p>
                  </div>
                </div>
              </div>

              <div className="card card-glow p-8 lg:p-10 flex flex-col">
                <div className="w-14 h-14 bg-gradient-to-br from-amber/20 to-amber-deep/20 rounded-2xl flex items-center justify-center mb-5">
                  <svg className="w-7 h-7 text-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h3 className="text-xl font-display font-bold text-cream mb-2">Natural Language Queries</h3>
                <p className="text-base text-muted leading-relaxed flex-1">
                  Ask questions like &ldquo;What was my top campaign last month?&rdquo; and get instant answers.
                </p>
              </div>

              <div className="lg:col-span-3 card card-glow p-8 lg:p-10 bg-gradient-to-r from-surface to-amber/5 border-amber/10">
                <div className="flex flex-col sm:flex-row sm:items-center gap-6">
                  <div className="w-14 h-14 shrink-0 bg-gradient-to-br from-amber/20 to-amber-deep/20 rounded-2xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-display font-bold text-cream mb-2">Actionable Insights</h3>
                    <p className="text-base text-muted leading-relaxed">
                      Get data-driven recommendations to optimize your ad spend and maximize ROI. Every answer includes the SQL so you can verify the results.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </ScrollReveal>

      <ScrollReveal>
        <section className="py-24 px-10">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="font-display font-bold text-3xl md:text-4xl text-cream mb-4 tracking-[-0.02em]">
              Ready to get started?
            </h2>
            <p className="text-lg text-muted mb-8">
              Connect your Meta Ads account and start querying your data in minutes.
            </p>
            <Link href="/chat" className="btn-primary text-base px-10 py-3.5">
              Start Chatting with Your Data
            </Link>
          </div>
        </section>
      </ScrollReveal>

      <footer className="border-t border-edge py-8 px-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <p className="text-sm text-dim">
            &copy; {new Date().getFullYear()} Groove. Built with Meta Marketing API.
          </p>
          <Link
            href="https://developers.facebook.com/docs/marketing-api"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-dim hover:text-cream transition-colors"
          >
            Meta Marketing API Docs
          </Link>
        </div>
      </footer>
    </div>
  );
}
