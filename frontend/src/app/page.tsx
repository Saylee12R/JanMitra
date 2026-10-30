import Link from 'next/link';

const STEPS = [
  { num: '1', title: 'Tell us about yourself', desc: 'Share basic details like age, location, and occupation' },
  { num: '2', title: 'Discover relevant schemes', desc: 'Our engine matches you with government schemes' },
  { num: '3', title: 'Understand eligibility', desc: 'See why each scheme may be relevant to you' },
  { num: '4', title: 'Prepare your documents', desc: 'Track required documents with a checklist' },
  { num: '5', title: 'Apply through official portals', desc: 'Direct links to official government websites' },
];

const FEATURES = [
  { icon: '🎯', title: 'Smart Matching', desc: 'Rule-based eligibility engine that checks your profile against official scheme criteria' },
  { icon: '📋', title: 'Document Checklist', desc: 'Track required documents and your application progress for each scheme' },
  { icon: '🤖', title: 'AI Assistant', desc: 'Ask questions about schemes and get grounded answers from official data' },
  { icon: '🔍', title: 'Search & Compare', desc: 'Explore all schemes, filter by category, and compare up to 3 schemes side by side' },
  { icon: '🏛️', title: 'Official Sources', desc: 'All information sourced from official government portals and databases' },
  { icon: '🔒', title: 'Trust & Transparency', desc: 'We never claim guaranteed eligibility — always verify on official portals' },
];

export default function HomePage() {
  return (
    <div className="animate-fadeIn">
      {/* Hero */}
      <section className="gradient-hero text-white py-20 md:py-28 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/15 rounded-full text-sm font-medium mb-6 backdrop-blur-sm">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            Powered by Official Government Data
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6">
            Government schemes,<br />
            <span className="text-emerald-300">made personal.</span>
          </h1>
          <p className="text-lg md:text-xl text-blue-100 max-w-2xl mx-auto mb-10 leading-relaxed">
            JanMitra helps you discover government schemes and services that may be relevant to you — based on your age, location, occupation and circumstances.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/onboarding"
              className="w-full sm:w-auto px-8 py-4 bg-white text-[#0F52BA] font-bold rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 text-lg"
            >
              Find My Schemes →
            </Link>
            <Link
              href="/schemes"
              className="w-full sm:w-auto px-8 py-4 bg-white/10 backdrop-blur-sm text-white font-semibold rounded-2xl border border-white/30 hover:bg-white/20 transition-all duration-200 text-lg"
            >
              Explore All Schemes
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">How JanMitra Works</h2>
          <p className="text-center text-gray-500 mb-14 max-w-xl mx-auto">Simple steps to discover schemes you may be eligible for</p>
          <div className="grid gap-6 md:grid-cols-5">
            {STEPS.map((step) => (
              <div key={step.num} className="text-center group">
                <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[#0F52BA] to-[#10B981] text-white flex items-center justify-center text-xl font-bold shadow-lg group-hover:scale-110 transition-transform duration-200">
                  {step.num}
                </div>
                <h3 className="font-semibold text-sm mb-1">{step.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">Why JanMitra</h2>
          <p className="text-center text-gray-500 mb-14 max-w-xl mx-auto">Everything you need to navigate government schemes with confidence</p>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass-card p-6 hover:shadow-lg transition-shadow duration-300">
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="font-bold text-lg mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Trust & Transparency</h2>
          <div className="disclaimer text-left">
            <p className="font-semibold mb-2">⚠️ Important Disclaimer</p>
            <p>JanMitra is an informational tool that helps you <strong>discover</strong> government schemes. It does <strong>not</strong> guarantee eligibility or submit applications on your behalf.</p>
            <p className="mt-2">All scheme information is sourced from official government portals. Final eligibility and application requirements should always be confirmed on the official scheme website.</p>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-8 text-sm text-gray-500">
            <span className="px-3 py-1 bg-gray-100 rounded-full">myScheme.gov.in</span>
            <span className="px-3 py-1 bg-gray-100 rounded-full">data.gov.in</span>
            <span className="px-3 py-1 bg-gray-100 rounded-full">scholarships.gov.in</span>
            <span className="px-3 py-1 bg-gray-100 rounded-full">pmkisan.gov.in</span>
            <span className="px-3 py-1 bg-gray-100 rounded-full">pmjay.gov.in</span>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to discover your schemes?</h2>
          <p className="text-gray-500 mb-8">It takes less than 2 minutes to set up your profile.</p>
          <Link
            href="/onboarding"
            className="inline-flex px-10 py-4 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 text-lg"
          >
            Get Started — It&apos;s Free
          </Link>
        </div>
      </section>
    </div>
  );
}
