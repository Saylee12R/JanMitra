'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Scheme } from '@/types';
import { getScheme, saveScheme, removeSavedScheme, getSavedSchemes, createApplication } from '@/lib/api';
import { getStoredUserId, getStoredProfile } from '@/lib/store';

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [applied, setApplied] = useState(false);

  const userId = getStoredUserId() || 1;

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getScheme(id),
      getSavedSchemes(userId).catch(() => []),
    ]).then(([s, savedList]) => {
      setScheme(s);
      const savedIds = (savedList as { scheme_id: number }[]).map((x) => x.scheme_id);
      setSaved(savedIds.includes(id));
    }).catch(() => {}).finally(() => setLoading(false));
  }, [id, userId]);

  const handleSave = async () => {
    setSaveLoading(true);
    try {
      if (saved) {
        await removeSavedScheme(id, userId);
        setSaved(false);
      } else {
        await saveScheme(id, userId);
        setSaved(true);
      }
    } catch { /* swallow */ }
    setSaveLoading(false);
  };

  const handleStartApplication = async () => {
    try {
      await createApplication(userId, { scheme_id: id, status: 'documents_pending' });
      setApplied(true);
      router.push(`/checklist?scheme_id=${id}`);
    } catch {
      router.push(`/checklist?scheme_id=${id}`);
    }
  };

  if (loading) return <LoadingDetail />;
  if (!scheme) return <NotFound />;

  const lastVerified = scheme.last_verified_at
    ? new Date(scheme.last_verified_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'Not specified';

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-fadeIn">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 mb-6 flex items-center gap-2">
        <Link href="/schemes" className="hover:text-[#0F52BA] transition">Schemes</Link>
        <span>›</span>
        <span className="text-gray-800 truncate max-w-xs">{scheme.name}</span>
      </nav>

      {/* Header Card */}
      <div className="glass-card p-6 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="category-badge">{scheme.category}</span>
              {scheme.active && <span className="category-badge bg-green-50 text-green-700">Active</span>}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">{scheme.name}</h1>
            {scheme.ministry && <p className="text-sm text-gray-500">{scheme.ministry}</p>}
            {scheme.department && scheme.department !== scheme.ministry && (
              <p className="text-xs text-gray-400">{scheme.department}</p>
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-2 shrink-0">
            <button onClick={handleSave} disabled={saveLoading}
              className={`px-4 py-2 rounded-xl text-sm font-medium border transition ${saved ? 'bg-yellow-50 border-yellow-300 text-yellow-700' : 'border-gray-200 hover:bg-gray-50 text-gray-600'}`}>
              {saved ? '★ Saved' : '☆ Save'}
            </button>
            <button onClick={handleStartApplication}
              className="px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-500 text-white hover:bg-emerald-600 transition">
              📋 Prepare Application
            </button>
          </div>
        </div>
      </div>

      {/* Description */}
      <Section title="About this Scheme">
        <p className="text-gray-700 leading-relaxed">{scheme.detailed_description || scheme.description}</p>
      </Section>

      {/* Eligibility */}
      <Section title="Who Can Apply (Eligibility)">
        <div className="grid sm:grid-cols-2 gap-3">
          {scheme.min_age != null && <EligRow label="Minimum Age" value={`${scheme.min_age} years`} />}
          {scheme.max_age != null && <EligRow label="Maximum Age" value={`${scheme.max_age} years`} />}
          {scheme.income_limit != null && <EligRow label="Income Limit" value={`₹${scheme.income_limit.toLocaleString('en-IN')}/year`} />}
          {scheme.gender && scheme.gender !== 'any' && <EligRow label="Gender" value={capitalize(scheme.gender)} />}
          {scheme.occupation?.length ? <EligRow label="Occupation" value={scheme.occupation.join(', ')} /> : null}
          {scheme.category_requirement?.length ? <EligRow label="Social Category" value={scheme.category_requirement.join(', ')} /> : null}
          {scheme.state?.length ? <EligRow label="States" value={scheme.state.join(', ')} /> : null}
          {scheme.education_requirement?.length ? <EligRow label="Education" value={scheme.education_requirement.join(', ')} /> : null}
          {scheme.disability_required != null && <EligRow label="Disability Required" value={scheme.disability_required ? 'Yes' : 'No'} />}
          {!scheme.min_age && !scheme.max_age && !scheme.gender && !scheme.occupation?.length && (
            <p className="text-gray-500 text-sm col-span-2">Open to all eligible citizens. Check the official website for complete eligibility.</p>
          )}
        </div>
      </Section>

      {/* Benefits */}
      {scheme.benefits && (
        <Section title="Benefits">
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
            <p className="text-emerald-800 leading-relaxed">{scheme.benefits}</p>
          </div>
        </Section>
      )}

      {/* Documents */}
      {scheme.documents?.length ? (
        <Section title="Required Documents">
          <ul className="space-y-2">
            {scheme.documents.map((doc, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">{i + 1}</span>
                {doc}
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {/* Application Process */}
      {scheme.application_process && (
        <Section title="How to Apply">
          <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-line">{scheme.application_process}</div>
        </Section>
      )}

      {/* Source & Actions */}
      <div className="glass-card p-6 mb-6">
        <h3 className="font-bold text-gray-900 mb-4">Official Information</h3>
        <div className="space-y-2 text-sm">
          {scheme.source_name && <InfoRow label="Source" value={scheme.source_name} />}
          {scheme.official_source_url && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium w-28 shrink-0">Official URL</span>
              <a href={scheme.official_source_url} target="_blank" rel="noopener noreferrer"
                className="text-[#0F52BA] hover:underline break-all text-xs">{scheme.official_source_url}</a>
            </div>
          )}
          <InfoRow label="Last Verified" value={lastVerified} />
        </div>
        <div className="flex flex-wrap gap-3 mt-5">
          {scheme.application_url && (
            <a href={scheme.application_url} target="_blank" rel="noopener noreferrer"
              className="px-6 py-3 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-semibold rounded-xl shadow hover:shadow-lg transition-all hover:scale-[1.01]">
              🏛️ Apply on Official Portal →
            </a>
          )}
          <button onClick={handleStartApplication}
            className="px-6 py-3 border-2 border-[#0F52BA] text-[#0F52BA] font-semibold rounded-xl hover:bg-blue-50 transition">
            📋 Start Document Checklist
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer">
        <strong>⚠️ Important:</strong> This information is provided for assistance purposes. Final eligibility and application requirements should be confirmed on the official government website. JanMitra does not guarantee eligibility and does not submit applications on your behalf.
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass-card p-6 mb-6">
      <h3 className="font-bold text-gray-900 mb-4 text-lg">{title}</h3>
      {children}
    </div>
  );
}

function EligRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 bg-gray-50 rounded-xl px-4 py-3">
      <span className="text-gray-500 text-sm font-medium shrink-0 w-28">{label}</span>
      <span className="text-gray-800 text-sm font-semibold">{value}</span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-gray-500 font-medium w-28 shrink-0">{label}</span>
      <span className="text-gray-800">{value}</span>
    </div>
  );
}

function capitalize(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }

function LoadingDetail() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-2/3"></div>
      <div className="h-40 bg-gray-200 rounded-2xl"></div>
      <div className="h-32 bg-gray-200 rounded-2xl"></div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="text-center py-24">
      <div className="text-5xl mb-4">😕</div>
      <h2 className="text-xl font-bold mb-2">Scheme not found</h2>
      <Link href="/schemes" className="text-[#0F52BA] hover:underline">Browse all schemes →</Link>
    </div>
  );
}
