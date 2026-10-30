'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { RecommendationItem, Application, SavedScheme } from '@/types';
import { getRecommendations, getApplications, getSavedSchemes } from '@/lib/api';
import { getStoredProfile, getStoredUserId, isProfileComplete } from '@/lib/store';

export default function DashboardPage() {
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [saved, setSaved] = useState<SavedScheme[]>([]);
  const [completeness, setCompleteness] = useState(0);
  const [loading, setLoading] = useState(true);
  const profile = getStoredProfile();
  const userId = getStoredUserId() || 1;
  const hasProfile = isProfileComplete(profile);

  useEffect(() => {
    if (!hasProfile || !profile) { setLoading(false); return; }
    Promise.all([
      getRecommendations(profile as Record<string, unknown>).catch(() => ({ schemes: [], count: 0, profile_completeness: 0, disclaimer: '' })),
      getApplications(userId).catch(() => []),
      getSavedSchemes(userId).catch(() => []),
    ]).then(([recs, apps, sv]) => {
      setRecommendations(recs.schemes.slice(0, 5));
      setCompleteness(recs.profile_completeness);
      setApplications(apps as Application[]);
      setSaved(sv as SavedScheme[]);
    }).finally(() => setLoading(false));
  }, []);

  const STATUS_LABELS: Record<string, { label: string; color: string }> = {
    interested: { label: 'Interested', color: 'bg-gray-100 text-gray-600' },
    documents_pending: { label: 'Documents Pending', color: 'bg-amber-100 text-amber-700' },
    ready_to_apply: { label: 'Ready to Apply', color: 'bg-blue-100 text-blue-700' },
    applied: { label: 'Applied', color: 'bg-purple-100 text-purple-700' },
    completed: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  };

  if (loading) {
    return (
      <div className="py-24 text-center">
        <div className="w-10 h-10 border-4 border-[#0F52BA] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-gray-400">Loading dashboard…</p>
      </div>
    );
  }

  if (!hasProfile) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="text-5xl mb-4">👤</div>
        <h2 className="text-2xl font-bold mb-3">Set up your profile first</h2>
        <p className="text-gray-500 mb-8">Complete your profile to get personalized scheme recommendations.</p>
        <Link href="/onboarding" className="px-8 py-3 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-bold rounded-2xl shadow-lg hover:shadow-xl transition hover:scale-105">
          Start Profile Setup →
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Your JanMitra overview</p>
        </div>
        <Link href="/onboarding" className="px-4 py-2 border border-gray-200 text-sm rounded-xl hover:bg-gray-50 transition text-gray-600">
          ✏️ Edit Profile
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard icon="🎯" label="Recommendations" value={recommendations.length} color="blue" href="/recommendations" />
        <StatCard icon="📌" label="Saved Schemes" value={saved.length} color="green" href="/saved" />
        <StatCard icon="📋" label="Applications" value={applications.length} color="amber" href="/checklist" />
        <StatCard icon="👤" label="Profile Complete" value={`${completeness}%`} color="purple" href="/onboarding" />
      </div>

      {/* Profile Completeness */}
      <div className="glass-card p-5 mb-8">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-800">Profile Completeness</h3>
          <span className="text-sm font-bold text-[#0F52BA]">{completeness}%</span>
        </div>
        <div className="progress-bar mb-2">
          <div className="progress-bar-fill" style={{ width: `${completeness}%` }} />
        </div>
        <p className="text-xs text-gray-500">
          {completeness < 100
            ? 'Complete your profile to get better scheme matches.'
            : '✅ Profile fully complete!'}
        </p>
        {profile && (
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {profile.age && <Tag>Age: {profile.age}</Tag>}
            {profile.gender && <Tag>Gender: {profile.gender}</Tag>}
            {profile.state && <Tag>State: {profile.state}</Tag>}
            {profile.occupation && <Tag>Occupation: {profile.occupation}</Tag>}
            {profile.category && <Tag>Category: {profile.category}</Tag>}
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Top Recommendations */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900">Top Recommendations</h3>
            <Link href="/recommendations" className="text-sm text-[#0F52BA] hover:underline">View all →</Link>
          </div>
          {recommendations.length === 0 ? (
            <div className="glass-card p-6 text-center text-gray-500 text-sm">
              <p>No recommendations yet.</p>
              <Link href="/recommendations" className="text-[#0F52BA] text-xs hover:underline mt-1 block">Load recommendations →</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recommendations.map((r) => (
                <Link key={r.id} href={`/schemes/${r.id}`}
                  className="glass-card p-4 block hover:shadow-md transition group">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-900 truncate group-hover:text-[#0F52BA]">{r.name}</p>
                      <p className="text-xs text-gray-400">{r.category}</p>
                    </div>
                    <span className={`match-badge shrink-0 ${r.match_score >= 80 ? 'high' : r.match_score >= 50 ? 'medium' : 'low'}`}>
                      {r.match_score.toFixed(0)}%
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Applications */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900">My Applications</h3>
            <Link href="/checklist" className="text-sm text-[#0F52BA] hover:underline">Checklist →</Link>
          </div>
          {applications.length === 0 ? (
            <div className="glass-card p-6 text-center text-gray-500 text-sm">
              <p>No applications tracked yet.</p>
              <p className="text-xs mt-1">Open a scheme and click "Prepare Application" to start.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {applications.map((app) => {
                const st = STATUS_LABELS[app.status] || { label: app.status, color: 'bg-gray-100 text-gray-600' };
                return (
                  <div key={app.id} className="glass-card p-4">
                    <p className="font-semibold text-sm text-gray-900 truncate">{app.scheme?.name || `Scheme #${app.scheme_id}`}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${st.color}`}>{st.label}</span>
                      <Link href={`/checklist?scheme_id=${app.scheme_id}`} className="text-xs text-[#0F52BA] hover:underline">Checklist →</Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="mt-8 glass-card p-6">
        <h3 className="font-bold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { href: '/recommendations', icon: '🎯', label: 'My Recommendations' },
            { href: '/schemes', icon: '🔍', label: 'Explore Schemes' },
            { href: '/assistant', icon: '🤖', label: 'Ask AI Assistant' },
            { href: '/compare', icon: '⚖️', label: 'Compare Schemes' },
          ].map((link) => (
            <Link key={link.href} href={link.href}
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-blue-50 hover:text-[#0F52BA] transition text-center text-sm font-medium text-gray-700">
              <span className="text-2xl">{link.icon}</span>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color, href }: { icon: string; label: string; value: string | number; color: string; href: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    green: 'bg-green-50 text-green-700 border-green-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    purple: 'bg-purple-50 text-purple-700 border-purple-100',
  };
  return (
    <Link href={href} className={`rounded-xl border p-4 transition hover:shadow-md ${colors[color]}`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs font-medium mt-0.5">{label}</div>
    </Link>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return <span className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full">{children}</span>;
}
