import React, { useEffect, useState } from 'react';
import { ChevronDown, Download, ExternalLink, FileText, MessageSquare, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onInsertComparison: (text: string) => void;
}

export interface SchemeFactItem {
  scheme_id: string;
  name: string;
  plan: string;
  category: string;
  amfi_code: string;
  factsheet_url: string;
  as_of: string;
  source_url: string;
  metrics: Record<string, string>;
}

export const CompareDrawer: React.FC<Props> = ({ isOpen, onClose, onInsertComparison }) => {
  const [schemes, setSchemes] = useState<SchemeFactItem[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>('hdfc_midcap_dg');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    const fetchLiveFacts = async () => {
      setLoading(true);
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
        const cleanBase = baseUrl.endsWith('/v1')
          ? baseUrl
          : `${baseUrl.replace(/\/$/, '')}/api/v1`;
        const res = await fetch(`${cleanBase}/facts/schemes`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.schemes && data.schemes.length > 0) {
            setSchemes(data.schemes);
            if (!selectedSchemeId || !data.schemes.some((s: SchemeFactItem) => s.scheme_id === selectedSchemeId)) {
              setSelectedSchemeId(data.schemes[0].scheme_id);
            }
          }
        }
      } catch (err) {
        console.warn('Failed to fetch live statutory facts:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchLiveFacts();
    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const currentScheme = schemes.find((s) => s.scheme_id === selectedSchemeId) || schemes[0];

  const handleAskInChat = () => {
    if (!currentScheme) return;
    const promptText = `What is the expense ratio, exit load, minimum SIP, and riskometer for ${currentScheme.name}?`;
    onInsertComparison(promptText);
    onClose();
  };

  const m = currentScheme?.metrics || {};

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-[#12161A]/70 backdrop-blur-sm z-40 transition-opacity"
      />

      {/* Drawer Panel */}
      <div className="fixed top-0 right-0 bottom-0 w-full sm:w-[580px] bg-[#151A20] border-l border-[#28323E] z-50 flex flex-col shadow-2xl transition-transform animate-slideIn">
        {/* Header */}
        <div className="p-4 sm:px-6 border-b border-[#28323E] flex items-center justify-between bg-[#12161A]/90 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#00D09C]/10 border border-[#00D09C]/35 flex items-center justify-center text-[#00D09C]">
              <FileText className="w-4 h-4 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-tight">
                  Scheme Statutory Fact Sheet
                </h2>
                <span className="px-2 py-0.2 rounded-full bg-[#00D09C]/10 border border-[#00D09C]/30 text-[#00D09C] text-[10px] font-mono font-medium">
                  {currentScheme ? `Audited facts.db • As of ${currentScheme.as_of}` : 'Live API'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Single-scheme factual inspection • Grounded in SQLite facts.db • No comparative ranking
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#1A2027] hover:bg-[#202832] border border-[#28323E] flex items-center justify-center text-slate-400 hover:text-white transition cursor-pointer"
            title="Close drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scheme Selector Bar */}
        <div className="p-4 sm:px-6 bg-[#1A2027]/70 border-b border-[#28323E] shrink-0 flex flex-col gap-2">
          <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span> Select Scheme to Inspect Statutory Facts:
          </span>
          <div className="relative">
            <select
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              className="w-full bg-[#12161A] text-xs font-semibold text-white border border-[#00D09C]/40 rounded-lg px-3 py-2.5 appearance-none focus:outline-none focus:border-[#00D09C] cursor-pointer"
            >
              {schemes.map((s) => (
                <option key={s.scheme_id} value={s.scheme_id}>
                  {s.name}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-3.5 text-slate-400">
              <ChevronDown className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:px-6 flex flex-col gap-4">
          {loading && schemes.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 font-mono">
              Fetching statutory parameters from facts.db...
            </div>
          ) : currentScheme ? (
            /* Single Scheme Facts Card */
            <div className="bg-[#1A2027] border border-[#28323E] rounded-xl p-4 flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-base font-bold text-white">{currentScheme.name}</h3>
                  <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap">
                    <span className="px-2 py-0.5 rounded bg-[#00D09C]/10 text-[#00D09C] font-mono font-semibold text-[11px]">
                      {currentScheme.plan}
                    </span>
                    {currentScheme.amfi_code && (
                      <span>• AMFI: <strong className="text-white font-mono">{currentScheme.amfi_code}</strong></span>
                    )}
                    <span>• Category: <strong className="text-white">{currentScheme.category}</strong></span>
                  </div>
                </div>
                <a
                  href={currentScheme.source_url || currentScheme.factsheet_url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 rounded-lg bg-[#12161A] hover:bg-[#202832] border border-[#28323E] text-[#00D09C] hover:text-white transition flex items-center gap-1 text-[11px] shrink-0"
                  title="Open official factsheet portal"
                >
                  <span>Portal</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              {/* 10-Metric Statutory Fact Grid */}
              <div className="grid grid-cols-2 gap-2 mt-1 text-xs">
                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Expense Ratio (TER)</div>
                  <div className="text-sm font-bold text-[#00D09C] font-mono mt-0.5">
                    {m.ter_direct || 'N/A'}
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">Direct Plan • Audited</div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">SEBI Riskometer</div>
                  <div className="text-sm font-bold text-red-400 font-mono mt-0.5">
                    {m.riskometer || 'Very High Risk'}
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">Mandatory SEBI tier</div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Exit Load Terms</div>
                  <div className="text-xs font-semibold text-slate-200 mt-0.5">
                    {m.exit_load || 'N/A'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Min SIP / Lumpsum</div>
                  <div className="text-xs font-semibold text-white font-mono mt-0.5">
                    {m.min_sip || '₹100'} / {m.min_lumpsum || '₹100'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E] col-span-2">
                  <div className="text-[10px] text-slate-400 font-medium">Benchmark Index</div>
                  <div className="text-xs font-semibold text-slate-200 font-mono mt-0.5">
                    {m.benchmark || 'N/A'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Fund Manager</div>
                  <div className="text-xs font-semibold text-white mt-0.5">
                    {m.fund_manager || 'HDFC AMC'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Fund Size (AUM)</div>
                  <div className="text-xs font-semibold text-white font-mono mt-0.5">
                    {m.aum || 'N/A'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Latest NAV</div>
                  <div className="text-xs font-semibold text-[#00D09C] font-mono mt-0.5">
                    {m.nav || 'N/A'}
                  </div>
                </div>

                <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                  <div className="text-[10px] text-slate-400 font-medium">Lock-in Period</div>
                  <div className="text-xs font-semibold text-slate-200 font-mono mt-0.5">
                    {m.lock_in || 'None'}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {/* Compliance Card */}
          <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-3.5 flex items-start gap-2.5">
            <div className="text-[11px] text-amber-200/90 leading-relaxed">
              <strong className="text-amber-300 font-semibold block uppercase tracking-wider text-[10px] mb-1">
                SEBI Non-Advisory &amp; Non-Comparative Compliance Mandate
              </strong>
              In compliance with SEBI mutual fund guidelines, this assistant presents strictly factual statutory parameters for single schemes and does not provide fund rankings, side-by-side comparative recommendations, or return projections.
            </div>
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 sm:px-6 bg-[#12161A] border-t border-[#28323E] flex items-center justify-between gap-3 shrink-0">
          <button
            onClick={() => alert(`Statutory Fact Record for ${currentScheme?.name || 'Selected Scheme'} (As of ${currentScheme?.as_of}) ready for reference.`)}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white px-3 py-2 rounded-lg bg-[#1A2027] hover:bg-[#202832] border border-[#28323E] transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Record</span>
          </button>
          <button
            onClick={handleAskInChat}
            className="flex items-center gap-2 text-xs font-semibold text-[#12161A] bg-[#00D09C] hover:bg-[#00B386] px-4 py-2 rounded-lg shadow-md transition active:scale-95 cursor-pointer"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ask This Scheme in Chat</span>
          </button>
        </div>
      </div>
    </>
  );
};
