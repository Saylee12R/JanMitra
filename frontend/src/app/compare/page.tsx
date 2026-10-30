'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Scheme } from '@/types';
import { compareSchemes, getSchemes } from '@/lib/api';

function CompareContent() {
  const searchParams = useSearchParams();
  const idsParam = searchParams.get('ids');
  const initialIds = idsParam ? idsParam.split(',').map(Number).filter(Boolean) : [];

  const [selected, setSelected] = useState<number[]>(initialIds);
  const [allSchemes, setAllSchemes] = useState<{ id: number; name: string }[]>([]);
  const [results, setResults] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getSchemes({ limit: '100' }).then((s) => setAllSchemes(s.map((x) => ({ id: x.id, name: x.name })))).catch(() => {});
  }, []);

  useEffect(() => {
    if (initialIds.length >= 2) runCompare(initialIds);
  }, []);

  const runCompare = async (ids: number[]) => {
    if (ids.length < 2) return;
    setLoading(true);
    try {
      const data = await compareSchemes(ids);
      setResults(data.schemes);
    } catch {
      setError('Could not load comparison.');
    }
    setLoading(false);
  };

  const toggleScheme = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  };

  const ROWS = [
    { label: 'Category', key: 'category' },
    { label: 'Ministry', key: 'ministry' },
    { label: 'Min Age', key: 'min_age', format: (v: unknown) => v != null ? `${v} yrs` : 'Any' },
    { label: 'Max Age', key: 'max_age', format: (v: unknown) => v != null ? `${v} yrs` : 'Any' },
    { label: 'Income Limit', key: 'income_limit', format: (v: unknown) => v != null ? `₹${(v as number).toLocaleString('en-IN')}` : 'None' },
    { label: 'Gender', key: 'gender', format: (v: unknown) => v && v !== 'any' ? String(v) : 'All' },
    { label: 'Social Category', key: 'category_requirement', format: (v: unknown) => Array.isArray(v) && v.length ? v.join(', ') : 'All' },
    { label: 'State', key: 'state', format: (v: unknown) => Array.isArray(v) && v.length ? v.join(', ') : 'All India' },
    { label: 'Benefits', key: 'benefits' },
    { label: 'Documents', key: 'documents', format: (v: unknown) => Array.isArray(v) ? `${v.length} required` : '–' },
  ] as const;

  return (
    <div>
      {/* Scheme selector */}
      <div className="glass-card p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-3">Select 2-3 schemes to compare</h2>
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
          {allSchemes.map((s) => (
            <button key={s.id} onClick={() => toggleScheme(s.id)}
              disabled={!selected.includes(s.id) && selected.length >= 3}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium border-2 transition ${selected.includes(s.id) ? 'border-[#0F52BA] bg-blue-50 text-[#0F52BA]' : 'border-gray-200 text-gray-600 hover:border-gray-300 disabled:opacity-40'}`}>
              {s.name}
            </button>
          ))}
        </div>
        <button onClick={() => runCompare(selected)} disabled={selected.length < 2 || loading}
          className="mt-4 px-6 py-2.5 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-semibold rounded-xl shadow hover:shadow-lg transition disabled:opacity-50">
          {loading ? 'Comparing…' : 'Compare →'}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-6">{error}</div>}

      {/* Comparison Table */}
      {results.length >= 2 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] border-collapse">
            <thead>
              <tr>
                <th className="text-left p-4 bg-gray-50 rounded-tl-xl font-semibold text-gray-600 text-sm w-32">Field</th>
                {results.map((s) => (
                  <th key={s.id} className="p-4 bg-blue-50 text-left font-bold text-[#0F52BA] text-sm">
                    <Link href={`/schemes/${s.id}`} className="hover:underline">{s.name}</Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, ri) => (
                <tr key={row.key} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50/60'}>
                  <td className="p-4 text-sm font-medium text-gray-500 align-top">{row.label}</td>
                  {results.map((s) => {
                    const val = s[row.key as keyof Scheme];
                    const display = 'format' in row ? (row as { format: (v: unknown) => string }).format(val) : val != null ? String(val) : '–';
                    return (
                      <td key={s.id} className="p-4 text-sm text-gray-800 align-top max-w-xs">
                        {row.key === 'benefits' ? (
                          <span className="text-emerald-700 text-xs">{String(val ?? '–')}</span>
                        ) : display}
                      </td>
                    );
                  })}
                </tr>
              ))}
              {/* Apply row */}
              <tr className="bg-white">
                <td className="p-4 text-sm font-medium text-gray-500">Apply</td>
                {results.map((s) => (
                  <td key={s.id} className="p-4">
                    {s.application_url ? (
                      <a href={s.application_url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex px-3 py-1.5 bg-[#0F52BA] text-white text-xs rounded-xl hover:bg-[#0d48a8] transition">
                        Apply →
                      </a>
                    ) : '–'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-10 animate-fadeIn">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Compare Schemes</h1>
        <p className="text-gray-500 mt-1">Compare up to 3 schemes side by side</p>
      </div>
      <Suspense fallback={<div className="py-12 text-center text-gray-400">Loading…</div>}>
        <CompareContent />
      </Suspense>
    </div>
  );
}
