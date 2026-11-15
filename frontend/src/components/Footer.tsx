import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full px-4 sm:px-6 py-3 border-t transition-colors bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#09100d] dark:border-[#1a231f] shrink-0">
      <div className="max-w-7xl mx-auto flex items-center justify-center sm:justify-between text-[13px] leading-relaxed text-center sm:text-left text-[#64748B] dark:text-[#94a3b8]">
        <span>
          Source: Groww scheme pages. Independent project, not affiliated with Groww or any fund house.
          Not investment advice.
        </span>
      </div>
    </footer>
  );
};
