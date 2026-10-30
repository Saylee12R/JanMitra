'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SchemeListItem, SCHEME_CATEGORIES } from '@/types';
import { getSchemes } from '@/lib/api';

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<SchemeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [sort, setSort] = useState('relevance');
  const [compareList, setCompareList] = useState<number[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (q) params.q = q;
      if (category) params.category = category;
      if (sort) params.sort = sort;
      const data = await getSchemes(params);
      setSchemes(data);
    } catch {
      setError('Could not load schemes. Please ensure the backend is running.');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [q, category, sort]);

  const toggleCompare = (id: number) => {
    setCompareList((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-10 animate-fadeIn">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-1">Explore Schemes</h1>
        <p className="text-gray-500">Browse all {schemes.length} government schemes</p>
      </div>

      {/* Search + Filters */}
      <div className="glass-card p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search schemes, keywords, ministry…"
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition text-sm"
          />
          <select value={category} onChange={(e) => setCategory(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition text-sm bg-white">
            <option value="">All Categories</option>
            {SCHEME_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition text-sm bg-white">
            <option value="relevance">Sort: Relevance</option>
            <option value="alphabetical">Sort: A-Z</option>
            <option value="newest">Sort: Newest</option>
            <option value="category">Sort: Category</option>
          </select>
        </div>
      </div>

      {/* Compare Floating Bar */}
      {compareList.length >= 2 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 glass-card px-6 py-3 flex items-center gap-4 shadow-xl border border-blue-100">
          <span className="text-sm font-medium text-gray-700">{compareList.length} schemes selected</span>
          <Link href={`/compare?ids=${compareList.join(',')}`}
            className="px-5 py-2 bg-[#0F52BA] text-white text-sm font-semibold rounded-xl hover:bg-[#0d48a8] transition">
            Compare Now →
          </Link>
          <button onClick={() => setCompareList([])} className="text-sm text-gray-400 hover:text-gray-600">Clear</button>
        </div>
      )}

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-6">{error}</div>}

      {loading ? (
        <LoadingGrid />
      ) : schemes.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <div className="text-5xl mb-4">🔍</div>
          <p>No schemes found for your search.</p>
          <button onClick={() => { setQ(''); setCategory(''); }} className="mt-4 text-[#0F52BA] hover:underline text-sm">Clear filters</button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {schemes.map((scheme) => (
            <SchemeCard
              key={scheme.id}
              scheme={scheme}
              isComparing={compareList.includes(scheme.id)}
              onToggleCompare={() => toggleCompare(scheme.id)}
              canCompare={compareList.length < 3 || compareList.includes(scheme.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SchemeCard({
  scheme, isComparing, onToggleCompare, canCompare
}: {
  scheme: SchemeListItem;
  isComparing: boolean;
  onToggleCompare: () => void;
  canCompare: boolean;
}) {
  return (
    <div className={`glass-card p-5 hover:shadow-lg transition-all duration-300 flex flex-col ${isComparing ? 'ring-2 ring-[#0F52BA]' : ''}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="category-badge">{scheme.category}</span>
        <button
          onClick={onToggleCompare}
          disabled={!canCompare && !isComparing}
          title={isComparing ? 'Remove from compare' : 'Add to compare'}
          className={`text-xs px-2 py-1 rounded-lg border transition ${isComparing ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-400 hover:border-gray-300 disabled:opacity-30'}`}>
          {isComparing ? '✓ Added' : '⊕ Compare'}
        </button>
      </div>
      <h2 className="font-bold text-gray-900 mb-1 text-sm leading-snug line-clamp-2">{scheme.name}</h2>
      {scheme.ministry && <p className="text-xs text-gray-400 mb-2">{scheme.ministry}</p>}
      <p className="text-xs text-gray-600 line-clamp-3 flex-1">{scheme.description}</p>
      {scheme.benefits && (
        <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-2 py-1 mt-2 line-clamp-2">💰 {scheme.benefits}</p>
      )}
      <div className="mt-4 flex gap-2">
        <Link href={`/schemes/${scheme.id}`}
          className="flex-1 text-center px-3 py-2 bg-[#0F52BA] text-white text-xs font-semibold rounded-xl hover:bg-[#0d48a8] transition">
          View Details
        </Link>
        {scheme.application_url && (
          <a href={scheme.application_url} target="_blank" rel="noopener noreferrer"
            className="px-3 py-2 border border-gray-200 text-xs rounded-xl hover:bg-gray-50 transition text-gray-600">
            Apply
          </a>
        )}
      </div>
    </div>
  );
}

function LoadingGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="glass-card p-5 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-20 mb-3"></div>
          <div className="h-5 bg-gray-200 rounded mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4 mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      ))}
    </div>
  );
}
