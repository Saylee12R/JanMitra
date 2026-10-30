'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { INDIAN_STATES, OCCUPATIONS, EDUCATION_LEVELS, SOCIAL_CATEGORIES, GENDERS, MARITAL_STATUSES, OnboardingData } from '@/types';
import { setStoredProfile, setStoredUserId } from '@/lib/store';
import { createUser } from '@/lib/api';

const TOTAL_STEPS = 10;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<OnboardingData>({});

  const update = (key: keyof OnboardingData, value: unknown) => {
    setData((prev) => ({ ...prev, [key]: value }));
  };

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  const back = () => setStep((s) => Math.max(s - 1, 1));
  const skip = () => next();

  const finish = async () => {
    setLoading(true);
    try {
      setStoredProfile(data);
      const user = await createUser(data as Record<string, unknown>);
      if (user && typeof user === 'object' && 'id' in user) {
        setStoredUserId((user as { id: number }).id);
      }
    } catch {
      // Guest mode — store locally even if backend is down
      setStoredProfile(data);
    }
    setLoading(false);
    router.push('/recommendations');
  };

  const progress = (step / TOTAL_STEPS) * 100;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-10 animate-fadeIn">
      {/* Progress */}
      <div className="w-full max-w-md mb-8">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Step {step} of {TOTAL_STEPS}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Step Card */}
      <div className="step-card animate-slideUp">
        {step === 1 && (
          <StepContent title="How old are you?" subtitle="This helps match age-specific schemes">
            <input
              type="number"
              min={1} max={120}
              value={data.age || ''}
              onChange={(e) => update('age', parseInt(e.target.value) || undefined)}
              placeholder="Enter your age"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
            />
          </StepContent>
        )}
        {step === 2 && (
          <StepContent title="What is your gender?" subtitle="Some schemes are designed for specific genders">
            <div className="grid grid-cols-3 gap-3">
              {GENDERS.map((g) => (
                <button key={g} onClick={() => update('gender', g.toLowerCase())}
                  className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${data.gender === g.toLowerCase() ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                  {g}
                </button>
              ))}
            </div>
          </StepContent>
        )}
        {step === 3 && (
          <StepContent title="Which state do you live in?" subtitle="For state-specific schemes">
            <select value={data.state || ''} onChange={(e) => update('state', e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 outline-none">
              <option value="">Select state</option>
              {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </StepContent>
        )}
        {step === 4 && (
          <StepContent title="Which district?" subtitle="Optional — helps with local schemes">
            <input type="text" value={data.district || ''} onChange={(e) => update('district', e.target.value)}
              placeholder="Enter your district" className="w-full px-4 py-3 border border-gray-200 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 outline-none" />
          </StepContent>
        )}
        {step === 5 && (
          <StepContent title="What is your occupation?" subtitle="Many schemes target specific occupations">
            <div className="grid grid-cols-2 gap-2">
              {OCCUPATIONS.map((o) => (
                <button key={o} onClick={() => update('occupation', o.toLowerCase())}
                  className={`px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${data.occupation === o.toLowerCase() ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                  {o}
                </button>
              ))}
            </div>
          </StepContent>
        )}
        {step === 6 && (
          <StepContent title="What is your annual income?" subtitle="Income limits apply to many schemes">
            <input type="number" min={0} value={data.annual_income || ''} onChange={(e) => update('annual_income', parseFloat(e.target.value) || undefined)}
              placeholder="Annual income in ₹" className="w-full px-4 py-3 border border-gray-200 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 outline-none" />
            <p className="text-xs text-gray-400 mt-2">Enter approximate total annual family income in Rupees</p>
          </StepContent>
        )}
        {step === 7 && (
          <StepContent title="Social category" subtitle="Several schemes are for specific categories">
            <div className="grid grid-cols-3 gap-3">
              {SOCIAL_CATEGORIES.map((c) => (
                <button key={c} onClick={() => update('category', c)}
                  className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${data.category === c ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                  {c}
                </button>
              ))}
            </div>
          </StepContent>
        )}
        {step === 8 && (
          <StepContent title="Education level" subtitle="For scholarship and education schemes">
            <div className="grid grid-cols-2 gap-2">
              {EDUCATION_LEVELS.map((e) => (
                <button key={e} onClick={() => update('education', e.toLowerCase())}
                  className={`px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${data.education === e.toLowerCase() ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                  {e}
                </button>
              ))}
            </div>
          </StepContent>
        )}
        {step === 9 && (
          <StepContent title="Marital status" subtitle="Some schemes are for specific marital statuses">
            <div className="grid grid-cols-2 gap-3">
              {MARITAL_STATUSES.map((m) => (
                <button key={m} onClick={() => update('marital_status', m.toLowerCase())}
                  className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${data.marital_status === m.toLowerCase() ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                  {m}
                </button>
              ))}
            </div>
          </StepContent>
        )}
        {step === 10 && (
          <StepContent title="Do you have a disability?" subtitle="Several schemes support persons with disabilities">
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => update('disability', true)}
                className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${data.disability === true ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                Yes
              </button>
              <button onClick={() => update('disability', false)}
                className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${data.disability === false ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                No
              </button>
            </div>
          </StepContent>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-100">
          <button onClick={back} disabled={step === 1}
            className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition">
            ← Back
          </button>
          <div className="flex gap-2">
            {step < TOTAL_STEPS && (
              <button onClick={skip} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-600 transition">
                Skip
              </button>
            )}
            {step < TOTAL_STEPS ? (
              <button onClick={next}
                className="px-6 py-2.5 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-semibold rounded-xl shadow hover:shadow-lg transition-all hover:scale-[1.02]">
                Next →
              </button>
            ) : (
              <button onClick={finish} disabled={loading}
                className="px-6 py-2.5 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white font-semibold rounded-xl shadow hover:shadow-lg transition-all hover:scale-[1.02] disabled:opacity-50">
                {loading ? 'Processing...' : 'Find My Schemes →'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepContent({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-1">{title}</h2>
      <p className="text-sm text-gray-500 mb-6">{subtitle}</p>
      {children}
    </div>
  );
}
