/**
 * JanMitra – API Client
 *
 * All backend API calls go through this module.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Health ────────────────────────────────────────
export async function getHealth() {
  return apiFetch<{ status: string; ai_available: boolean; version: string }>('/api/health');
}

// ── Users ─────────────────────────────────────────
export async function createUser(data: Record<string, unknown>) {
  return apiFetch('/api/users', { method: 'POST', body: JSON.stringify(data) });
}

export async function getUser(id: number) {
  return apiFetch(`/api/users/${id}`);
}

export async function updateUser(id: number, data: Record<string, unknown>) {
  return apiFetch(`/api/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

// ── Schemes ───────────────────────────────────────
export async function getSchemes(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return apiFetch<import('@/types').SchemeListItem[]>(`/api/schemes${qs}`);
}

export async function getScheme(id: number) {
  return apiFetch<import('@/types').Scheme>(`/api/schemes/${id}`);
}

// ── Recommendations ───────────────────────────────
export async function getRecommendations(profile: Record<string, unknown>) {
  return apiFetch<import('@/types').RecommendationResponse>('/api/recommend', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

// ── Saved Schemes ─────────────────────────────────
export async function getSavedSchemes(userId: number) {
  return apiFetch<import('@/types').SavedScheme[]>(`/api/saved?user_id=${userId}`);
}

export async function saveScheme(schemeId: number, userId: number) {
  return apiFetch(`/api/saved/${schemeId}?user_id=${userId}`, { method: 'POST' });
}

export async function removeSavedScheme(schemeId: number, userId: number) {
  return apiFetch(`/api/saved/${schemeId}?user_id=${userId}`, { method: 'DELETE' });
}

// ── Applications ──────────────────────────────────
export async function getApplications(userId: number) {
  return apiFetch<import('@/types').Application[]>(`/api/applications?user_id=${userId}`);
}

export async function createApplication(userId: number, data: { scheme_id: number; status?: string }) {
  return apiFetch(`/api/applications?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateApplication(appId: number, userId: number, data: Record<string, unknown>) {
  return apiFetch(`/api/applications/${appId}?user_id=${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ── Checklist ─────────────────────────────────────
export async function getChecklist(schemeId: number, userId: number) {
  return apiFetch<import('@/types').ChecklistResponse>(`/api/checklist/${schemeId}?user_id=${userId}`);
}

export async function createChecklistItem(schemeId: number, userId: number, data: { title: string; order?: number }) {
  return apiFetch(`/api/checklist/${schemeId}?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateChecklistItem(itemId: number, userId: number, data: { completed?: boolean }) {
  return apiFetch(`/api/checklist/${itemId}?user_id=${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ── Compare ───────────────────────────────────────
export async function compareSchemes(schemeIds: number[]) {
  return apiFetch<{ schemes: import('@/types').Scheme[] }>('/api/compare', {
    method: 'POST',
    body: JSON.stringify({ scheme_ids: schemeIds }),
  });
}

// ── AI Assistant ──────────────────────────────────
export async function chatWithAssistant(data: import('@/types').ChatRequest) {
  return apiFetch<import('@/types').ChatResponse>('/api/assistant/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
