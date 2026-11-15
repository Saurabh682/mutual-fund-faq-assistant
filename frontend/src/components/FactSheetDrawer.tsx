import React from 'react';
import { ChevronDown, ChevronRight, X } from 'lucide-react';
import { formatDate, groupIndian, plainExitLoad } from '../lib/format';
import { useDialogA11y } from '../lib/useDialogA11y';
import { useChatStore } from '../store/useChatStore';
import { groupByFundHouse } from '../lib/schemes';

function parseRiskLevel(riskStr?: string): { level: number; label: string } {
  if (!riskStr) return { level: 6, label: 'Very High' };
  const lower = riskStr.toLowerCase();
  if (lower.includes('very high')) return { level: 6, label: 'Very High' };
  if (lower.includes('moderately high')) return { level: 4, label: 'Moderately High' };
  if (lower.includes('low to moderate') || lower.includes('low-moderate'))
    return { level: 2, label: 'Low to Moderate' };
  if (lower.includes('high')) return { level: 5, label: 'High' };
  if (lower.includes('moderate')) return { level: 3, label: 'Moderate' };
  if (lower.includes('low')) return { level: 1, label: 'Low' };
  return { level: 6, label: riskStr };
}

interface FactSheetContentProps {
  onClose?: () => void;
  isModalOrDrawer?: boolean;
  /** id of the heading, so a dialog around this content can name itself with aria-labelledby */
  titleId?: string;
}

/** Riskometer pill colour: green for low, through amber, to red for very high. */
function riskTone(label: string): string {
  const l = label.toLowerCase();
  if (l.includes('very high')) return 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300';
  if (l.includes('high')) return 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300';
  if (l.includes('moderate')) return 'bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
  return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300';
}

