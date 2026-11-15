import React from 'react';
import { Info, X } from 'lucide-react';
import { useDialogA11y } from '../lib/useDialogA11y';
import { useChatStore } from '../store/useChatStore';
import { fundHouseNames } from '../lib/schemes';

export const AboutModal: React.FC = () => {
  const { isAboutModalOpen, setAboutModalOpen, meta } = useChatStore();
  const dialogRef = useDialogA11y(isAboutModalOpen, () => setAboutModalOpen(false));

  if (!isAboutModalOpen) return null;

  const schemeCount = meta?.schemes.length;
  const houses = fundHouseNames(meta?.schemes || []);

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-modal-title"
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
      onClick={() => setAboutModalOpen(false)}
    >
      <div
        className="w-full max-w-lg rounded-2xl p-6 shadow-2xl relative border bg-white border-[#E2E8F0] text-[#0F172A] dark:bg-[#22282c] dark:border-[#2d353b] dark:text-[#f1f5f9]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0] dark:border-[#2d353b]">
          <div className="flex items-center gap-2.5 text-[#B45309] dark:text-[#fcd34d]">
            <Info className="w-5 h-5 shrink-0" />
            <h2 id="about-modal-title" className="text-[17px] font-bold text-[#0F172A] dark:text-[#f1f5f9]">
              About FundFacts
            </h2>
          </div>
          <button
            onClick={() => setAboutModalOpen(false)}
            aria-label="Close details modal"
            className="w-11 h-11 flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#f1f5f9] hover:bg-[#F1F5F9] dark:hover:bg-[#2d353b] transition-colors cursor-pointer"
            type="button"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="py-4 space-y-3.5 text-[14px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
          <p>
            FundFacts provides objective, factual information on mutual fund schemes sourced directly from scheme pages on Groww.
          </p>
          <p className="text-[#0F172A] dark:text-[#f1f5f9] font-medium">
            This service is strictly computational and non-interpretive. It does not provide portfolio recommendations, comparison advice, or future market forecasts.
          </p>
          <div className="p-3.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#181d20] dark:border-[#2d353b]">
            <span className="text-[13px] font-semibold text-[#0D9488] dark:text-[#6ee7b7] uppercase tracking-wide block mb-1">
              Coverage Scope
            </span>
            <span className="text-[14px] text-[#0F172A] dark:text-[#f1f5f9]">
              Covers {schemeCount ? `${schemeCount} ` : 'the '}{houses ? `${houses} ` : ''}Direct-Growth schemes as indexed in the snapshot catalog.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-3">
          <button
            onClick={() => setAboutModalOpen(false)}
            className="min-h-[44px] px-5 py-2.5 rounded-xl font-semibold text-[14px] shadow-sm transition-colors bg-[#0D9488] text-white hover:bg-[#0F766E] dark:bg-[#6ee7b7] dark:text-[#132e27] dark:hover:bg-[#6ee7b7] cursor-pointer"
            type="button"
          >
            Acknowledge &amp; Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};
