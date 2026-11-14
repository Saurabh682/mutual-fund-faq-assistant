import React, { useState } from 'react';
import { ArrowRight, HelpCircle, X } from 'lucide-react';
import { useDialogA11y } from '../lib/useDialogA11y';
import { useChatStore } from '../store/useChatStore';

const CATEGORY_TAGS = ['Exit Rules', 'Investment Minimums', 'Fund Norms'];

export const StarterQuestions: React.FC = () => {
  const { meta, selectedSchemeId, setSelectedSchemeId, sendUserMessage, isSending } =
    useChatStore();

  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const guideRef = useDialogA11y(isGuideOpen, () => setIsGuideOpen(false));

  const starterQuestions = meta?.starter_questions || [
    'What is the exit load for HDFC Mid-Cap Opportunities Fund?',
    'What is the minimum SIP amount for HDFC Small Cap Fund?',
    'What is the lock-in period for ELSS mutual funds?',
  ];

  const schemes = meta?.schemes || [];

  const handleChipClick = (schemeId: string) => {
    setSelectedSchemeId(schemeId);
  };

  const handleQuestionClick = (question: string) => {
    if (isSending) return;
    sendUserMessage(question);
  };

  return (
    <section className="rounded-2xl p-5 sm:p-7 shadow-sm border transition-colors bg-white border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1b2620]">
      {/* Title & Subtitle */}
      <div className="flex flex-col gap-1.5 mb-5">
        <h1 className="text-[22px] sm:text-[26px] font-bold text-[#0F172A] dark:text-[#dde4df] tracking-tight">
          {schemes.length > 0 ? `Ask facts about ${schemes.length} HDFC schemes` : 'Ask facts about HDFC schemes'}
        </h1>
        <p className="text-[14px] sm:text-[15px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
          Expense ratio, exit load, minimum SIP, riskometer, benchmark and more. Answers cite their
          source and date.
        </p>
      </div>

      {/* 5 Scheme Chips */}
      <div className="flex flex-wrap gap-2 mb-6" aria-label="Scheme quick selector">
        {schemes.map((s) => {
          const isSelected = s.id === selectedSchemeId;
          return (
            <button
              key={s.id}
              onClick={() => handleChipClick(s.id)}
              className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-[13px] font-medium flex items-center gap-2 transition-all cursor-pointer border ${
                isSelected
                  ? 'bg-emerald-50 text-[#047857] border-[#047857]/30 font-semibold dark:bg-[#2f3633] dark:text-[#dde4df] dark:border-[#10b981]/50'
                  : 'bg-[#F8FAFC] text-[#475569] border-[#E2E8F0] hover:bg-[#F1F5F9] hover:text-[#0F172A] dark:bg-[#16201b] dark:text-[#94a3b8] dark:border-[#1f2824] dark:hover:bg-[#242c28] dark:hover:text-[#dde4df]'
              }`}
              type="button"
              aria-pressed={isSelected}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isSelected ? 'bg-[#047857] dark:bg-[#10b981]' : 'bg-transparent'
                }`}
              />
              <span>{s.name.replace(' (Direct - Growth)', '').replace(' (Direct Growth)', '')}</span>
            </button>
          );
        })}
      </div>

      {/* 3 Starter Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-4">
        {starterQuestions.slice(0, 3).map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleQuestionClick(q)}
            disabled={isSending}
            className="text-left p-4 rounded-xl transition-all flex flex-col justify-between gap-3 group border cursor-pointer min-h-[44px] bg-[#F8FAFC] border-[#E2E8F0] hover:bg-[#F1F5F9] dark:bg-[#16201b] dark:border-[#1f2c25] dark:hover:bg-[#242c28] disabled:opacity-50"
            type="button"
          >
            <span className="text-[14px] text-[#0F172A] dark:text-[#dde4df] group-hover:text-[#047857] dark:group-hover:text-[#10b981] transition-colors leading-snug">
              &ldquo;{q}&rdquo;
            </span>
            <div className="flex items-center justify-between text-[13px] pt-1 text-[#64748B] dark:text-[#94a3b8]">
              <span>{CATEGORY_TAGS[idx] || 'Fund Inquiry'}</span>
              <ArrowRight className="w-4 h-4 text-[#047857] dark:text-[#10b981] group-hover:translate-x-0.5 transition-transform" />
            </div>
          </button>
        ))}
      </div>

      {/* "What can I ask?" trigger link */}
      <div className="flex items-center justify-start pt-1">
        <button
          onClick={() => setIsGuideOpen(true)}
          className="min-h-[44px] text-[13px] font-semibold text-[#047857] dark:text-[#10b981] hover:underline inline-flex items-center gap-1.5 cursor-pointer"
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
            className="w-full max-w-md rounded-2xl p-6 shadow-2xl relative border bg-white border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#2f3633]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0] dark:border-[#2f3633]">
              <h2 id="guide-dialog-title" className="text-[16px] font-bold text-[#0F172A] dark:text-[#dde4df]">
                Supported Factual Queries
              </h2>
              <button
                onClick={() => setIsGuideOpen(false)}
                aria-label="Close guidance dialog"
                className="w-11 h-11 flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#dde4df] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-3 text-[13px] space-y-2.5 text-[#475569] dark:text-[#94a3b8]">
              <p>
                You can ask exact factual questions about any of the {schemes.length ? `${schemes.length} ` : ''}indexed HDFC schemes:
              </p>
              <ul className="list-disc list-inside space-y-1 text-[#0F172A] dark:text-[#dde4df] pl-1 font-medium">
                <li>Total Expense Ratio (TER - Direct Growth)</li>
                <li>Exit load rates and holding period conditions</li>
                <li>Minimum monthly SIP &amp; minimum lumpsum amounts</li>
                <li>Lock-in periods (e.g. ELSS tax saving funds)</li>
                <li>SEBI Riskometer tier classifications</li>
                <li>Benchmark indices and primary lead fund managers</li>
                <li>Latest daily Net Asset Value (NAV) and fund AUM</li>
              </ul>
              <p className="text-[13px] pt-1 text-[#92400E] dark:text-[#ffb95f]">
                <strong>Compliance note:</strong> We cannot recommend funds, predict future returns, or evaluate personal portfolio allocation.
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
