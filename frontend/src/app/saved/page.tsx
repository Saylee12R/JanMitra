'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SavedScheme } from '@/types';
import { getSavedSchemes, removeSavedScheme } from '@/lib/api';
import { getStoredUserId } from '@/lib/store';

export default function SavedPage() {
  const [schemes, setSchemes] = useState<SavedScheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const userId = getStoredUserId() || 1;

  const load = () => {
    setLoading(true);
    getSavedSchemes(userId)
      .then(setSchemes)
      .catch(() => setError('Could not load saved schemes.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [userId]);

  const handleRemove = async (schemeId: number) => {
    try {
      await removeSavedScheme(schemeId, userId);
      setSchemes((prev) => prev.filter((s) => s.scheme_id !== schemeId));
    } catch { /* swallow */ }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-fadeIn">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Saved Schemes</h1>
          <p className="text-gray-500 mt-1">Schemes you've bookmarked for later</p>
        </div>
        <Link href="/schemes" className="px-4 py-2 text-sm bg-[#0F52BA] text-white rounded-xl hover:bg-[#0d48a8] transition">
          + Browse More
        </Link>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-6">{error}</div>}

      {loading ? (
        <div className="py-20 text-center">
          <div className="w-10 h-10 border-4 border-[#0F52BA] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-gray-400 text-sm">Loading saved schemes…</p>
        </div>
      ) : schemes.length === 0 ? (
        <div className="text-center py-24">
          <div className="text-5xl mb-4">📌</div>
          <h2 className="text-xl font-bold mb-2">No saved schemes yet</h2>
          <p className="text-gray-500 mb-6 max-w-sm mx-auto">Browse schemes and click Save to bookmark them here.</p>
          <Link href="/schemes" className="px-5 py-2.5 bg-[#0F52BA] text-white rounded-xl font-medium hover:bg-[#0d48a8] transition">
            Explore Schemes
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {schemes.map((saved) => (
            <div key={saved.id} className="glass-card p-5 flex flex-wrap items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <span className="category-badge mb-2 inline-block">{saved.scheme.category}</span>
                <h2 className="font-bold text-gray-900 mb-1">{saved.scheme.name}</h2>
                {saved.scheme.ministry && <p className="text-xs text-gray-400 mb-2">{saved.scheme.ministry}</p>}
                <p className="text-sm text-gray-600 line-clamp-2">{saved.scheme.description}</p>
                {saved.scheme.benefits && (
                  <p className="text-xs text-emerald-700 mt-2">💰 {saved.scheme.benefits.slice(0, 100)}{saved.scheme.benefits.length > 100 ? '…' : ''}</p>
                )}
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                <Link href={`/schemes/${saved.scheme_id}`}
                  className="px-4 py-2 bg-[#0F52BA] text-white text-sm rounded-xl hover:bg-[#0d48a8] transition text-center">
                  View Details
                </Link>
                <Link href={`/checklist?scheme_id=${saved.scheme_id}`}
                  className="px-4 py-2 border border-emerald-300 text-emerald-700 text-sm rounded-xl hover:bg-emerald-50 transition text-center">
                  📋 Checklist
                </Link>
                <button onClick={() => handleRemove(saved.scheme_id)}
                  className="px-4 py-2 border border-gray-200 text-gray-500 text-sm rounded-xl hover:bg-gray-50 transition">
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
