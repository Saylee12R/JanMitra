'use client';
import { useState, useRef, useEffect } from 'react';
import { ChatResponse } from '@/types';
import { chatWithAssistant } from '@/lib/api';
import { getStoredProfile, getStoredUserId } from '@/lib/store';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  disclaimer?: string;
  timestamp: Date;
}

const SAMPLE_QUESTIONS = [
  'What is PM-KISAN? Am I eligible as a farmer?',
  'Which scholarships are available for college students?',
  'What health schemes are available for BPL families?',
  'How do I apply for Ayushman Bharat?',
  'What documents are needed for PM Ujjwala Yojana?',
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm JanMitra Assistant. I can help you understand government schemes, eligibility criteria, required documents, and application procedures.\n\n⚠️ I only answer questions about government schemes — not unrelated topics. All my answers are based on official government data.",
      timestamp: new Date(0), // stable initial value; updated in useEffect
    },
  ]);

  // Fix: update initial timestamp client-side to avoid prerender error
  useEffect(() => {
    setMessages((prev) => [{ ...prev[0], timestamp: new Date() }, ...prev.slice(1)]);
  }, []);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);
  const userId = getStoredUserId() || 1;
  const profile = getStoredProfile();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');

    const userMsg: Message = { role: 'user', content: msg, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res: ChatResponse = await chatWithAssistant({
        user_id: userId,
        conversation_id: conversationId,
        message: msg,
        user_profile: profile || undefined,
      });
      setConversationId(res.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          sources: res.sources,
          disclaimer: res.disclaimer,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I encountered an error connecting to the backend. Please make sure the JanMitra backend is running on port 8000.',
          timestamp: new Date(),
        },
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 flex flex-col animate-fadeIn" style={{ minHeight: 'calc(100vh - 130px)' }}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">JanMitra Assistant</h1>
        <p className="text-gray-500 mt-1">Ask anything about government schemes — powered by Gemini AI</p>
      </div>

      {/* Sample questions */}
      {messages.length <= 1 && (
        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUESTIONS.map((q) => (
              <button key={q} onClick={() => send(q)}
                className="px-3 py-1.5 text-xs bg-blue-50 text-[#0F52BA] rounded-xl border border-blue-100 hover:bg-blue-100 transition">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 space-y-4 mb-4 overflow-y-auto max-h-[60vh] pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-1' : 'order-0'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#0F52BA] to-[#10B981] flex items-center justify-center text-white text-xs font-bold">J</div>
                  <span className="text-xs text-gray-400">JanMitra Assistant</span>
                </div>
              )}
              <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-[#0F52BA] to-[#10B981] text-white rounded-tr-sm'
                  : 'bg-white border border-gray-100 text-gray-800 shadow-sm rounded-tl-sm'
              }`}>
                {msg.content}
              </div>
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {msg.sources.map((src, si) => (
                    <a key={si} href={src} target="_blank" rel="noopener noreferrer"
                      className="text-xs px-2 py-0.5 bg-gray-50 border border-gray-200 rounded-lg text-gray-500 hover:text-[#0F52BA] transition">
                      🔗 Source {si + 1}
                    </a>
                  ))}
                </div>
              )}
              {/* Disclaimer */}
              {msg.disclaimer && (
                <p className="mt-1 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100">{msg.disclaimer}</p>
              )}
              <p className="text-xs text-gray-300 mt-1 text-right">{msg.timestamp.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="glass-card p-3 flex gap-2 sticky bottom-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about any government scheme…"
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-xl text-sm bg-gray-50 border border-gray-200 focus:ring-2 focus:ring-blue-500 outline-none transition"
        />
        <button onClick={() => send()} disabled={!input.trim() || loading}
          className="px-4 py-2.5 bg-gradient-to-r from-[#0F52BA] to-[#10B981] text-white rounded-xl font-semibold text-sm hover:shadow-lg transition disabled:opacity-50">
          Send
        </button>
      </div>
    </div>
  );
}
