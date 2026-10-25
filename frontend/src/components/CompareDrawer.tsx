import React, { useState } from 'react';
import { ArrowLeftRight, Check, ChevronDown, Download, MessageSquare, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onInsertComparison: (text: string) => void;
}

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
}> = {
  'HDFC Mid-Cap Opportunities Fund': {
    name: 'HDFC Mid-Cap Opportunities Fund',
    plan: 'Direct-Growth',
    inception: '2007 Inception',
    ter: '0.74%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100 / ₹100',
    category: 'Mid Cap',
    risk: 'Very High Risk',
    benchmark: 'NIFTY Midcap 150 TRI',
    manager: 'Chirag Setalvad',
    aum: '₹72,400 Cr',
    turnover: '14.2% • 7.8% cash',
  },
  'HDFC Small Cap Fund': {
    name: 'HDFC Small Cap Fund',
    plan: 'Direct-Growth',
    inception: '2008 Inception',
    ter: '0.68%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100 / ₹100',
    category: 'Small Cap',
    risk: 'Very High Risk',
    benchmark: 'NIFTY Smallcap 250 TRI',
    manager: 'Chirag Setalvad',
    aum: '₹34,250 Cr',
    turnover: '19.5% • 5.1% cash',
  },
  'HDFC Top 100 Fund': {
    name: 'HDFC Top 100 Fund',
    plan: 'Direct-Growth',
    inception: '1996 Inception',
    ter: '1.02%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100 / ₹100',
    category: 'Large Cap',
    risk: 'Very High Risk',
    benchmark: 'NIFTY 100 TRI',
    manager: 'Rahul Baijal',
    aum: '₹38,100 Cr',
    turnover: '22.1% • 4.5% cash',
  },
  'HDFC Silver ETF FoF': {
    name: 'HDFC Silver ETF FoF',
    plan: 'Direct-Growth',
    inception: '2022 Inception',
    ter: '0.22%',
    exitLoad: '1.00% if < 15 days, Nil thereafter',
    minSip: '₹100 / ₹100',
    category: 'Commodities FoF',
    risk: 'Very High Risk',
    benchmark: 'Domestic Price of Silver',
    manager: 'Nirman Morakhia',
    aum: '₹2,100 Cr',
    turnover: '8.4% • 2.1% cash',
  },
  'HDFC Multi Cap Fund': {
    name: 'HDFC Multi Cap Fund',
    plan: 'Direct-Growth',
    inception: '2021 Inception',
    ter: '0.79%',
    exitLoad: '1.00% if < 1 yr, Nil thereafter',
    minSip: '₹100 / ₹100',
    category: 'Multi Cap',
    risk: 'Very High Risk',
    benchmark: 'NIFTY 500 Multicap 50:25:25 TRI',
    manager: 'Gopal Agrawal',
    aum: '₹16,800 Cr',
    turnover: '28.3% • 6.2% cash',
  },
};

