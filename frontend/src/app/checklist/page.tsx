'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ChecklistResponse, ChecklistItem } from '@/types';
import { getChecklist, updateChecklistItem, createChecklistItem, getSavedSchemes } from '@/lib/api';
import { getStoredUserId } from '@/lib/store';

function ChecklistContent() {
  const searchParams = useSearchParams();
  const schemeIdParam = searchParams.get('scheme_id');
  const [schemeId, setSchemeId] = useState<number | null>(schemeIdParam ? parseInt(schemeIdParam) : null);
  const [data, setData] = useState<ChecklistResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [savedSchemes, setSavedSchemes] = useState<{ scheme_id: number; scheme: { name: string } }[]>([]);
  const [newItem, setNewItem] = useState('');
  const [adding, setAdding] = useState(false);
  const userId = getStoredUserId() || 1;

  useEffect(() => {
    getSavedSchemes(userId).then((s) => setSavedSchemes(s as never)).catch(() => {});
  }, [userId]);

  useEffect(() => {
    if (!schemeId) return;
    setLoading(true);
    getChecklist(schemeId, userId)
      .then(setData)
      .catch(() => setError('Could not load checklist.'))
      .finally(() => setLoading(false));
  }, [schemeId, userId]);

  const toggleItem = async (item: ChecklistItem) => {
    try {
      await updateChecklistItem(item.id, userId, { completed: !item.completed });
      setData((prev) => {
        if (!prev) return prev;
        const updated = prev.items.map((i) =>
          i.id === item.id ? { ...i, completed: !i.completed } : i
        );
        const completed = updated.filter((i) => i.completed).length;
        return {
          ...prev,
          items: updated,
          completed,
          progress_percent: Math.round((completed / updated.length) * 100),
        };
      });
    } catch { /* swallow */ }
  };

  const addItem = async () => {
    if (!newItem.trim() || !schemeId) return;
    setAdding(true);
    try {
      const item = await createChecklistItem(schemeId, userId, { title: newItem.trim() });
      setData((prev) => {
        if (!prev) return prev;
        return { ...prev, items: [...prev.items, item as ChecklistItem], total: prev.total + 1 };
      });
      setNewItem('');
    } catch { /* swallow */ }
    setAdding(false);
  };

  if (!schemeId) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">📋</div>
        <h2 className="text-xl font-bold mb-3">Select a scheme to manage your checklist</h2>
        {savedSchemes.length > 0 ? (
          <div className="mt-6 max-w-sm mx-auto space-y-2">
            {savedSchemes.map((s) => (
              <button key={s.scheme_id} onClick={() => setSchemeId(s.scheme_id)}
                className="w-full px-4 py-3 glass-card text-left text-sm font-medium text-gray-800 hover:shadow-md transition">
                {s.scheme.name}
              </button>
            ))}
          </div>
        ) : (
          <div>
            <p className="text-gray-500 mb-4">Save some schemes first to start a checklist.</p>
            <Link href="/schemes" className="px-5 py-2.5 bg-[#0F52BA] text-white rounded-xl font-medium hover:bg-[#0d48a8] transition">Browse Schemes</Link>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Scheme selector */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <select value={schemeId || ''} onChange={(e) => setSchemeId(parseInt(e.target.value))}
          className="px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm bg-white flex-1 max-w-xs">
          {savedSchemes.map((s) => (
            <option key={s.scheme_id} value={s.scheme_id}>{s.scheme.name}</option>
          ))}
        </select>
        <Link href={`/schemes/${schemeId}`} className="text-sm text-[#0F52BA] hover:underline">View Scheme →</Link>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 mb-4">{error}</div>}
      {loading && (
        <div className="py-12 text-center">
          <div className="w-10 h-10 border-4 border-[#0F52BA] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-gray-400 text-sm">Loading checklist…</p>
        </div>
      )}
      {data && (
        <>
          {/* Progress */}
          <div className="glass-card p-5 mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-gray-700">{data.completed}/{data.total} items completed</span>
              <span className="font-bold text-[#0F52BA]">{data.progress_percent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${data.progress_percent}%` }} />
            </div>
            {data.progress_percent === 100 && (
              <p className="text-emerald-600 text-sm font-medium mt-2">🎉 All items complete! You're ready to apply.</p>
            )}
          </div>

          {/* Items */}
          <div className="space-y-2 mb-6">
            {data.items.map((item) => (
              <button key={item.id} onClick={() => toggleItem(item)}
                className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl border-2 text-left transition-all ${item.completed ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-gray-200 hover:border-gray-300'}`}>
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${item.completed ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-gray-300'}`}>
                  {item.completed && <span className="text-xs">✓</span>}
                </div>
                <div className="flex-1">
                  <span className={`text-sm font-medium ${item.completed ? 'line-through text-gray-400' : 'text-gray-800'}`}>{item.title}</span>
                  {item.description && <p className="text-xs text-gray-400 mt-0.5">{item.description}</p>}
                </div>
              </button>
            ))}
          </div>

          {/* Add custom item */}
          <div className="flex gap-2">
            <input value={newItem} onChange={(e) => setNewItem(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') addItem(); }}
              placeholder="Add a custom checklist item…"
              className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
            <button onClick={addItem} disabled={adding || !newItem.trim()}
              className="px-4 py-2.5 bg-[#0F52BA] text-white text-sm rounded-xl hover:bg-[#0d48a8] transition disabled:opacity-50">
              + Add
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function ChecklistPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10 animate-fadeIn">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Application Checklist</h1>
        <p className="text-gray-500 mt-1">Track documents and steps for your application</p>
      </div>
      <Suspense fallback={<div className="text-center py-12 text-gray-400">Loading…</div>}>
        <ChecklistContent />
      </Suspense>
    </div>
  );
}
