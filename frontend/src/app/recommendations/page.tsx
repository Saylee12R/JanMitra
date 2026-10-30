'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { RecommendationItem } from '@/types';
import { getRecommendations } from '@/lib/api';
import { getStoredProfile, getStoredUserId, isProfileComplete } from '@/lib/store';

function MatchBadge({ score }: { score: number }) {
  const cls = score >= 80 ? 'high' : score >= 50 ? 'medium' : 'low';
  return <span className={`match-badge ${cls}`}>{score.toFixed(0)}% match</span>;
}

export default function RecommendationsPage() {
  const router = useRouter();
  const [schemes, setSchemes] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [completeness, setCompleteness] = useState(0);
  const [count, setCount] = useState(0);

  useEffect(() => {
    const profile = getStoredProfile();
    if (!isProfileComplete(profile)) {
      router.replace('/onboarding');
      return;
    }
    getRecommendations(profile as Record<string, unknown>)
      .then((data) => {
        setSchemes(data.schemes);
        setCount(data.count);
        setCompleteness(data.profile_completeness);
      })
      .catch(() => setError('Could not load recommendations. Please check that the backend is running.'))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <LoadingState />;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 animate-fadeIn">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Your Recommendations</h1>
            <p className="text-gray-500 mt-1">Based on your profile, you may be eligible for these schemes</p>
          </div>
          <Link href="/onboarding"
            className="px-4 py-2 text-sm border border-gray-200 rounded-xl hover:bg-gray-50 transition text-gray-600">
            ✏️ Edit Profile
          </Link>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
          <StatCard label="Matching Schemes" value={count.toString()} color="blue" />
          <StatCard label="Profile Complete" value={`${completeness}%`} color="green" />
          <StatCard label="Data Source" value="Official Gov." color="amber" />
        </div>

        {/* Disclaimer */}
        <div className="disclaimer">
          <strong>📋 Disclaimer:</strong> Based on the information you provided, you <em>may</em> be eligible for these schemes. Final eligibility should be confirmed with the official scheme authority.
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-6">{error}</div>
      )}

      {schemes.length === 0 && !error ? (
        <EmptyState />
      ) : (
        <div className="space-y-4">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
}

function SchemeCard({ scheme }: { scheme: RecommendationItem }) {
  return (
    <div className="glass-card p-6 hover:shadow-lg transition-all duration-300 group animate-slideUp">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="category-badge">{scheme.category}</span>
            <MatchBadge score={scheme.match_score} />
          </div>
          <h2 className="text-lg font-bold text-gray-900 group-hover:text-[#0F52BA] transition-colors">{scheme.name}</h2>
          {scheme.ministry && <p className="text-xs text-gray-400 mt-0.5">{scheme.ministry}</p>}
        </div>
        <Link href={`/schemes/${scheme.id}`}
          className="shrink-0 px-4 py-2 bg-[#0F52BA] text-white text-sm font-semibold rounded-xl hover:bg-[#0d48a8] transition-colors">
          View Details
        </Link>
      </div>

      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{scheme.description}</p>

      {/* Why matched */}
      {scheme.reasons.length > 0 && (
        <div className="bg-green-50 rounded-xl px-4 py-3 mb-4">
          <p className="text-xs font-semibold text-green-700 mb-1">✅ Why this may be relevant:</p>
          <ul className="space-y-0.5">
            {scheme.reasons.slice(0, 3).map((r, i) => (
              <li key={i} className="text-xs text-green-700">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {scheme.benefits && (
        <p className="text-xs text-gray-500"><span className="font-medium text-gray-700">Benefits:</span> {scheme.benefits.slice(0, 120)}{scheme.benefits.length > 120 ? '…' : ''}</p>
      )}

      {scheme.application_url && (
        <a href={scheme.application_url} target="_blank" rel="noopener noreferrer"
          className="inline-flex mt-3 text-xs text-[#0F52BA] hover:underline font-medium">
          🔗 Official Portal →
        </a>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    green: 'bg-green-50 text-green-700 border-green-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs font-medium mt-0.5">{label}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-20 text-center">
      <div className="w-12 h-12 border-4 border-[#0F52BA] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-gray-500">Finding schemes for your profile…</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-20">
      <div className="text-5xl mb-4">🔍</div>
      <h2 className="text-xl font-bold mb-2">No matching schemes found</h2>
      <p className="text-gray-500 mb-6 max-w-md mx-auto">Try completing more profile fields or explore all available schemes.</p>
      <div className="flex justify-center gap-3">
        <Link href="/onboarding" className="px-5 py-2.5 bg-[#0F52BA] text-white rounded-xl font-medium hover:bg-[#0d48a8] transition">Update Profile</Link>
        <Link href="/schemes" className="px-5 py-2.5 border border-gray-200 rounded-xl font-medium hover:bg-gray-50 transition">Explore Schemes</Link>
      </div>
    </div>
  );
}