export const FactSheetContent: React.FC<FactSheetContentProps> = ({
  onClose,
  isModalOrDrawer = false,
  titleId,
}) => {
  const { meta, schemeFacts, factsState, reloadSchemeFacts, selectedSchemeId, setSelectedSchemeId } = useChatStore();

  const schemes = meta?.schemes || [];
  const activeFacts = schemeFacts.find((s) => s.scheme_id === selectedSchemeId);
  const activeScheme = schemes.find((s) => s.id === selectedSchemeId);

  const fallbackIso = activeFacts && typeof activeFacts.as_of === 'string' ? activeFacts.as_of : '';
  const getMetric = (key: string): { val: string; iso: string; date: string } => {
    const raw = activeFacts?.[key];
    if (typeof raw === 'object' && raw !== null && 'value' in raw) {
      const iso = raw.as_of || fallbackIso;
      return { val: raw.value || '—', iso, date: formatDate(iso) };
    }
    return { val: '—', iso: fallbackIso, date: formatDate(fallbackIso) };
  };

  const ter = getMetric('ter_direct');
  const exitLoad = getMetric('exit_load');
  const minSip = getMetric('min_sip');
  const minLumpsum = getMetric('min_lumpsum');
  const lockIn = getMetric('lock_in');
  const riskometer = getMetric('riskometer');
  const benchmark = getMetric('benchmark');
  const fundManager = getMetric('fund_manager');
  const nav = getMetric('nav');
  const aum = getMetric('aum');

  // One date for the whole sheet (the footer). A row only says "as of" when it differs, so a stale row stands out.
  const sheetIso =
    [ter, exitLoad, minSip, minLumpsum, lockIn, riskometer, benchmark, fundManager, nav, aum]
      .map((m) => m.iso)
      .filter(Boolean)
      .sort()
      .pop() ?? '';
  const sheetDate = formatDate(sheetIso);
  const rowDate = (m: { iso: string; date: string }) =>
    m.iso && m.iso !== sheetIso ? (
      <span className="text-[13px] text-[#64748B] dark:text-[#94a3b8]">as of {m.date}</span>
    ) : null;

  const riskInfo = parseRiskLevel(riskometer.val);

  return (
    <div className="flex flex-col h-full">
      {/* Header with Scheme Switcher */}
      <div className="flex flex-col gap-2.5 pb-3 border-b border-[#E2E8F0] dark:border-[#2f3633] shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#047857] dark:bg-[#10b981]" />
            <h2 id={titleId} className="text-[17px] font-bold text-[#0F172A] dark:text-[#dde4df]">
              Scheme Fact Sheet
            </h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              aria-label="Close fact sheet"
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#0F172A] dark:text-[#94a3b8] dark:hover:text-[#dde4df] hover:bg-[#F1F5F9] dark:hover:bg-[#242c28] transition-colors cursor-pointer"
              type="button"
            >
              {isModalOrDrawer ? <X className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            </button>
          )}
        </div>

        {/* Scheme Selector Dropdown */}
        <div className="relative">
          <label htmlFor="drawer-scheme-select" className="sr-only">
            Select Scheme in Fact Sheet
          </label>
          <div className="relative">
            <select
              id="drawer-scheme-select"
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              className="w-full bg-[#F8FAFC] dark:bg-[#16201b] border border-[#E2E8F0] dark:border-[#1f2824] hover:bg-[#F1F5F9] dark:hover:bg-[#242c28] text-[#0F172A] dark:text-[#dde4df] text-[13px] sm:text-[14px] font-medium px-3.5 py-2.5 rounded-xl appearance-none cursor-pointer focus:outline-none transition-colors truncate pr-8"
            >
              {groupByFundHouse(schemes).map((g) => (
                <optgroup key={g.house} label={g.house || 'Schemes'}>
                  {g.schemes.map((s) => (
                <option
                  key={s.id}
                  value={s.id}
                  className="bg-white text-[#0F172A] dark:bg-[#16201b] dark:text-[#dde4df]"
                >
                  {s.name}
                </option>
              ))}
                </optgroup>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-[#64748B] dark:text-[#94a3b8] pointer-events-none absolute right-3 top-3.5" />
          </div>
        </div>
      </div>

      {activeFacts && (
        <div className="flex flex-wrap gap-2 pt-1 pb-2" aria-label="Scheme classification">
          {activeScheme?.category && (
            <span className="px-2.5 py-1 rounded-full text-[12px] font-semibold border bg-[#F8FAFC] border-[#E2E8F0] text-[#475569] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#94a3b8]">
              {activeScheme.category}
            </span>
          )}
          {riskometer.val !== '—' && (
            <span className={`px-2.5 py-1 rounded-full text-[12px] font-semibold ${riskTone(riskometer.val)}`}>
              {riskometer.val}
            </span>
          )}
        </div>
      )}

      {!activeFacts ? (
        factsState === 'loading' ? (
          <div role="status" aria-label="Loading fact sheet" className="flex-1 py-3 space-y-2 animate-pulse">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-[52px] rounded-xl bg-[#E2E8F0] dark:bg-[#242c28]" />
            ))}
          </div>
        ) : (
          <div role="alert" className="flex-1 py-8 flex flex-col items-center gap-3 text-center">
            <p className="text-[14px] leading-relaxed text-[#475569] dark:text-[#94a3b8]">
              Couldn&apos;t load this fact sheet. The data service may be starting up.
            </p>
            <button
              type="button"
              onClick={() => reloadSchemeFacts()}
              className="min-h-[44px] px-4 rounded-xl text-[13px] font-semibold border cursor-pointer bg-white border-[#E2E8F0] text-[#0F172A] hover:bg-[#F8FAFC] dark:bg-[#16201b] dark:border-[#2f3633] dark:text-[#dde4df] dark:hover:bg-[#242c28]"
            >
              Try again
            </button>
          </div>
        )
      ) : (
      <div className="overflow-y-auto flex-1 py-3 space-y-2 text-[13px]">
        {/* Row 1: TER (Direct) */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">TER (Direct)</span>
            {rowDate(ter)}
          </div>
          <span className="text-[15px] font-bold text-[#047857] dark:text-[#10b981] num-tabular">
            {ter.val}
          </span>
        </div>

        {/* Row 2: Exit load */}
        <div className="flex items-start justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824] gap-2">
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Exit load</span>
            {rowDate(exitLoad)}
          </div>
          <span className="text-[13px] text-right text-[#0F172A] dark:text-[#dde4df] font-medium max-w-[200px]">
            {plainExitLoad(exitLoad.val)}
          </span>
        </div>

        {/* Row 3: Minimum SIP */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Minimum SIP</span>
            {rowDate(minSip)}
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df] num-tabular">
            {minSip.val}
          </span>
        </div>

        {/* Row 4: Minimum lumpsum */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Minimum lumpsum</span>
            {rowDate(minLumpsum)}
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df] num-tabular">
            {minLumpsum.val}
          </span>
        </div>

        {/* Row 5: Lock-in */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Lock-in</span>
            {rowDate(lockIn)}
          </div>
          <span className="text-[13px] font-medium text-[#0F172A] dark:text-[#dde4df]">
            {lockIn.val}
          </span>
        </div>

        {/* Row 6: Riskometer (6-segment visual bar) */}
        <div className="p-3 rounded-xl border flex flex-col gap-2 bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Riskometer</span>
              {rowDate(riskometer)}
            </div>
            <span
              className={`text-[13px] font-bold px-2 py-0.5 rounded-md ${
                riskInfo.level >= 5
                  ? 'bg-red-100 text-red-700 dark:bg-[#3d1a1d] dark:text-[#ffb4ab] border border-red-300 dark:border-[#690005]'
                  : riskInfo.level >= 3
                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-[#ffb95f]'
                  : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-[#4edea3]'
              }`}
            >
              {riskInfo.label}
            </span>
          </div>

          {/* 6-level segmented visual bar */}
          <div
            className="grid grid-cols-6 gap-1 h-2 rounded-full overflow-hidden"
            aria-label={`Riskometer scale level ${riskInfo.level} of 6: ${riskInfo.label}`}
          >
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 1 ? 'bg-[#10b981]' : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="Low"
            />
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 2 ? 'bg-[#34d399]' : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="Low to Moderate"
            />
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 3 ? 'bg-[#facc15]' : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="Moderate"
            />
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 4 ? 'bg-[#fb923c]' : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="Moderately High"
            />
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 5 ? 'bg-[#f87171]' : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="High"
            />
            <div
              className={`h-full rounded-sm ${
                riskInfo.level >= 6
                  ? 'bg-[#ef4444] shadow-[0_0_6px_rgba(239,68,68,0.8)] ring-1 ring-red-400'
                  : 'bg-[#E2E8F0] dark:bg-[#2f3633]'
              }`}
              title="Very High"
            />
          </div>
          <div className="flex justify-between text-[13px] text-[#64748B] dark:text-[#94a3b8] px-0.5">
            <span>Low</span>
            <span className="font-medium text-[#0F172A] dark:text-[#dde4df]">
              Level {riskInfo.level} / 6
            </span>
            <span>Very High</span>
          </div>
        </div>

        {/* Row 7: Benchmark */}
        <div className="flex items-start justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824] gap-2">
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">Benchmark</span>
            {rowDate(benchmark)}
          </div>
          <span className="text-[13px] text-right font-medium text-[#0F172A] dark:text-[#dde4df] max-w-[200px]">
            {benchmark.val}
          </span>
        </div>

        {/* Row 8: Fund manager (labeled: "Fund manager (as listed on source page)") */}
        <div className="flex items-start justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824] gap-2">
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">
              Fund manager (as listed on source page)
            </span>
            {rowDate(fundManager)}
          </div>
          <span className="text-[13px] text-right font-medium text-[#0F172A] dark:text-[#dde4df] max-w-[190px]">
            {fundManager.val}
          </span>
        </div>

        {/* Row 9: NAV */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">NAV</span>
            {rowDate(nav)}
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df] num-tabular">
            {nav.val}
          </span>
        </div>

        {/* Row 10: AUM */}
        <div className="flex items-center justify-between p-2.5 rounded-xl border bg-[#F8FAFC] border-[#E2E8F0] dark:bg-[#16201b] dark:border-[#1f2824]">
          <div className="flex flex-col">
            <span className="font-semibold text-[#0F172A] dark:text-[#dde4df]">AUM</span>
            {rowDate(aum)}
          </div>
          <span className="text-[14px] font-bold text-[#0F172A] dark:text-[#dde4df] num-tabular">
            {groupIndian(aum.val)}
          </span>
        </div>
      </div>

      )}

      {/* Footer */}
      {activeFacts && (
        <div className="pt-3 border-t border-[#E2E8F0] dark:border-[#2f3633] shrink-0 text-center">
          <p className="text-[13px] text-[#64748B] dark:text-[#94a3b8] leading-relaxed">
            Source: Groww scheme page{sheetDate ? ` · Data as of ${sheetDate}` : ''}
          </p>
        </div>
      )}
    </div>
  );
};

export const FactSheetDrawer: React.FC = () => {
  const { isFactSheetOpen, toggleFactSheet } = useChatStore();
  const dialogsRef = useDialogA11y(isFactSheetOpen, () => toggleFactSheet(false));

  if (!isFactSheetOpen) return null;

  return (
    <div ref={dialogsRef} className="contents">
      {/* Backdrop for Overlay Drawer (Tablet < 1100px & Mobile < 768px) */}
      <div
        onClick={() => toggleFactSheet(false)}
        className="fixed inset-0 bg-black/60 z-40 xl:hidden backdrop-blur-xs transition-opacity"
        aria-hidden="true"
      />

      {/* Mobile Bottom Sheet (< 768px) */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-factsheet-title"
        className="fixed inset-x-0 bottom-0 z-50 max-h-[88vh] md:hidden rounded-t-2xl shadow-2xl flex flex-col overflow-hidden animate-slide-up bg-white border-t border-[#E2E8F0] dark:bg-[#161d1a] dark:border-[#29352e]"
      >
        {/* Drag Bar Handle */}
        <div className="w-full pt-3 pb-1 flex justify-center items-center shrink-0">
          <div className="w-10 h-1.5 rounded-full bg-[#CBD5E1] dark:bg-[#3c4a42]" />
        </div>
        <div className="p-4 flex-1 overflow-hidden flex flex-col">
          <FactSheetContent titleId="mobile-factsheet-title" onClose={() => toggleFactSheet(false)} isModalOrDrawer={true} />
        </div>
      </div>

      {/* Tablet Slide-in Right Drawer (768px - 1099px) */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="tablet-factsheet-title"
        className="fixed top-0 right-0 bottom-0 w-[420px] max-w-[90vw] z-50 hidden md:flex xl:hidden flex-col shadow-2xl p-5 animate-slide-in-right bg-white border-l border-[#E2E8F0] dark:bg-[#131a17] dark:border-[#1f2824]"
      >
        <FactSheetContent titleId="tablet-factsheet-title" onClose={() => toggleFactSheet(false)} isModalOrDrawer={true} />
      </div>
    </div>
  );
};
