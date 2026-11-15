import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Lock } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const Composer: React.FC = () => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendUserMessage, isSending } = useChatStore();

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;
    sendUserMessage(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  // Auto-resize textarea height
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
    }
  }, [text]);

  const charCount = text.length;
  const isTooLong = charCount > 1000;

  return (
    <div className="w-full rounded-2xl p-3 sm:p-4 shadow-lg sticky bottom-2 z-20 border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b]">
      {/* Textarea container */}
      <div className="relative rounded-xl p-3 transition-colors bg-[#F8FAFC] border border-[#E2E8F0] focus-within:border-[#0D9488] dark:bg-[#22282c] dark:border-[#2d353b] dark:focus-within:bg-[#2d353b]">
        <label htmlFor="chat-textarea" className="sr-only">
          Ask a factual question about mutual funds
        </label>
        <textarea
          id="chat-textarea"
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={1000}
          rows={2}
          placeholder="Ask about TER, exit load, minimum SIP, benchmark, or riskometer..."
          className="w-full bg-transparent resize-none text-[14px] sm:text-[15px] leading-relaxed focus:outline-none placeholder:text-[#94a3b8] text-[#0F172A] dark:text-[#f1f5f9]"
        />

        {/* Action bar inside composer */}
        <div className="flex items-center justify-between pt-2">
          {/* Character counter */}
          <span
            className={`text-[13px] ${
              isTooLong
                ? 'text-red-500 font-bold'
                : 'text-[#64748B] dark:text-[#94a3b8]'
            }`}
          >
            {charCount} / 1000
          </span>

          <div className="flex items-center gap-2">
            {/* Clear button */}
            {charCount > 0 && (
              <button
                onClick={handleClear}
                className="min-h-[44px] px-3 py-1.5 text-[13px] font-medium text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#f1f5f9] rounded-lg transition-colors cursor-pointer"
                type="button"
              >
                Clear
              </button>
            )}

            {/* Send button */}
            <button
              onClick={handleSend}
              disabled={!text.trim() || isSending || isTooLong}
              className="min-h-[44px] min-w-[44px] rounded-xl flex items-center justify-center shadow-xs transition-all cursor-pointer bg-[#0D9488] text-white hover:bg-[#0F766E] disabled:opacity-40 disabled:cursor-not-allowed dark:bg-[#6ee7b7] dark:text-[#132e27] dark:hover:bg-[#6ee7b7]"
              type="button"
              aria-label="Send message"
            >
              <ArrowUp className="w-5 h-5 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>

      {/* Subtext info row */}
      <div className="px-1 pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 text-[13px] text-[#64748B] dark:text-[#94a3b8]">
        <div className="flex items-center gap-1.5 min-w-0">
          <Lock className="w-3.5 h-3.5 text-[#B45309] dark:text-[#fcd34d] shrink-0" />
          <span className="truncate">
            Do not share PAN, Aadhaar, folio numbers, OTPs, or banking PINs.
          </span>
        </div>
        <span className="hidden sm:inline text-right shrink-0">Press Enter ↵ to search facts</span>
      </div>
    </div>
  );
};
