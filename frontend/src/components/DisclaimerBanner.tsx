import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div
      role="region"
      aria-label="Regulatory Disclaimer"
      className="sticky top-0 z-50 w-full bg-[#12161A] text-white border-b border-gray-800 px-4 py-2.5 text-xs md:text-sm font-medium shadow-sm transition-all"
    >
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" aria-hidden="true" />
          <span className="text-gray-200">
            <strong className="text-white font-semibold">Regulatory Notice:</strong> Facts-only Mutual Fund FAQ Assistant. Strictly zero investment advice, return projections, or scheme recommendations.
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 bg-[#1E242B] border border-gray-700/60 px-2.5 py-0.5 rounded-full text-xs text-gray-300">
          <ShieldCheck className="w-3.5 h-3.5 text-[#00D09C]" aria-hidden="true" />
          <span>HDFC Mutual Fund (5 Schemes)</span>
        </div>
      </div>
    </div>
  );
};
