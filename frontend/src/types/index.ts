// ─────────────────────────────────────────────
//  JanMitra Frontend – TypeScript Types
// ─────────────────────────────────────────────

export interface UserProfile {
  id?: number;
  email?: string;
  age?: number;
  gender?: string;
  state?: string;
  district?: string;
  occupation?: string;
  annual_income?: number;
  category?: string;
  education?: string;
  marital_status?: string;
  disability?: boolean;
  disability_type?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Scheme {
  id: number;
  name: string;
  slug: string;
  category: string;
  ministry?: string;
  department?: string;
  description: string;
  detailed_description?: string;
  min_age?: number;
  max_age?: number;
  income_limit?: number;
  gender?: string;
  occupation?: string[];
  category_requirement?: string[];
  state?: string[];
  education_requirement?: string[];
  disability_required?: boolean;
  marital_status_requirement?: string[];
  benefits?: string;
  documents?: string[];
  application_process?: string;
  application_url?: string;
  official_source_url?: string;
  source_name?: string;
  last_verified_at?: string;
  active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SchemeListItem {
  id: number;
  name: string;
  slug: string;
  category: string;
  ministry?: string;
  description: string;
  benefits?: string;
  application_url?: string;
  gender?: string;
  min_age?: number;
  max_age?: number;
  income_limit?: number;
  state?: string[];
  active: boolean;
}

export interface RecommendationItem {
  id: number;
  name: string;
  slug: string;
  category: string;
  ministry?: string;
  description: string;
  match_score: number;
  reasons: string[];
  benefits?: string;
  application_url?: string;
  documents?: string[];
}

export interface RecommendationResponse {
  count: number;
  profile_completeness: number;
  disclaimer: string;
  schemes: RecommendationItem[];
}

export interface SavedScheme {
  id: number;
  user_id: number;
  scheme_id: number;
  created_at: string;
  scheme: SchemeListItem;
}

export interface Application {
  id: number;
  user_id: number;
  scheme_id: number;
  status: 'interested' | 'documents_pending' | 'ready_to_apply' | 'applied' | 'completed';
  notes?: string;
  created_at: string;
  updated_at: string;
  scheme?: SchemeListItem;
}

export interface ChecklistItem {
  id: number;
  scheme_id: number;
  user_id: number;
  title: string;
  description?: string;
  completed: boolean;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ChecklistResponse {
  scheme_id: number;
  total: number;
  completed: number;
  progress_percent: number;
  items: ChecklistItem[];
}

export interface ChatRequest {
  user_id?: number;
  conversation_id?: number;
  message: string;
  user_profile?: Partial<UserProfile>;
}

export interface ChatResponse {
  conversation_id: number;
  reply: string;
  sources: string[];
  disclaimer: string;
}

export interface HealthResponse {
  status: string;
  environment: string;
  ai_available: boolean;
  version: string;
}

// ── Onboarding Steps ────────────────────────────
export interface OnboardingData {
  age?: number;
  gender?: string;
  state?: string;
  district?: string;
  occupation?: string;
  annual_income?: number;
  category?: string;
  education?: string;
  marital_status?: string;
  disability?: boolean;
}

export const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Andaman and Nicobar Islands', 'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
  'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
];

export const OCCUPATIONS = [
  'Student', 'Farmer', 'Business', 'Self-employed', 'Salaried',
  'Homemaker', 'Retired', 'Unemployed', 'Daily Wage Worker',
  'Artisan', 'Street Vendor', 'Other',
];

export const EDUCATION_LEVELS = [
  'Below 8th', '8th Pass', '10th Pass', '12th Pass',
  'Diploma', 'Undergraduate', 'Graduate', 'Post-graduate',
  'Professional', 'Doctorate',
];

export const SOCIAL_CATEGORIES = [
  'General', 'OBC', 'SC', 'ST', 'EWS',
];

export const GENDERS = ['Male', 'Female', 'Other'];

export const MARITAL_STATUSES = ['Single', 'Married', 'Divorced', 'Widowed'];

export const SCHEME_CATEGORIES = [
  'Agriculture', 'Education', 'Health', 'Housing',
  'Women Welfare', 'Social Security', 'Insurance',
  'Entrepreneurship', 'Skill Development', 'Urban Livelihood',
  'Disability Support',
];
