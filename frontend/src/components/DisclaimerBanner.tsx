import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <header
      role="region"
      aria-label="Regulatory Compliance Disclaimer"
      className="h-[44px] shrink-0 w-full bg-[rgba(245,158,11,0.08)] border-b border-[rgba(245,158,11,0.22)] px-4 flex items-center justify-between z-30 text-xs"
    >
      <div className="flex items-center gap-2 text-amber-300 font-medium tracking-tight">
        <span className="flex items-center justify-center w-5 h-5 rounded bg-amber-500/20 text-amber-400 shrink-0">
          <AlertTriangle className="w-3.5 h-3.5" />
        </span>
        <span className="text-amber-200/90 font-semibold text-[11px] sm:text-xs">
          <strong className="text-amber-400 font-bold uppercase tracking-wider text-[10px] sm:text-[11px] mr-1">
            Regulatory Disclaimer:
          </strong>
          Facts-only mutual fund assistant. Zero investment advice, comparisons, or recommendations provided.
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#00D09C]/10 border border-[#00D09C]/30 text-[#00D09C] text-[11px] font-medium">
          <span className="w-2 h-2 rounded-full bg-[#00D09C] pulse-dot inline-block shadow-[0_0_8px_#00D09C]"></span>
          <span>Corpus: 5 Official HDFC Schemes</span>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono border border-slate-700/60">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span>SEBI Grounded</span>
        </div>
      </div>
    </header>
  );
};
