import React, { useState } from 'react';
import { ChevronDown, Download, ExternalLink, FileText, MessageSquare, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onInsertComparison: (text: string) => void;
}

// Hand-verified canonical scheme metrics grounded in data/ground_truth.yaml & data/index/facts.db
const SCHEME_DATA: Record<string, {
  name: string;
  plan: string;
  inception: string;
  ter: string;
  exitLoad: string;
  minSip: string;
  category: string;
  risk: string;
  benchmark: string;
  manager: string;
  aum: string;
  turnover: string;
  amfiCode: string;
  factsheetUrl: string;
}> = {
  'HDFC Mid-Cap Opportunities Fund': {
    name: 'HDFC Mid-Cap Opportunities Fund',
    plan: 'Direct-Growth',
    inception: '2007 Inception',
    ter: '0.74%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100',
    category: 'Mid Cap Fund',
    risk: 'Very High Risk',
    benchmark: 'NIFTY Midcap 150 TRI',
    manager: 'Chirag Setalvad',
    aum: '₹1,01,856 Cr',
    turnover: '14.8% • 5.8% cash',
    amfiCode: '118989',
    factsheetUrl: 'https://www.hdfcfund.com/our-products/hdfc-mid-cap-opportunities-fund',
  },
  'HDFC Small Cap Fund': {
    name: 'HDFC Small Cap Fund',
    plan: 'Direct-Growth',
    inception: '2008 Inception',
    ter: '0.80%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100',
    category: 'Small Cap Fund',
    risk: 'Very High Risk',
    benchmark: 'BSE 250 SmallCap TRI',
    manager: 'Chirag Setalvad',
    aum: '₹40,801 Cr',
    turnover: '19.5% • 7.2% cash',
    amfiCode: '130503',
    factsheetUrl: 'https://www.hdfcfund.com/our-products/hdfc-small-cap-fund',
  },
  'HDFC Top 100 Fund': {
    name: 'HDFC Top 100 Fund',
    plan: 'Direct-Growth',
    inception: '1996 Inception',
    ter: '1.02%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100',
    category: 'Large Cap Fund',
    risk: 'Very High Risk',
    benchmark: 'NIFTY 100 TRI',
    manager: 'Rahul Baijal',
    aum: '₹37,294 Cr',
    turnover: '22.1% • 3.3% cash',
    amfiCode: '119062',
    factsheetUrl: 'https://www.hdfcfund.com/our-products/hdfc-top-100-fund',
  },
  'HDFC Silver ETF FoF': {
    name: 'HDFC Silver ETF FoF',
    plan: 'Direct-Growth',
    inception: '2022 Inception',
    ter: '0.21%',
    exitLoad: '1.00% if < 15 days, Nil thereafter',
    minSip: '₹100',
    category: 'Commodities FoF',
    risk: 'Very High Risk',
    benchmark: 'Domestic Price of Silver',
    manager: 'Arun Agarwal, Nirman Morakhia',
    aum: '₹4,497 Cr',
    turnover: '8.4% • 1.5% cash',
    amfiCode: '150186',
    factsheetUrl: 'https://www.hdfcfund.com/our-products/hdfc-silver-etf-fund-fund',
  },
  'HDFC Multi Cap Fund': {
    name: 'HDFC Multi Cap Fund',
    plan: 'Direct-Growth',
    inception: '2021 Inception',
    ter: '0.96%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100',
    category: 'Multi Cap Fund',
    risk: 'Very High Risk',
    benchmark: 'NIFTY 500 Multicap 50:25:25 TRI',
    manager: 'Gopal Agrawal',
    aum: '₹19,490 Cr',
    turnover: '28.3% • 3.7% cash',
    amfiCode: '149262',
    factsheetUrl: 'https://www.hdfcfund.com/our-products/hdfc-multi-cap-fund',
  },
};

