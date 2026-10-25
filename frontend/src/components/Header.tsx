import React from 'react';
import { ArrowLeftRight, ChevronDown, ExternalLink, FileText, Menu, Trash2 } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

interface Props {
  onOpenCompare: () => void;
}

const SCHEME_DISPLAY_NAMES: Record<string, string> = {
  hdfc_midcap_dg: 'HDFC Mid-Cap Opportunities Fund',
  hdfc_smallcap_dg: 'HDFC Small Cap Fund',
  hdfc_largecap_dg: 'HDFC Top 100 Fund',
  hdfc_silver_fof_dg: 'HDFC Silver ETF FoF',
  hdfc_multicap_dg: 'HDFC Multi Cap Fund',
};

export const Header: React.FC<Props> = ({ onOpenCompare }) => {
  const { toggleSidebar, activeThread, startNewThread } = useChatStore();

  const activeSchemeKey = activeThread?.last_scheme_id || 'hdfc_midcap_dg';
  const activeSchemeName = SCHEME_DISPLAY_NAMES[activeSchemeKey] || 'All 5 HDFC Schemes';

  const handleClearChat = async () => {
    if (confirm('Start a fresh conversation?')) {
      await startNewThread();
    }
  };

  return (
    <div className="h-14 border-b border-[#28323E] px-4 md:px-8 flex items-center justify-between shrink-0 bg-[#12161A]/90 backdrop-blur z-10">
      <div className="flex items-center gap-3">
        {/* Mobile Drawer button */}
        <button
          onClick={toggleSidebar}
          className="md:hidden p-1.5 rounded-lg bg-[#1A2027] border border-[#28323E] text-slate-300 hover:text-white"
          aria-label="Toggle navigation drawer"
        >
          <Menu className="w-4 h-4" />
        </button>

        {/* Active Scheme Scope Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 hidden sm:inline">Active Scope:</span>
          <div className="flex items-center gap-2 bg-[#1A2027] hover:bg-[#202832] border border-[#28323E] px-3 py-1.5 rounded-lg text-xs font-semibold text-white cursor-pointer transition shadow-sm">
            <span className="w-2 h-2 rounded-full bg-[#00D09C]"></span>
            <span className="truncate max-w-[180px] sm:max-w-none">{activeSchemeName}</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-[#28323E] rounded text-slate-300 font-mono">
              DIRECT GROWTH
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenCompare}
          className="flex items-center gap-1.5 text-xs font-semibold text-[#00D09C] bg-[#00D09C]/10 hover:bg-[#00D09C]/20 border border-[#00D09C]/40 px-3 py-1.5 rounded-lg transition shadow-sm hover:shadow-[0_0_12px_rgba(0,208,156,0.25)] cursor-pointer"
        >
          <ArrowLeftRight className="w-3.5 h-3.5 stroke-[2.2]" />
          <span>Compare Schemes</span>
          <span className="px-1.5 py-0.2 text-[9px] font-mono bg-[#00D09C]/20 text-[#00D09C] rounded border border-[#00D09C]/30 uppercase">
            Diff
          </span>
        </button>

        <a
          href="https://www.hdfcfund.com"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-[#1A2027] border border-transparent hover:border-[#28323E] transition"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>AMC Factsheet</span>
          <ExternalLink className="w-3 h-3 opacity-60" />
        </a>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-[#1A2027] border border-transparent hover:border-[#28323E] transition"
        >
          <span>API Docs</span>
          <ExternalLink className="w-3 h-3 opacity-60" />
        </a>

        <div className="h-4 w-px bg-[#28323E] mx-1 hidden sm:block"></div>

        <button
          onClick={handleClearChat}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-400 px-2 py-1.5 rounded-lg hover:bg-red-500/10 transition cursor-pointer"
          title="Clear chat and start fresh"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Clear Chat</span>
        </button>
      </div>
    </div>
  );
};
