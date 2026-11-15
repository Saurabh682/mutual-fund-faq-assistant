import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const DisclaimerBanner: React.FC = () => {
  const { setAboutModalOpen } = useChatStore();

  return (
    <div
      role="banner"
      className="w-full min-h-[38px] px-4 sm:px-6 py-1.5 flex items-center justify-between gap-3 text-[13px] border-b transition-colors bg-[#FEF3C7]/80 border-[#FDE68A] text-[#92400E] dark:bg-[#2d353b] dark:border-[#2d353b] dark:text-[#fcd34d] shrink-0 z-30"
    >
      <div className="flex items-center gap-2 min-w-0">
        <AlertTriangle className="w-4 h-4 shrink-0 text-[#B45309] dark:text-[#fcd34d]" />
        <span className="font-semibold whitespace-nowrap">Facts-only. No investment advice.</span>
        <span className="hidden md:inline text-[#92400E]/80 dark:text-[#94a3b8] truncate">
          · Independent computational mutual fund records.
        </span>
      </div>
      <button
        onClick={() => setAboutModalOpen(true)}
        className="font-semibold underline hover:text-[#78350F] dark:hover:text-[#f1f5f9] transition-colors shrink-0 min-h-[44px] min-w-[44px] inline-flex items-center justify-center cursor-pointer"
        type="button"
        aria-label="View disclaimer details"
      >
        Details
      </button>
    </div>
  );
};
