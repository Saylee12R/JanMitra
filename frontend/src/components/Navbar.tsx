'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/schemes', label: 'Explore Schemes' },
  { href: '/recommendations', label: 'My Recommendations' },
  { href: '/saved', label: 'Saved' },
  { href: '/checklist', label: 'Checklist' },
  { href: '/assistant', label: 'Assistant' },
  { href: '/dashboard', label: 'Dashboard' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-200/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0F52BA] to-[#10B981] flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:shadow-xl transition-shadow">
              J
            </div>
            <span className="text-xl font-bold gradient-text hidden sm:inline">JanMitra</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-50 text-[#0F52BA]'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* CTA + Mobile Toggle */}
          <div className="flex items-center gap-3">
            <Link
              href="/onboarding"
              className="hidden sm:inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white text-sm font-semibold rounded-xl shadow-md hover:shadow-lg transition-all duration-200 hover:scale-[1.02]"
            >
              Find My Schemes
            </Link>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 animate-fadeIn">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-blue-50 text-[#0F52BA]' : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            <Link
              href="/onboarding"
              onClick={() => setMobileOpen(false)}
              className="block mx-4 mt-3 text-center px-4 py-3 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white text-sm font-semibold rounded-xl"
            >
              Find My Schemes
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
