import React, { useState } from 'react';
import { ArrowRight, HelpCircle, X } from 'lucide-react';
import { useDialogA11y } from '../lib/useDialogA11y';
import { useChatStore } from '../store/useChatStore';
import { fundHouseNames } from '../lib/schemes';

const CATEGORY_TAGS = ['Exit Rules', 'Investment Minimums', 'Fund Norms'];
const WELCOME_KEY = 'fundfacts.welcomeDismissed';

export const StarterQuestions: React.FC = () => {
  const { meta, sendUserMessage, isSending, setAboutModalOpen } =
    useChatStore();

  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [showWelcome, setShowWelcome] = useState(() => {
    try {
      return localStorage.getItem(WELCOME_KEY) !== '1';
    } catch {
      return true;
    }
  });
  const dismissWelcome = () => {
    setShowWelcome(false);
    try {
      localStorage.setItem(WELCOME_KEY, '1');
    } catch {
      /* private mode: the banner just comes back next visit */
    }
  };
  const guideRef = useDialogA11y(isGuideOpen, () => setIsGuideOpen(false));

  const starterQuestions = meta?.starter_questions || [
    'What is the exit load for HDFC Mid-Cap Opportunities Fund?',
    'What is the minimum SIP amount for HDFC Small Cap Fund?',
    'What is the lock-in period for ELSS mutual funds?',
  ];

  const schemes = meta?.schemes || [];

  const handleQuestionClick = (question: string) => {
    if (isSending) return;
    sendUserMessage(question);
  };

  return (
    <section className="rounded-2xl p-5 sm:p-7 shadow-sm border transition-colors bg-white border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b]">
      {showWelcome && (
        <div
          role="note"
          className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-2 p-3 rounded-xl border bg-teal-50 border-[#0D9488]/20 text-[13px] text-[#0F172A] dark:bg-[#22282c] dark:border-[#6ee7b7]/30 dark:text-[#f1f5f9]"
        >
          <span className="flex-1 min-w-[200px]">
            <strong>New here?</strong> This assistant answers factual questions only. It won&apos;t recommend funds.
          </span>
          <button
            type="button"
            onClick={() => setAboutModalOpen(true)}
            className="min-h-[44px] px-2 font-semibold text-[#0D9488] dark:text-[#6ee7b7] hover:underline cursor-pointer"
          >
            Learn more
          </button>
          <button
            type="button"
            onClick={dismissWelcome}
            className="min-h-[44px] px-4 rounded-lg font-semibold cursor-pointer bg-[#0D9488] text-white hover:bg-[#0F766E]"
          >
            Got it
          </button>
        </div>
      )}
      {/* Title & Subtitle */}
      <div className="flex flex-col gap-1.5 mb-6">
        <h1 className="text-[22px] sm:text-[26px] font-bold text-[#0F172A] dark:text-[#f1f5f9] tracking-tight">
          {schemes.length > 0
            ? `Ask facts about ${schemes.length} ${fundHouseNames(schemes) || 'mutual fund'} schemes`
            : 'Ask facts about mutual fund schemes'}
        </h1>
        <p className="text-[14px] sm:text-[15px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
          Expense ratio, exit load, minimum SIP, riskometer, benchmark and more, each with its
          source and date. Pick a scheme above or try a question below.
        </p>
      </div>

      {/* 3 Starter Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mb-4">
        {starterQuestions.slice(0, 3).map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleQuestionClick(q)}
            disabled={isSending}
            className="text-left p-4 rounded-xl transition-all flex flex-col justify-between gap-3 group border cursor-pointer min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] hover:bg-[#F1F5F9] dark:bg-[#22282c] dark:border-[#2d353b] dark:hover:bg-[#2d353b] disabled:opacity-50"
            type="button"
          >
            <span className="text-[14px] text-[#0F172A] dark:text-[#f1f5f9] group-hover:text-[#0D9488] dark:group-hover:text-[#6ee7b7] transition-colors leading-snug">
              &ldquo;{q}&rdquo;
            </span>
            <div className="flex items-center justify-between text-[13px] pt-1 text-[#64748B] dark:text-[#94a3b8]">
              <span>{CATEGORY_TAGS[idx]}</span>
              <ArrowRight className="w-4 h-4 text-[#0D9488] dark:text-[#6ee7b7] group-hover:translate-x-0.5 transition-transform" />
            </div>
          </button>
        ))}
      </div>

      {/* "What can I ask?" trigger link */}
      <div className="flex items-center justify-start pt-1">
        <button
          onClick={() => setIsGuideOpen(true)}
          className="min-h-[44px] text-[13px] font-semibold text-[#0D9488] dark:text-[#6ee7b7] hover:underline inline-flex items-center gap-1.5 cursor-pointer"
          type="button"
        >
          <HelpCircle className="w-4 h-4" />
          <span>What can I ask?</span>
        </button>
      </div>

      {/* "What can I ask?" Guidance Dialog */}
      {isGuideOpen && (
        <div
          ref={guideRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="guide-dialog-title"
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in"
          onClick={() => setIsGuideOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl p-6 shadow-2xl relative border bg-white border-[#E2E8F0] dark:bg-[#22282c] dark:border-[#2d353b]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0] dark:border-[#2d353b]">
              <h2 id="guide-dialog-title" className="text-[16px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
                Supported Factual Queries
              </h2>
              <button
                onClick={() => setIsGuideOpen(false)}
                aria-label="Close guidance dialog"
                className="w-11 h-11 flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#f1f5f9] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-3 text-[13px] space-y-2.5 text-[#475569] dark:text-[#94a3b8]">
              <p>
                You can ask exact factual questions about any of the {schemes.length ? `${schemes.length} ` : ''}indexed {fundHouseNames(schemes)} schemes:
              </p>
              <ul className="list-disc list-inside space-y-1 text-[#0F172A] dark:text-[#f1f5f9] pl-1 font-medium">
                <li>Total Expense Ratio (TER - Direct Growth)</li>
                <li>Exit load rates and holding period conditions</li>
                <li>Minimum monthly SIP &amp; minimum lumpsum amounts</li>
                <li>Lock-in periods (e.g. ELSS tax saving funds)</li>
                <li>SEBI Riskometer tier classifications</li>
                <li>Benchmark indices and primary lead fund managers</li>
                <li>Latest daily Net Asset Value (NAV) and fund AUM</li>
              </ul>
              <p className="text-[13px] pt-1 text-[#92400E] dark:text-[#fcd34d]">
                <strong>Compliance note:</strong> We cannot recommend funds, predict future returns, or evaluate personal portfolio allocation.
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
