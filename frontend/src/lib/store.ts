'use client';

/**
 * JanMitra – Local profile storage (guest mode)
 *
 * Stores user profile in localStorage for hackathon demo.
 * Can be replaced with auth-backed storage later.
 */

import { OnboardingData, UserProfile } from '@/types';

const PROFILE_KEY = 'janmitra_profile';
const USER_ID_KEY = 'janmitra_user_id';

export function getStoredProfile(): OnboardingData | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredProfile(profile: OnboardingData): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function getStoredUserId(): number | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_ID_KEY);
  return raw ? parseInt(raw, 10) : null;
}

export function setStoredUserId(id: number): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_ID_KEY, id.toString());
}

export function clearStoredProfile(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(PROFILE_KEY);
  localStorage.removeItem(USER_ID_KEY);
}

export function isProfileComplete(profile: OnboardingData | null): boolean {
  if (!profile) return false;
  return !!(profile.age && profile.gender && profile.state && profile.occupation);
}