export const CompareDrawer: React.FC<Props> = ({ isOpen, onClose, onInsertComparison }) => {
  const [schemeA, setSchemeA] = useState('HDFC Mid-Cap Opportunities Fund');
  const [schemeB, setSchemeB] = useState('HDFC Small Cap Fund');

  const dataA = SCHEME_DATA[schemeA] || SCHEME_DATA['HDFC Mid-Cap Opportunities Fund'];
  const dataB = SCHEME_DATA[schemeB] || SCHEME_DATA['HDFC Small Cap Fund'];

  if (!isOpen) return null;

  const handleInsert = () => {
    const promptText = `Compare the expense ratio, exit load, minimum SIP, and benchmark between ${dataA.name} and ${dataB.name}.`;
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
      <div className="fixed top-0 right-0 bottom-0 w-full sm:w-[590px] bg-[#151A20] border-l border-[#28323E] z-50 flex flex-col shadow-2xl transition-transform animate-slideIn">
        {/* Header */}
        <div className="p-4 sm:px-6 border-b border-[#28323E] flex items-center justify-between bg-[#12161A]/90 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#00D09C]/10 border border-[#00D09C]/35 flex items-center justify-center text-[#00D09C]">
              <ArrowLeftRight className="w-4 h-4 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-tight">HDFC Scheme Comparison</h2>
                <span className="px-2 py-0.2 rounded-full bg-[#00D09C]/10 border border-[#00D09C]/30 text-[#00D09C] text-[10px] font-mono font-medium">
                  Factual Matrix Only
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Side-by-side statutory metrics • Non-advisory comparison
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#1A2027] hover:bg-[#202832] border border-[#28323E] flex items-center justify-center text-slate-400 hover:text-white transition cursor-pointer"
            title="Close comparison"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scheme Selector Bar (Dual Header) */}
        <div className="p-4 sm:px-6 bg-[#1A2027]/70 border-b border-[#28323E] shrink-0 grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D09C]"></span> Scheme A (Baseline)
            </span>
            <div className="relative">
              <select
                value={schemeA}
                onChange={(e) => setSchemeA(e.target.value)}
                className="w-full bg-[#12161A] text-xs font-semibold text-white border border-[#00D09C]/40 rounded-lg px-2.5 py-2 appearance-none focus:outline-none focus:border-[#00D09C] cursor-pointer"
              >
                {Object.keys(SCHEME_DATA).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <div className="pointer-events-none absolute right-2.5 top-3 text-slate-400">
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
              <span className="px-1.5 py-0.2 bg-[#202832] rounded text-slate-300">{dataA.plan}</span>
              <span>• {dataA.inception}</span>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Scheme B (Benchmark)
            </span>
            <div className="relative">
              <select
                value={schemeB}
                onChange={(e) => setSchemeB(e.target.value)}
                className="w-full bg-[#12161A] text-xs font-semibold text-white border border-amber-500/40 rounded-lg px-2.5 py-2 appearance-none focus:outline-none focus:border-amber-400 cursor-pointer"
              >
                {Object.keys(SCHEME_DATA).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <div className="pointer-events-none absolute right-2.5 top-3 text-slate-400">
                <ChevronDown className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
              <span className="px-1.5 py-0.2 bg-[#202832] rounded text-slate-300">{dataB.plan}</span>
              <span>• {dataB.inception}</span>
            </div>
          </div>
        </div>

        {/* Scrollable Comparison Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:px-6 flex flex-col gap-4">
          {/* Statutory Matrix Table */}
          <div className="border border-[#28323E] rounded-xl overflow-hidden bg-[#12161A]">
            <div className="bg-[#1A2027] px-3.5 py-2 border-b border-[#28323E] flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider font-mono">
                Statutory Fact Matrix
              </span>
              <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                <Check className="w-3 h-3" /> Audited AMC Record
              </span>
            </div>

            <div className="divide-y divide-[#28323E]/70 text-xs">
              {/* Row 1: Direct TER */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Direct TER (Expense Ratio)</div>
                <div className="col-span-1.5 font-mono font-bold text-[#00D09C] bg-[#00D09C]/10 px-2 py-1 rounded text-center">
                  {dataA.ter}
                </div>
                <div className="col-span-1.5 font-mono font-bold text-amber-300 bg-amber-500/10 px-2 py-1 rounded text-center">
                  {dataB.ter}
                </div>
              </div>

              {/* Row 2: Exit Load */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Exit Load Terms</div>
                <div className="col-span-1.5 text-slate-200 text-[11px] leading-snug px-1">{dataA.exitLoad}</div>
                <div className="col-span-1.5 text-slate-200 text-[11px] leading-snug px-1">{dataB.exitLoad}</div>
              </div>

              {/* Row 3: Min SIP / Lumpsum */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Min SIP / Lumpsum</div>
                <div className="col-span-1.5 font-mono font-semibold text-white px-1">{dataA.minSip}</div>
                <div className="col-span-1.5 font-mono font-semibold text-white px-1">{dataB.minSip}</div>
              </div>

              {/* Row 4: Category & Risk */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Category & Risk</div>
                <div className="col-span-1.5 text-[11px] px-1">
                  <span className="text-white font-medium">{dataA.category}</span>
                  <span className="block text-[10px] text-red-400 font-mono">{dataA.risk}</span>
                </div>
                <div className="col-span-1.5 text-[11px] px-1">
                  <span className="text-white font-medium">{dataB.category}</span>
                  <span className="block text-[10px] text-red-400 font-mono">{dataB.risk}</span>
                </div>
              </div>

              {/* Row 5: Benchmark Index */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Benchmark Index</div>
                <div className="col-span-1.5 text-[11px] text-slate-300 font-mono px-1 leading-tight">{dataA.benchmark}</div>
                <div className="col-span-1.5 text-[11px] text-slate-300 font-mono px-1 leading-tight">{dataB.benchmark}</div>
              </div>

              {/* Row 6: Fund Manager */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Fund Manager</div>
                <div className="col-span-1.5 text-[11px] text-slate-200 px-1">{dataA.manager}</div>
                <div className="col-span-1.5 text-[11px] text-slate-200 px-1">{dataB.manager}</div>
              </div>

              {/* Row 7: AUM */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Asset Base (AUM)</div>
                <div className="col-span-1.5 font-mono font-semibold text-white px-1">{dataA.aum}</div>
                <div className="col-span-1.5 font-mono font-semibold text-white px-1">{dataB.aum}</div>
              </div>

              {/* Row 8: Portfolio Turnover & Cash */}
              <div className="grid grid-cols-5 p-3 items-center hover:bg-[#1A2027]/40 transition">
                <div className="col-span-2 text-slate-400 text-[11px] font-medium">Turnover & Cash</div>
                <div className="col-span-1.5 text-[11px] font-mono text-slate-300 px-1">{dataA.turnover}</div>
                <div className="col-span-1.5 text-[11px] font-mono text-slate-300 px-1">{dataB.turnover}</div>
              </div>
            </div>
          </div>

          {/* Compliance Card */}
          <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-3.5 flex items-start gap-2.5">
            <div className="text-[11px] text-amber-200/90 leading-relaxed">
              <strong className="text-amber-300 font-semibold block uppercase tracking-wider text-[10px] mb-1">
                SEBI Compliance Mandate
              </strong>
              Forward-looking projections, returns rankings, and advisory recommendations are strictly omitted. Consult a SEBI-registered financial advisor for personal suitability.
            </div>
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 sm:px-6 bg-[#12161A] border-t border-[#28323E] flex items-center justify-between gap-3 shrink-0">
          <button
            onClick={() => alert(`Statutory Fact Matrix (${dataA.name} vs ${dataB.name}) ready.`)}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white px-3 py-2 rounded-lg bg-[#1A2027] hover:bg-[#202832] border border-[#28323E] transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Diff</span>
          </button>
          <button
            onClick={handleInsert}
            className="flex items-center gap-2 text-xs font-semibold text-[#12161A] bg-[#00D09C] hover:bg-[#00B386] px-4 py-2 rounded-lg shadow-md transition active:scale-95 cursor-pointer"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Insert Matrix into Chat</span>
          </button>
        </div>
      </div>
    </>
  );
};
