import React, { useState } from 'react';
import { ArrowUp, ShieldAlert } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

const PII_WARNING_PATTERN = /\b([a-zA-Z]{5}\s*\d{4}\s*[a-zA-Z]|\d{4}[\s-]?\d{4}[\s-]?\d{4}|folio|otp|password|bank account|ifsc)\b/i;

export const Composer: React.FC = () => {
  const [text, setText] = useState('');
  const { sendUserMessage, isSending } = useChatStore();

  const hasPiiWarning = PII_WARNING_PATTERN.test(text);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isSending) return;
    sendUserMessage(text);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 shrink-0">
      {/* Soft Client PII Warning */}
      {hasPiiWarning && (
        <div className="mb-2 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 flex items-center gap-2 text-xs text-amber-800 dark:text-amber-200 animate-fadeIn">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>
            Security reminder: Do not submit personal PAN, Aadhaar, account numbers, or credentials.
          </span>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="relative bg-white dark:bg-[#1E242B] border border-gray-200 dark:border-gray-700/80 rounded-2xl shadow-sm focus-within:border-[#00b386] focus-within:ring-1 focus-within:ring-[#00b386] transition-all p-2"
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, 500))}
          onKeyDown={handleKeyDown}
          placeholder="Ask a factual question about HDFC Mutual Fund schemes..."
          rows={2}
          className="w-full resize-none bg-transparent text-sm md:text-base text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none px-2 py-1"
          aria-label="User query input"
        />

        <div className="flex items-center justify-between pt-1 px-1 border-t border-gray-100 dark:border-gray-800/60">
          <span className="text-[11px] text-gray-400 font-mono">
            {text.length}/500
          </span>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-gray-400 hidden sm:inline">
              Press Enter ↵ to send
            </span>
            <button
              type="submit"
              disabled={!text.trim() || isSending}
              className="w-8 h-8 rounded-xl bg-[#00b386] hover:bg-[#00d09c] disabled:opacity-40 text-white flex items-center justify-center transition shadow-xs cursor-pointer disabled:cursor-not-allowed"
              aria-label="Send message"
            >
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
