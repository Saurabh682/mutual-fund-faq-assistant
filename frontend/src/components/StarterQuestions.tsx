import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

const SCHEME_LIST = [
  { id: 'hdfc_midcap_dg', name: 'HDFC Mid-Cap Opportunities' },
  { id: 'hdfc_smallcap_dg', name: 'HDFC Small Cap Fund' },
  { id: 'hdfc_largecap_dg', name: 'HDFC Top 100 Fund' },
  { id: 'hdfc_silver_fof_dg', name: 'HDFC Silver ETF FoF' },
  { id: 'hdfc_multicap_dg', name: 'HDFC Multi Cap Fund' },
];

export const StarterQuestions: React.FC = () => {
  const { sendUserMessage, isSending } = useChatStore();

  const handleSelect = (question: string) => {
    if (!isSending) {
      sendUserMessage(question);
    }
  };

  return (
    <div className="bg-[#1A2027] border border-[#28323E] rounded-2xl p-5 md:p-6 shadow-xl relative overflow-hidden my-4">
      <div className="absolute -right-16 -top-16 w-48 h-48 bg-[#00D09C]/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-md bg-[#00D09C]/15 text-[#00D09C] border border-[#00D09C]/30 text-[11px] font-bold tracking-wide uppercase">
              Official Facts Engine
            </span>
            <span className="text-xs text-slate-400">• Verified AMC Data</span>
          </div>
          <h1 className="text-lg md:text-xl font-bold text-white tracking-tight">
            Official HDFC Mutual Fund Facts Assistant
          </h1>
          <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Fast, verified answers grounded strictly in Groww and AMC scheme records. No advice, no speculation, zero algorithmic portfolio predictions.
          </p>
        </div>
        <div className="hidden sm:flex shrink-0 w-12 h-12 rounded-2xl bg-[#12161A] border border-[#28323E] items-center justify-center text-[#00D09C] shadow-inner">
          <ShieldCheck className="w-6 h-6" />
        </div>
      </div>

      {/* Scheme Scope Pills (5 items) */}
      <div className="mt-4 pt-4 border-t border-[#28323E]/80">
        <div className="text-[11px] font-semibold text-slate-400 mb-2.5 flex items-center gap-1.5">
          <span>Active Knowledge Base (5 Ingested Schemes):</span>
          <span className="text-[10px] text-slate-500 font-mono">(Direct &amp; Regular Plans)</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {SCHEME_LIST.map((scheme, idx) => (
            <button
              key={scheme.id}
              onClick={() => handleSelect(`What is the expense ratio and exit load of ${scheme.name}?`)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
                idx === 0
                  ? 'bg-[#00D09C]/10 border border-[#00D09C]/40 text-[#00D09C] hover:bg-[#00D09C]/20 shadow-xs'
                  : 'bg-[#12161A] hover:bg-[#202832] border border-[#28323E] text-slate-300 hover:border-slate-500'
              }`}
            >
              {idx === 0 && <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span>}
              <span>{scheme.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 3 Clickable Starter Question Cards */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2.5">
        <div
          onClick={() => handleSelect('What is the exit load for HDFC Mid-Cap Opportunities Fund?')}
          className="group bg-[#12161A]/80 hover:bg-[#12161A] border border-[#28323E] hover:border-[#00D09C]/60 rounded-xl p-3 cursor-pointer transition flex flex-col justify-between"
        >
          <span className="text-xs text-slate-200 group-hover:text-white leading-snug">
            "What is the exit load for HDFC Mid-Cap Opportunities Fund?"
          </span>
          <span className="text-[10px] text-[#00D09C] font-semibold mt-2 flex items-center gap-1">
            Ask fact → <span className="text-slate-500 font-mono text-[9px]">(Exit rules)</span>
          </span>
        </div>

        <div
          onClick={() => handleSelect('What is the minimum SIP amount for HDFC Small Cap Fund?')}
          className="group bg-[#12161A]/80 hover:bg-[#12161A] border border-[#28323E] hover:border-[#00D09C]/60 rounded-xl p-3 cursor-pointer transition flex flex-col justify-between"
        >
          <span className="text-xs text-slate-200 group-hover:text-white leading-snug">
            "What is the minimum SIP amount for HDFC Small Cap Fund?"
          </span>
          <span className="text-[10px] text-[#00D09C] font-semibold mt-2 flex items-center gap-1">
            Ask fact → <span className="text-slate-500 font-mono text-[9px]">(SIP thresholds)</span>
          </span>
        </div>

        <div
          onClick={() => handleSelect('How do I redeem my mutual fund units on Groww?')}
          className="group bg-[#12161A]/80 hover:bg-[#12161A] border border-[#28323E] hover:border-[#00D09C]/60 rounded-xl p-3 cursor-pointer transition flex flex-col justify-between"
        >
          <span className="text-xs text-slate-200 group-hover:text-white leading-snug">
            "How do I redeem my mutual fund units on Groww?"
          </span>
          <span className="text-[10px] text-[#00D09C] font-semibold mt-2 flex items-center gap-1">
            Ask fact → <span className="text-slate-500 font-mono text-[9px]">(Settlement timeline)</span>
          </span>
        </div>
      </div>
    </div>
  );
};