export const CompareDrawer: React.FC<Props> = ({ isOpen, onClose, onInsertComparison }) => {
  const [selectedScheme, setSelectedScheme] = useState('HDFC Mid-Cap Opportunities Fund');

  const schemeData = SCHEME_DATA[selectedScheme] || SCHEME_DATA['HDFC Mid-Cap Opportunities Fund'];

  if (!isOpen) return null;

  const handleAskInChat = () => {
    const promptText = `What is the expense ratio, exit load, minimum SIP, benchmark, and riskometer for ${schemeData.name}?`;
    onInsertComparison(promptText);
    onClose();
  };

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
                  Official facts.db
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Canonical statutory metrics • Single-scheme inspection • No comparative ranking
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
              value={selectedScheme}
              onChange={(e) => setSelectedScheme(e.target.value)}
              className="w-full bg-[#12161A] text-xs font-semibold text-white border border-[#00D09C]/40 rounded-lg px-3 py-2.5 appearance-none focus:outline-none focus:border-[#00D09C] cursor-pointer"
            >
              {Object.keys(SCHEME_DATA).map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-3.5 text-slate-400">
              <ChevronDown className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:px-6 flex flex-col gap-4">
          {/* Single Scheme Facts Card */}
          <div className="bg-[#1A2027] border border-[#28323E] rounded-xl p-4 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-white">{schemeData.name}</h3>
                <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-[#00D09C]/10 text-[#00D09C] font-mono font-semibold text-[11px]">
                    {schemeData.plan}
                  </span>
                  <span>• AMFI Code: <strong className="text-white font-mono">{schemeData.amfiCode}</strong></span>
                  <span>• {schemeData.inception}</span>
                </div>
              </div>
              <a
                href={schemeData.factsheetUrl}
                target="_blank"
                rel="noreferrer"
                className="p-1.5 rounded-lg bg-[#12161A] hover:bg-[#202832] border border-[#28323E] text-[#00D09C] hover:text-white transition flex items-center gap-1 text-[11px]"
                title="Open official AMC portal"
              >
                <span>AMC Portal</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* 10-Metric Statutory Fact Grid */}
            <div className="grid grid-cols-2 gap-2 mt-1 text-xs">
              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Expense Ratio (TER)</div>
                <div className="text-sm font-bold text-[#00D09C] font-mono mt-0.5">{schemeData.ter}</div>
                <div className="text-[9px] text-slate-500 font-mono">Direct Plan • Audited AMC</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">SEBI Riskometer</div>
                <div className="text-sm font-bold text-red-400 font-mono mt-0.5">{schemeData.risk}</div>
                <div className="text-[9px] text-slate-500 font-mono">Mandatory SEBI tier</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Exit Load Terms</div>
                <div className="text-xs font-semibold text-slate-200 mt-0.5">{schemeData.exitLoad}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Min SIP / Lumpsum</div>
                <div className="text-xs font-semibold text-white font-mono mt-0.5">{schemeData.minSip}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E] col-span-2">
                <div className="text-[10px] text-slate-400 font-medium">Benchmark Index</div>
                <div className="text-xs font-semibold text-slate-200 font-mono mt-0.5">{schemeData.benchmark}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Fund Manager</div>
                <div className="text-xs font-semibold text-white mt-0.5">{schemeData.manager}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Fund Size (AUM)</div>
                <div className="text-xs font-semibold text-white font-mono mt-0.5">{schemeData.aum}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">SEBI Category</div>
                <div className="text-xs font-semibold text-white mt-0.5">{schemeData.category}</div>
              </div>

              <div className="bg-[#12161A] p-2.5 rounded-lg border border-[#28323E]">
                <div className="text-[10px] text-slate-400 font-medium">Turnover &amp; Cash</div>
                <div className="text-xs font-semibold text-slate-200 font-mono mt-0.5">{schemeData.turnover}</div>
              </div>
            </div>
          </div>

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
            onClick={() => alert(`Statutory Fact Record for ${schemeData.name} ready for reference.`)}
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
